from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from app.template_config import Jinja2Templates

from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.content.store import load_content
from app.config.database import get_db
from app.config.settings import settings
from app.models.user import User
from app.models.enquiry import Enquiry


router = APIRouter(
    prefix="/account",
    tags=["Customer Account"]
)

import json

templates = Jinja2Templates(
    directory="app/templates"
)

# Shared site content is required by base.html.
templates.env.globals["site"] = load_content

templates.env.filters["from_json"] = json.loads

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ============================================================
# PASSWORD
# ============================================================

def hash_password(password: str) -> str:

    return pwd_context.hash(password)


def verify_password(
    password: str,
    password_hash: str
) -> bool:

    return pwd_context.verify(
        password,
        password_hash
    )

# ============================================================
# CURRENT USER
# ============================================================

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):

    token = request.cookies.get(
        "customer_token"
    )

    if not token:
        return None

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            return None

        user = (
            db.query(User)
            .filter(
                User.id == int(user_id)
            )
            .first()
        )

        return user

    except (
        JWTError,
        ValueError,
        TypeError
    ):

        return None
# ============================================================
# LOGIN PAGE
# ============================================================

@router.get("/login")
def login_page(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


# ============================================================
# LOGIN
# ============================================================
@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    email = email.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        return RedirectResponse(
            url="/account/login?error=1",
            status_code=303
        )

    if not verify_password(
        password,
        user.password_hash
    ):
        return RedirectResponse(
            url="/account/login?error=1",
            status_code=303
        )

    expire = (
        datetime.now(timezone.utc)
        + timedelta(days=7)
    )

    token = jwt.encode(
        {
            "sub": str(user.id),
            "exp": expire
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    response = RedirectResponse(
        url="/account/profile",
        status_code=303
    )

    response.set_cookie(
        key="customer_token",
        value=token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        samesite="lax"
    )

    return response
    # ============================================================
# SETTINGS
# ============================================================

@router.get("/settings")
def settings_page(
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
        name="settings.html",
        context={
            "user": user
        }
    )


# ============================================================
# CHANGE PASSWORD PAGE
# ============================================================

@router.get("/change-password")
def change_password_page(
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
        name="change_password.html",
        context={
            "user": user
        }
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

@router.post("/change-password")
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if not user:
        return RedirectResponse(
            url="/account/login",
            status_code=303
        )


    # CURRENT PASSWORD

    if not verify_password(
        current_password,
        user.password_hash
    ):

        return RedirectResponse(
            url="/account/change-password?error=current",
            status_code=303
        )


    # NEW PASSWORD MATCH

    if new_password != confirm_password:

        return RedirectResponse(
            url="/account/change-password?error=match",
            status_code=303
        )


    # PASSWORD LENGTH

    if len(new_password) < 8:

        return RedirectResponse(
            url="/account/change-password?error=length",
            status_code=303
        )


    # SAME PASSWORD

    if verify_password(
        new_password,
        user.password_hash
    ):

        return RedirectResponse(
            url="/account/change-password?error=same",
            status_code=303
        )


    # UPDATE PASSWORD

    user.password_hash = hash_password(
        new_password
    )

    db.commit()


    return RedirectResponse(
        url="/account/settings?password_changed=1",
        status_code=303
    )
# ============================================================
# REGISTER PAGE
# ============================================================

@router.get("/register")
def register_page(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )


# ============================================================
# REGISTER
# ============================================================

@router.post("/register")
def register(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    name = name.strip()
    email = email.strip().lower()
    phone = phone.strip()

    existing_user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    if existing_user:

        return RedirectResponse(
            url="/account/register?error=exists",
            status_code=303
        )

    user = User(
        name=name,
        email=email,
        phone=phone or None,
        password_hash=hash_password(password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return RedirectResponse(
        url="/account/login?registered=1",
        status_code=303
    )


# ============================================================
# LOGOUT
# ============================================================

@router.get("/logout")
def logout():

    response = RedirectResponse(
        url="/",
        status_code=303
    )

    response.delete_cookie(
        "customer_token"
    )

    return response

# ============================================================
# MY ENQUIRIES
# ============================================================

@router.get("/enquiries")
def my_enquiries(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if not user:
        return RedirectResponse(
            url="/account/login",
            status_code=303
        )

    enquiries = (
        db.query(Enquiry)
        .filter(
            (Enquiry.user_id == user.id) |
            (Enquiry.email == user.email)
        )
        .order_by(
            Enquiry.created_at.desc()
        )
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="my_enquiries.html",
        context={
            "user": user,
            "enquiries": enquiries
        }
    )

@router.get("/current-user")
def current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)

    if not user:
        return {
            "logged_in": False
        }

    return {
        "logged_in": True,
        "id": user.id
    }