from app.config.settings import settings
from datetime import datetime, timedelta, timezone


from fastapi import APIRouter, Request, Form, Depends, HTTPException
from jose import jwt, JWTError

from fastapi.responses import RedirectResponse
from app.template_config import Jinja2Templates


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

templates = Jinja2Templates(
    directory="app/templates"
)
SECRET_KEY = settings.secret_key

ALGORITHM = "HS256"

ADMIN_USERNAME = settings.admin_username

ADMIN_PASSWORD = settings.admin_password

@router.get("/login")
def login_page(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="admin/login.html"
    )


@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...)
):

    if (
        username != ADMIN_USERNAME
        or password != ADMIN_PASSWORD
    ):
        return RedirectResponse(
            url="/auth/login?error=1",
            status_code=303
        )

    expire = datetime.now(timezone.utc) + timedelta(hours=8)

    token = jwt.encode(
        {
            "sub": username,
            "exp": expire
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    response = RedirectResponse(
        url="/admin",
        status_code=303
    )

    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        max_age=8 * 60 * 60,
        samesite="lax"
    )

    return response


@router.get("/logout")
def logout():

    response = RedirectResponse(
        url="/auth/login",
        status_code=303
    )

    response.delete_cookie("admin_token")

    return response

def require_admin(
    request: Request
):
    token = request.cookies.get("admin_token")

    if not token:
        raise HTTPException(
            status_code=303,
            headers={
                "Location": "/auth/login"
            }
        )

    try:
        jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

    except JWTError:
        raise HTTPException(
            status_code=303,
            headers={
                "Location": "/auth/login"
            }
        )

    return True