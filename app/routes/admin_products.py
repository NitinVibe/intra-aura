from fastapi import APIRouter, Depends, Request
from app.template_config import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.product import Product
from app.models.category import Category
from app.routes.auth import require_admin
import json

router = APIRouter(
    prefix="/admin",
    tags=["Admin Products"],
    dependencies=[Depends(require_admin)]
)

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get("/products")
def products_page(
    request: Request,
    db: Session = Depends(get_db)
):
    products = (
        db.query(Product)
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
            "categories": categories
        }
    )