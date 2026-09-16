from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.order import Order
from app.models.payment import PaymentSetting
from app.routes.customer_auth import get_current_user
from app.services.order_stock import release_order_stock
from app.services.razorpay import (
    RazorpayError,
    capture_payment,
    fetch_payment,
    verify_checkout_signature,
    verify_webhook_signature,
)

router = APIRouter(tags=["Payments"])


def _payment_settings(db: Session):
    return (
        db.query(PaymentSetting)
        .filter(PaymentSetting.id == 1)
        .first()
    )


def _mark_paid(
    db: Session,
    order: Order,
    payment_id: str | None = None,
):
    if order.payment_status == "Paid":
        return

    order.payment_status = "Paid"
    order.status = (
        "Confirmed"
        if order.status in {"Pending", "Cancelled"}
        else order.status
    )

    if payment_id:
        order.razorpay_payment_id = payment_id

    order.payment_verified_at = datetime.utcnow()


def _mark_failed(
    db: Session,
    order: Order,
):
    if order.payment_status == "Paid":
        return

    release_order_stock(db, order)

    order.payment_status = "Failed"
    order.status = "Cancelled"


@router.post("/account/payments/verify")
async def verify_payment(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Please log in")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment data")

    try:
        local_order_id = int(data.get("local_order_id"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Invalid order")

    payment_id = str(
        data.get("razorpay_payment_id", "")
    ).strip()

    signature = str(
        data.get("razorpay_signature", "")
    ).strip()

    returned_razorpay_order_id = str(
        data.get("razorpay_order_id", "")
    ).strip()

    if not payment_id or not signature or not returned_razorpay_order_id:
        raise HTTPException(
            status_code=422,
            detail="Incomplete payment response."
        )

    order = (
        db.query(Order)
        .filter(
            Order.id == local_order_id,
            Order.user_id == user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.payment_status == "Paid":
        return {
            "success": True,
            "message": "Payment already verified.",
            "order_id": order.id,
            "redirect_url": f"/account/orders/{order.id}?payment=success",
        }

    if order.status == "Cancelled" or order.stock_released:
        raise HTTPException(
            status_code=409,
            detail="This order is no longer payable."
        )

    # IMPORTANT: use the Razorpay order ID stored by our server,
    # not the browser-supplied order ID, when calculating the signature.
    if returned_razorpay_order_id != order.razorpay_order_id:
        raise HTTPException(
            status_code=400,
            detail="Payment order mismatch."
        )

    payment = _payment_settings(db)

    if not payment or not payment.key_id or not payment.key_secret:
        raise HTTPException(
            status_code=503,
            detail="Payment configuration is unavailable."
        )

    if not verify_checkout_signature(
        order.razorpay_order_id,
        payment_id,
        signature,
        payment.key_secret,
    ):
        raise HTTPException(
            status_code=400,
            detail="Payment verification failed."
        )

    try:
        payment_data = fetch_payment(
            payment.key_id,
            payment.key_secret,
            payment_id,
        )

        if payment_data.get("order_id") != order.razorpay_order_id:
            raise HTTPException(
                status_code=400,
                detail="Payment does not belong to this order."
            )

        expected_amount = int(
            (Decimal(str(order.total_amount)) * 100)
            .quantize(Decimal("1"))
        )

        if int(payment_data.get("amount", 0)) != expected_amount:
            raise HTTPException(
                status_code=400,
                detail="Payment amount does not match the order."
            )

        status = str(
            payment_data.get("status", "")
        ).lower()

        if status == "authorized":
            # Auto-capture is recommended by Razorpay, but if this account
            # uses manual capture, capture it server-side before fulfilment.
            try:
                payment_data = capture_payment(
                    payment.key_id,
                    payment.key_secret,
                    payment_id,
                    amount=Decimal(str(order.total_amount)),
                )
                status = str(
                    payment_data.get("status", "")
                ).lower()
            except RazorpayError as exc:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Payment was authorized but could not be captured "
                        f"yet: {exc}"
                    ),
                )

        if status != "captured":
            if status == "failed":
                _mark_failed(db, order)
                db.commit()
                raise HTTPException(
                    status_code=402,
                    detail="Payment failed."
                )

            raise HTTPException(
                status_code=409,
                detail=(
                    f"Payment is not captured yet (status: {status or 'unknown'}). "
                    "Please wait a moment and check your order again."
                )
            )

        _mark_paid(db, order, payment_id)
        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except RazorpayError as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Could not verify payment status: {exc}"
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Payment verification could not be completed."
        )

    return {
        "success": True,
        "message": "Payment successful.",
        "order_id": order.id,
        "redirect_url": f"/account/orders/{order.id}?payment=success",
    }


@router.post("/account/payments/failed")
async def payment_failed(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Please log in")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment data")

    razorpay_order_id = str(
        data.get("razorpay_order_id", "")
    ).strip()

    if not razorpay_order_id:
        raise HTTPException(status_code=422, detail="Missing payment order")

    order = (
        db.query(Order)
        .filter(
            Order.razorpay_order_id == razorpay_order_id,
            Order.user_id == user.id,
        )
        .with_for_update()
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.payment_status == "Paid":
        return {"success": True}

    _mark_failed(db, order)
    db.commit()

    return {
        "success": True,
        "message": "Payment failed and the order was cancelled.",
        "redirect_url": f"/account/orders/{order.id}?payment=failed",
    }


@router.post("/payments/razorpay/webhook")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    payment = _payment_settings(db)

    if not payment or not payment.webhook_secret:
        raise HTTPException(
            status_code=503,
            detail="Webhook secret is not configured."
        )

    if not verify_webhook_signature(
        raw_body,
        signature,
        payment.webhook_secret,
    ):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    event = str(data.get("event", ""))

    payload = data.get("payload", {})

    payment_entity = (
        payload.get("payment", {}).get("entity", {})
        if isinstance(payload, dict)
        else {}
    )

    order_entity = (
        payload.get("order", {}).get("entity", {})
        if isinstance(payload, dict)
        else {}
    )

    razorpay_order_id = (
        payment_entity.get("order_id")
        or order_entity.get("id")
    )

    if not razorpay_order_id:
        # Valid webhook but not an order event we need.
        return {"received": True}

    order = (
        db.query(Order)
        .filter(
            Order.razorpay_order_id == razorpay_order_id
        )
        .with_for_update()
        .first()
    )

    if not order:
        # Keep the webhook response 2xx so Razorpay does not endlessly retry
        # a valid event for an order that is not in this database.
        return {"received": True}

    try:
        if event in {"payment.captured", "order.paid"}:
            payment_id = payment_entity.get("id")

            if payment_entity:
                expected_amount = int(
                    (Decimal(str(order.total_amount)) * 100)
                    .quantize(Decimal("1"))
                )
                received_amount = int(
                    payment_entity.get("amount", expected_amount)
                )

                if received_amount != expected_amount:
                    raise HTTPException(
                        status_code=400,
                        detail="Webhook amount mismatch"
                    )

            if order.status == "Cancelled" or order.stock_released:
                # The payment completed after this local order had already
                # been cancelled/released. Record the captured payment but
                # never resurrect fulfilment automatically.
                order.payment_status = "Paid"
                order.razorpay_payment_id = payment_id
                order.payment_verified_at = datetime.utcnow()
            else:
                _mark_paid(db, order, payment_id)

        elif event == "payment.failed":
            _mark_failed(db, order)

        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed"
        )

    return {"received": True}
