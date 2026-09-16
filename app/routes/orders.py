from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session

from app.template_config import Jinja2Templates
from app.content.store import load_content
from app.config.database import get_db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.payment import PaymentSetting
from app.models.user import User
from app.routes.customer_auth import (
    apply_profile,
    get_current_user,
    profile_validation_issues,
    user_profile_dict,
)
from app.schemas.account import CheckoutRequest, ProfileUpdate
from app.services.razorpay import (
    RazorpayError,
    create_order as razorpay_create_order,
)
from app.services.order_stock import release_order_stock

router = APIRouter(prefix="/account", tags=["Customer Orders"])

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["site"] = load_content


def _payment_settings(db: Session) -> PaymentSetting | None:
    return (
        db.query(PaymentSetting)
        .filter(PaymentSetting.id == 1)
        .first()
    )


def _payment_payload(
    payment: PaymentSetting,
    order: Order,
):
    return {
        "key_id": payment.key_id,
        "mode": payment.mode,
        "razorpay_order_id": order.razorpay_order_id,
        "amount": int(
            (Decimal(str(order.total_amount)) * 100)
            .quantize(Decimal("1"))
        ),
        "currency": "INR",
        "local_order_id": order.id,
        "name": order.shipping_name,
        "email": order.shipping_email,
        "contact": order.shipping_phone,
        "description": f"{load_content().get('site', {}).get('name', 'Intra Aura')} Order #{order.id}",
        "brand_name": str(load_content().get("site", {}).get("name", "Intra Aura")),
    }


def _shipping_from_user(user):
    return {
        "shipping_name": user.name,
        "shipping_email": user.email,
        "shipping_phone": user.phone,
        "shipping_address": user.address,
        "shipping_area_street": user.area_street,
        "shipping_landmark": user.landmark,
        "shipping_city": user.city,
        "shipping_state": user.state,
        "shipping_pincode": user.pincode,
    }


@router.get("/orders")
def orders_page(
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)

    if not user:
        return RedirectResponse(
            url="/account/login?next=/account/orders",
            status_code=303
        )

    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={
            "user": user,
            "orders": orders,
        },
    )


@router.get("/orders/{order_id}")
def order_detail_page(
    order_id: int,
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        return RedirectResponse(
            url=f"/account/login?next=/account/orders/{order_id}",
            status_code=303
        )

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return templates.TemplateResponse(
        request=request,
        name="order_detail.html",
        context={
            "user": user,
            "order": order,
        },
    )


@router.post("/checkout")
async def checkout(
    payload: CheckoutRequest,
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Please log in to place an order"
        )

    payment = _payment_settings(db)

    if not payment or not payment.enabled or not payment.key_id or not payment.key_secret:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "payment_not_configured",
                "message": "Online payment is not configured yet. Please contact the administrator.",
            },
        )

    # Existing saved profile must be complete.
    missing, existing_errors = profile_validation_issues(user)

    if (missing or existing_errors) and payload.profile is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "profile_incomplete",
                "message": "Complete your delivery details before placing the order.",
                "missing_fields": missing,
                "field_errors": existing_errors,
                "profile": user_profile_dict(user),
            },
        )

    profile = payload.profile

    if profile is not None:
        duplicate = (
            db.query(User)
            .filter(
                User.email == profile.email,
                User.id != user.id,
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "validation_error",
                    "field_errors": {
                        "email": "This email is already registered."
                    },
                },
            )

        apply_profile(user, profile)

    # Use the authenticated user's profile after any update.
    try:
        saved_profile = ProfileUpdate.model_validate(
            user_profile_dict(user)
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail={
                "code": "validation_error",
                "message": "Please correct your delivery details.",
            },
        )

    quantities: dict[int, int] = {}

    for item in payload.items:
        quantities[item.id] = quantities.get(item.id, 0) + item.quantity

    order = None

    try:
        # Lock product rows during the inventory reservation.
        products = (
            db.query(Product)
            .filter(Product.id.in_(quantities.keys()))
            .with_for_update()
            .all()
        )

        by_id = {product.id: product for product in products}

        if len(by_id) != len(quantities):
            missing_ids = [
                pid for pid in quantities
                if pid not in by_id
            ]
            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {missing_ids[0]}"
            )

        total = Decimal("0.00")
        validated_items = []

        for product_id, quantity in quantities.items():
            product = by_id[product_id]

            if not product.is_active:
                raise HTTPException(
                    status_code=409,
                    detail=f"{product.name} is no longer available"
                )

            if product.stock < quantity:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Only {product.stock} unit(s) of "
                        f"{product.name} are available"
                    )
                )

            unit_price = (
                product.discount_price
                if product.discount_price is not None
                else product.price
            )

            unit_price = Decimal(str(unit_price))
            total += unit_price * quantity

            validated_items.append(
                (product, unit_price, quantity)
            )

        shipping = {
            **_shipping_from_user(user),
            "shipping_name": saved_profile.name,
            "shipping_email": saved_profile.email,
            "shipping_phone": saved_profile.phone,
            "shipping_address": saved_profile.address,
            "shipping_area_street": saved_profile.area_street,
            "shipping_landmark": saved_profile.landmark,
            "shipping_city": saved_profile.city,
            "shipping_state": saved_profile.state,
            "shipping_pincode": saved_profile.pincode,
        }

        order = Order(
            user_id=user.id,
            total_amount=total,
            status="Pending",
            payment_status="Pending",
            **shipping,
        )

        db.add(order)
        db.flush()

        for product, unit_price, quantity in validated_items:
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_name=product.name,
                    price=unit_price,
                    quantity=quantity,
                )
            )

            # Reserve inventory until payment succeeds or the order is
            # cancelled/failed.
            product.stock -= quantity

        db.commit()
        db.refresh(order)

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="We could not prepare your order. Please try again.",
        )

    # Create the Razorpay order only after the local order/inventory
    # transaction has succeeded.
    try:
        razorpay_order = razorpay_create_order(
            payment.key_id,
            payment.key_secret,
            amount=Decimal(str(order.total_amount)),
            receipt=f"IA-{order.id}",
            notes={
                "local_order_id": str(order.id),
                "customer_id": str(user.id),
            },
        )

        razorpay_order_id = razorpay_order.get("id")

        if not razorpay_order_id:
            raise RazorpayError(
                "Razorpay did not return an order ID."
            )

        order.razorpay_order_id = razorpay_order_id
        db.commit()
        db.refresh(order)

    except Exception as exc:
        # Razorpay order creation failed, so release our inventory
        # reservation and keep a failed audit record.
        try:
            locked_order = (
                db.query(Order)
                .filter(Order.id == order.id)
                .with_for_update()
                .first()
            )

            if locked_order:
                release_order_stock(db, locked_order)
                locked_order.payment_status = "Failed"
                locked_order.status = "Cancelled"
                db.commit()
        except Exception:
            db.rollback()

        message = (
            str(exc)
            if isinstance(exc, RazorpayError)
            else "Unable to start the payment."
        )

        raise HTTPException(
            status_code=502,
            detail={
                "code": "payment_creation_failed",
                "message": message,
            },
        )

    return {
        "success": True,
        "order_id": order.id,
        "payment": _payment_payload(payment, order),
    }


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Please log in")

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == user.id,
        )
        .with_for_update()
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.payment_status == "Paid":
        raise HTTPException(
            status_code=409,
            detail="Paid orders cannot be cancelled online. Please contact us for a refund request."
        )

    if order.status in {"Shipped", "Delivered", "Cancelled"}:
        raise HTTPException(
            status_code=409,
            detail="This order can no longer be cancelled."
        )

    release_order_stock(db, order)
    order.status = "Cancelled"

    if order.payment_status == "Pending":
        order.payment_status = "Cancelled"

    db.commit()

    return {
        "success": True,
        "message": "Order cancelled successfully.",
        "redirect_url": f"/account/orders/{order.id}?cancelled=1",
    }


@router.post("/orders/{order_id}/pay")
def resume_payment(
    order_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Please log in")

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.payment_status != "Pending" or order.stock_released:
        raise HTTPException(
            status_code=409,
            detail="This order is no longer awaiting payment."
        )

    payment = _payment_settings(db)

    if not payment or not payment.enabled or not payment.key_id or not payment.key_secret:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "payment_not_configured",
                "message": "Online payment is not configured yet.",
            },
        )

    if not order.razorpay_order_id:
        raise HTTPException(
            status_code=409,
            detail="This payment session has expired. Please contact us."
        )

    return {
        "success": True,
        "payment": _payment_payload(payment, order),
    }
