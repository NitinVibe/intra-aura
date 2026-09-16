from fastapi import APIRouter, Depends, HTTPException, Request
from app.template_config import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from datetime import datetime
from app.models.user import User
from app.models.order import Order
from app.models.payment import PaymentSetting
from fastapi import Form
from fastapi.responses import RedirectResponse

from app.config.database import get_db
from app.models.category import Category
from app.models.product import Product, ProductImage
from app.models.enquiry import Enquiry
from app.routes.auth import require_admin
from app.services.order_stock import release_order_stock
import json

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)]
)




templates = Jinja2Templates(
    directory="app/templates"
)

templates.env.filters["from_json"] = json.loads


@router.get("")
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    products_count = db.query(Product).count()

    categories_count = db.query(Category).count()

    enquiries_count = db.query(Enquiry).count()

    new_enquiries_count = (
        db.query(Enquiry)
        .filter(Enquiry.status == "new")
        .count()
    )

    low_stock_count = (
        db.query(Product)
        .filter(Product.stock <= 5)
        .count()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "products_count": products_count,
            "categories_count": categories_count,
            "enquiries_count": enquiries_count,
            "new_enquiries_count": new_enquiries_count,
            "low_stock_count": low_stock_count,
        }
    )

@router.get("/categories")
def categories_page(
    request: Request,
    db: Session = Depends(get_db)
):
    categories = (
        db.query(Category)
        .order_by(Category.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/categories.html",
        context={
            "categories": categories
        }
    )
@router.get("/enquiries")
def enquiries_page(
    request: Request,
    db: Session = Depends(get_db)
):
    enquiries = (
        db.query(Enquiry)
        .order_by(Enquiry.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/enquiries.html",
        context={
            "enquiries": enquiries
        }
    )
@router.get("/enquiries/{enquiry_id}")
def enquiry_detail_page(
    enquiry_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    enquiry = (
        db.query(Enquiry)
        .filter(Enquiry.id == enquiry_id)
        .first()
    )

    if not enquiry:
        raise HTTPException(
            status_code=404,
            detail="Enquiry not found"
        )

    product = None
    cart_items = []

    # Single product enquiry
    if enquiry.product_id:
        product = (
            db.query(Product)
            .filter(Product.id == enquiry.product_id)
            .first()
        )

    # Cart enquiry
    if enquiry.cart_data:
        try:
            cart_items = json.loads(enquiry.cart_data)
        except (json.JSONDecodeError, TypeError):
            cart_items = []

    return templates.TemplateResponse(
        request=request,
        name="admin/enquiry_detail.html",
        context={
            "enquiry": enquiry,
            "product": product,
            "cart_items": cart_items
        }
    )

@router.post("/enquiries/{enquiry_id}/status")
def update_enquiry_status(
    enquiry_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    enquiry = (
        db.query(Enquiry)
        .filter(Enquiry.id == enquiry_id)
        .first()
    )

    if not enquiry:
        raise HTTPException(
            status_code=404,
            detail="Enquiry not found"
        )

    allowed_statuses = {
        "new",
        "contacted",
        "resolved"
    }

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid enquiry status"
        )

    enquiry.status = status

    db.commit()

    return RedirectResponse(
        url=f"/admin/enquiries/{enquiry_id}",
        status_code=303
    )

@router.delete("/enquiries/{enquiry_id}")
def delete_enquiry(
    enquiry_id: int,
    db: Session = Depends(get_db)
):
    enquiry = (
        db.query(Enquiry)
        .filter(Enquiry.id == enquiry_id)
        .first()
    )

    if not enquiry:
        raise HTTPException(
            status_code=404,
            detail="Enquiry not found"
        )

    db.delete(enquiry)
    db.commit()

    return {
        "message": "Enquiry deleted successfully"
    }

@router.get("/products")
def products_page(
    request: Request,
    search: str | None = None,
    category_id: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)

    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%")
        )

    if category_id and category_id != "all":
        query = (
            query
            .join(Product.categories)
            .filter(Category.id == int(category_id))
        )

    products = (
        query
        .order_by(Product.id.desc())
        .all()
    )

    categories = (
        db.query(Category)
        .order_by(Category.name.asc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/products.html",
        context={
            "products": products,
            "categories": categories,
            "search": search or "",
            "selected_category": category_id
        }
    )
@router.get("/products/new")
def new_product_page(
    request: Request,
    db: Session = Depends(get_db)
):
    categories = (
        db.query(Category)
        .order_by(Category.name.asc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/product_form.html",
        context={
            "categories": categories
        }
    )

@router.get("/products/{product_id}/edit")
def edit_product_page(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    categories = (
        db.query(Category)
        .order_by(Category.name.asc())
        .all()
    )

    images = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id)
        .order_by(ProductImage.sort_order.asc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/product_edit.html",
        context={
            "product": product,
            "categories": categories,
            "images": images
        }
    )
    

@router.get("/customers")
def customers_page(request: Request, db: Session = Depends(get_db)):
    customers = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(request=request, name="admin/customers.html", context={"customers": customers})


@router.get("/customers/{customer_id}")
def customer_detail_page(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    customer = db.query(User).filter(User.id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    enquiries = (
        db.query(Enquiry)
        .filter(Enquiry.user_id == customer_id)
        .order_by(Enquiry.id.desc())
        .all()
    )

    orders = []
    if inspect(db.bind).has_table("orders"):
        orders = (
            db.query(Order)
            .filter(Order.user_id == customer_id)
            .order_by(Order.created_at.desc())
            .all()
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/customer_detail.html",
        context={
            "customer": customer,
            "enquiries": enquiries,
            "orders": orders,
        },
    )


@router.get("/orders")
def admin_orders_page(
    request: Request,
    db: Session = Depends(get_db)
):
    orders_enabled = inspect(db.bind).has_table("orders")

    orders = (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .all()
        if orders_enabled
        else []
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/orders.html",
        context={
            "orders": orders,
            "orders_enabled": orders_enabled,
        },
    )


@router.get("/orders/{order_id}")
def admin_order_detail_page(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return templates.TemplateResponse(
        request=request,
        name="admin/order_detail.html",
        context={
            "order": order,
            "allowed_statuses": [
                "Pending",
                "Confirmed",
                "Processing",
                "Shipped",
                "Delivered",
                "Cancelled",
            ],
        },
    )



@router.post("/orders/{order_id}/status")
def update_admin_order_status(
    order_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    allowed = {
        "Pending",
        "Confirmed",
        "Processing",
        "Shipped",
        "Delivered",
        "Cancelled",
    }

    if status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid order status")

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if status in {"Confirmed", "Processing", "Shipped", "Delivered"} and order.payment_status != "Paid":
        raise HTTPException(
            status_code=409,
            detail="Payment must be captured before fulfilment can move beyond Pending."
        )

    if status == "Cancelled":
        if order.payment_status == "Paid":
            raise HTTPException(
                status_code=409,
                detail="A paid order cannot be cancelled here. Process a refund first."
            )

        if order.payment_status not in {"Failed", "Cancelled"}:
            release_order_stock(db, order)

        order.payment_status = (
            "Cancelled"
            if order.payment_status != "Failed"
            else order.payment_status
        )

    if order.payment_status == "Paid" and status == "Pending":
        raise HTTPException(
            status_code=400,
            detail="A paid order cannot be moved back to Pending."
        )

    order.status = status
    db.commit()

    return RedirectResponse(
        url=f"/admin/orders/{order_id}?updated=1",
        status_code=303
    )


@router.get("/settings")
def admin_settings_page(
    request: Request,
    db: Session = Depends(get_db)
):
    from app.content.store import load_content

    payment = db.query(PaymentSetting).filter(PaymentSetting.id == 1).first()

    webhook_url = (
        str(request.base_url).rstrip("/")
        + "/payments/razorpay/webhook"
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/settings.html",
        context={
            "content": load_content(),
            "payment": payment,
            "webhook_url": webhook_url,
        },
    )


@router.post("/settings")
async def admin_settings_save(
    request: Request,
    db: Session = Depends(get_db)
):
    from app.content.store import load_content, save_content

    form = await request.form()
    content = load_content()

    # -----------------------------
    # Existing site settings
    # -----------------------------
    content.setdefault("site", {})["name"] = str(
        form.get("name", "Intra Aura")
    ).strip()

    content["site"]["tagline"] = str(
        form.get("tagline", "")
    ).strip()

    content["site"]["copyright"] = str(
        form.get("copyright", "")
    ).strip()

    header = content.setdefault("header", {})
    existing = header.get("nav_links", [])

    by_label = {
        str(x.get("label", "")).strip().lower(): x.get("url", "")
        for x in existing
        if isinstance(x, dict)
    }

    labels = {
        "home": "Home",
        "products": "Products",
        "categories": "Categories",
        "services": "Services",
        "portfolio": "Portfolio",
        "about": "About Us",
        "contact": "Contact",
    }

    defaults = {
        "home": "/",
        "products": "/products",
        "categories": "/categories",
        "services": "/services",
        "portfolio": "/portfolio",
        "about": "/about",
        "contact": "/contact",
    }

    header["nav_links"] = [
        {
            "label": (
                str(form.get(f"nav_{k}", v)).strip() or v
            ),
            "url": by_label.get(v.lower(), defaults[k]),
        }
        for k, v in labels.items()
    ]

    save_content(content)

    # -----------------------------
    # Razorpay settings
    # -----------------------------
    payment = (
        db.query(PaymentSetting)
        .filter(PaymentSetting.id == 1)
        .first()
    )

    if not payment:
        payment = PaymentSetting(
            id=1,
            provider="razorpay",
            enabled=False,
            mode="test",
        )
        db.add(payment)

    mode = str(form.get("razorpay_mode", "test")).strip().lower()
    if mode not in {"test", "live"}:
        mode = "test"

    enabled = str(form.get("razorpay_enabled", "")).lower() in {
        "1", "true", "on", "yes"
    }

    key_id = str(form.get("razorpay_key_id", "")).strip()
    key_secret = str(form.get("razorpay_key_secret", "")).strip()
    webhook_secret = str(
        form.get("razorpay_webhook_secret", "")
    ).strip()

    if key_id:
        payment.key_id = key_id

    # Blank secret means "keep the existing secret".
    if key_secret:
        payment.key_secret = key_secret

    if webhook_secret:
        payment.webhook_secret = webhook_secret

    payment.mode = mode

    if enabled and not payment.key_id:
        db.rollback()
        return RedirectResponse(
            url="/admin/settings?payment_error=key_id",
            status_code=303
        )

    if enabled and not payment.key_secret:
        db.rollback()
        return RedirectResponse(
            url="/admin/settings?payment_error=key_secret",
            status_code=303
        )

    payment.enabled = enabled

    db.commit()

    return RedirectResponse(
        url="/admin/settings?saved=1",
        status_code=303
    )
