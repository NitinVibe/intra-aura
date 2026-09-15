from fastapi import (
    APIRouter,
    Request,
    Form,
    Depends,
    HTTPException
)
from fastapi.responses import RedirectResponse
from app.template_config import Jinja2Templates
from sqlalchemy.orm import Session

from app.content.store import load_content
from app.config.database import get_db
from app.models.product import Product
from app.models.enquiry import Enquiry
import json
from jose import jwt, JWTError
from app.config.settings import settings
from app.models.user import User
from app.routes.customer_auth import get_current_user
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"

router = APIRouter(
    tags=["Enquiries"]
)


templates = Jinja2Templates(
    directory="app/templates"
)

# Shared site content is required by base.html.
templates.env.globals["site"] = load_content


# ============================================================
# PRODUCT ENQUIRY PAGE
# ============================================================

@router.get("/products/{product_id}/enquire")
def enquiry_page(
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
        return RedirectResponse(
            url="/products",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="enquiry_form.html",
        context={
            "product": product
        }
    )


# ============================================================
# PRODUCT ENQUIRY SUBMIT
# ============================================================

@router.post("/products/{product_id}/enquire")
def submit_product_enquiry(
    product_id: int,
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db)
):

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        return RedirectResponse(
            url="/products",
            status_code=303
        )

    enquiry = Enquiry(
        name=name,
        email=email,
        phone=phone,
        product_id=product.id,
        message=message,
        status="new"
    )

    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)

    return RedirectResponse(
        url=f"/products/{product.id}/enquire?success=1",
        status_code=303
    )


# ============================================================
# GENERAL CONTACT / GET A QUOTE / PRICE CALCULATOR ENQUIRY
# ============================================================

@router.post("/enquiries/")
async def create_general_enquiry(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    try:
        data = await request.json()

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid request data"
        )

    # ========================================================
    # CUSTOMER DATA
    # ========================================================

    name = str(
        data.get("name", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip().lower()

    phone = str(
        data.get("phone", "")
    ).strip()

    message = str(
        data.get("message", "")
    ).strip()

    # ========================================================
    # OPTIONAL DATA
    # ========================================================

    product_id = data.get("product_id")

    cart_data = data.get("cart_data")
    cart_total = data.get("cart_total")

    calculator_data = data.get("calculator_data")
    estimated_price = data.get("estimated_price")

    # ========================================================
    # VALIDATION
    # ========================================================

    if not name:
        raise HTTPException(
            status_code=422,
            detail="Name is required"
        )

    if not email:
        raise HTTPException(
            status_code=422,
            detail="Email is required"
        )

    if not phone:
        raise HTTPException(
            status_code=422,
            detail="Phone is required"
        )

    # ========================================================
    # CART DATA
    # ========================================================

    if cart_data is not None:

        if not isinstance(cart_data, str):
            raise HTTPException(
                status_code=422,
                detail="Invalid cart data"
            )

    # ========================================================
    # CART TOTAL
    # ========================================================

    if cart_total is not None:

        try:
            cart_total = float(cart_total)

        except (TypeError, ValueError):
            raise HTTPException(
                status_code=422,
                detail="Invalid cart total"
            )

    # ========================================================
    # ESTIMATED PRICE
    # ========================================================

    if estimated_price is not None:

        try:
            estimated_price = float(
                estimated_price
            )

        except (TypeError, ValueError):
            raise HTTPException(
                status_code=422,
                detail="Invalid estimated price"
            )

    # ========================================================
    # PRODUCT
    # ========================================================

    product = None

    if product_id is not None:

        try:
            product_id = int(product_id)

        except (TypeError, ValueError):
            raise HTTPException(
                status_code=422,
                detail="Invalid product"
            )

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Selected product not found"
            )

    # ========================================================
    # USER
    # ========================================================
    #
    # IMPORTANT:
    # We get the logged-in user from the customer_token.
    # We do NOT trust the frontend to provide user_id.
    #
    # This makes calculator enquiries appear in
    # /account/enquiries for the logged-in customer.
    # ========================================================

    user_id = None

    if user:
        user_id = user.id

    # ========================================================
    # CREATE ENQUIRY
    # ========================================================

    enquiry = Enquiry(

        # Logged-in customer's ID
        user_id=user_id,

        # Customer information
        name=name,
        email=email,
        phone=phone,

        # Product enquiry
        product_id=(
            product.id
            if product
            else None
        ),

        # Cart enquiry
        cart_data=cart_data,
        cart_total=cart_total,

        # Price calculator enquiry
        calculator_data=calculator_data,
        estimated_price=estimated_price,

        # Message
        message=message,

        # Initial status
        status="new"
    )

    # ========================================================
    # SAVE
    # ========================================================

    db.add(enquiry)

    db.commit()

    db.refresh(enquiry)

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "message": "Enquiry submitted successfully",
        "enquiry_id": enquiry.id,
        "user_id": enquiry.user_id
    }