from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from app.template_config import Jinja2Templates

from app.content.store import load_content
from app.routes.customer_auth import get_current_user


router = APIRouter(
    prefix="/account",
    tags=["Profile"]
)

templates = Jinja2Templates(
    directory="app/templates"
)

# Shared site content is required by base.html.
templates.env.globals["site"] = load_content


@router.get("/profile")
def profile_page(
    request: Request,
    user=Depends(get_current_user)
):

    if not user:
        return RedirectResponse(
            url="/account/login",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user
        }
    )