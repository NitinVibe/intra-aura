from fastapi import APIRouter, Depends, Request
from app.template_config import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.product import Product
from app.models.category import Category
from app.content.store import load_content

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)
templates.env.globals["site"] = load_content


# ==========================================
# HOME
# ==========================================

@router.get("/")
def home_page(
    request: Request,
    db: Session = Depends(get_db)
):
    featured_products = (
        db.query(Product)
        .filter(Product.is_active == True)
        .order_by(Product.id.desc())
        .limit(6)
        .all()
    )

    categories = (
        db.query(Category)
        .order_by(Category.name.asc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "featured_products": featured_products,
            "categories": categories,
        }
    )


# ==========================================
# PRODUCTS
# ==========================================

@router.get("/products")
def products_page(
    request: Request,
    category_id: int | None = None,
    search: str | None = None,
    db: Session = Depends(get_db)
):
    # -----------------------------------------
    # PRODUCTS QUERY
    # -----------------------------------------

    query = db.query(Product).filter(
        Product.is_active == True
    )

    if category_id is not None:
        query = (
            query
            .join(Product.categories)
            .filter(Category.id == category_id)
        )

    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%")
        )

    products = (
        query
        .order_by(Product.id.desc())
        .all()
    )


    # -----------------------------------------
    # ALL CATEGORIES
    # -----------------------------------------

    categories = (
        db.query(Category)
        .order_by(Category.name.asc())
        .all()
    )


    # -----------------------------------------
    # SELECTED CATEGORY
    # -----------------------------------------

    selected_category = None

    if category_id is not None:
        selected_category = (
            db.query(Category)
            .filter(Category.id == category_id)
            .first()
        )


    # -----------------------------------------
    # SEND DATA TO TEMPLATE
    # -----------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={
            "products": products,
            "categories": categories,
            "selected_category": selected_category,
            "search": search or ""
        }
    )


# ==========================================
# PRODUCT DETAIL
# ==========================================

@router.get("/products/{product_id}")
def product_detail(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.is_active == True
        )
        .first()
    )

    if not product:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={
            "product": product
        }
    )


# ==========================================
# CATEGORIES
# ==========================================

@router.get("/categories")
def categories_page(
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
        name="categories.html",
        context={
            "categories": categories
        }
    )


# ==========================================
# SERVICES
# ==========================================

@router.get("/services")
def services_page(
    request: Request
):
    return templates.TemplateResponse(
        request=request,
        name="services.html"
    )


# ==========================================
# CONTACT
# ==========================================

@router.get("/contact")
def contact_page(
    request: Request,
    db: Session = Depends(get_db)
):
    products = (
        db.query(Product)
        .filter(Product.is_active == True)
        .order_by(Product.name.asc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context={
            "products": products
        }
    )


# ==========================================
# PORTFOLIO
# ==========================================

@router.get("/portfolio")
def portfolio_page(
    request: Request
):
    return templates.TemplateResponse(
        request=request,
        name="portfolio.html"
    )


# ==========================================
# ABOUT
# ==========================================

@router.get("/about")
def about_page(
    request: Request
):
    return templates.TemplateResponse(
        request=request,
        name="about.html"
    )


# ==========================================
# TERMS & CONDITIONS
# ==========================================

@router.get("/terms-and-conditions")
def terms_and_conditions_page(
    request: Request
):
    return templates.TemplateResponse(
        request=request,
        name="terms_and_conditions.html"
    )


# ==========================================
# PRICE CALCULATOR
# ==========================================

@router.get("/price-calculator")
def price_calculator_page(
    request: Request,
    db: Session = Depends(get_db)
):
    products = (
        db.query(Product)
        .filter(Product.is_active == True)
        .order_by(Product.name.asc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="price_calculator.html",
        context={
            "products": products
        }
    )


# ==========================================
# CART
# ==========================================

@router.get("/cart")
def cart_page(
    request: Request
):
    return templates.TemplateResponse(
        request=request,
        name="cart.html"
    )


# ==========================================
# WISHLIST
# ==========================================

@router.get("/wishlist")
def wishlist_page(
    request: Request
):
    return templates.TemplateResponse(
        request=request,
        name="wishlist.html"
    )