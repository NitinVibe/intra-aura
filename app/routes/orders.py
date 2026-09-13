from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from app.template_config import Jinja2Templates
from sqlalchemy.orm import Session

from app.content.store import load_content
from app.config.database import get_db
from app.routes.customer_auth import get_current_user
from app.models.order import Order

router = APIRouter(
    prefix="/account",
    tags=["Customer Orders"]
)

templates = Jinja2Templates(
    directory="app/templates"
)

# Shared site content is required by base.html.
templates.env.globals["site"] = load_content


@router.get("/orders")
def orders_page(
    request: Request,
    db: Session = Depends(get_db)
):

    user = get_current_user(request, db)

    if not user:
        return RedirectResponse(
            url="/account/login",
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
            "orders": orders
        }
    )