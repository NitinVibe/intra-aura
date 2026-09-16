from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request, Form, Depends, HTTPException
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
from app.schemas.account import ProfileUpdate
from pydantic import ValidationError


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
# PROFILE VALIDATION / SERIALIZATION
# ============================================================

REQUIRED_CHECKOUT_FIELDS = (
    "name", "email", "phone", "address", "area_street",
    "city", "state", "pincode"
)


def user_profile_dict(user):
    return {
        "name": user.name or "",
        "email": user.email or "",
        "phone": user.phone or "",
        "address": user.address or "",
        "area_street": user.area_street or "",
        "landmark": user.landmark or "",
        "city": user.city or "",
        "state": user.state or "",
        "pincode": user.pincode or "",
    }


def profile_validation_issues(user):
    data = user_profile_dict(user)
    missing = [
        field for field in REQUIRED_CHECKOUT_FIELDS
        if not str(data.get(field, "")).strip()
    ]
    field_errors = {}
    try:
        ProfileUpdate.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            field = str(error.get("loc", ["profile"])[0])
            field_errors[field] = error.get("msg", "Invalid value")
    return missing, field_errors


def profile_missing_fields(user):
    return profile_validation_issues(user)[0]


def apply_profile(user, profile: ProfileUpdate):
    for field in (
        "name", "email", "phone", "address", "area_street",
        "landmark", "city", "state", "pincode"
    ):
        setattr(user, field, getattr(profile, field))


# ============================================================
# LOGIN PAGE
# ============================================================

@router.get("/login")
def login_page(
    request: Request
):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "next_url": _safe_next(request.query_params.get("next"))
        },
    )


def _safe_next(value: str | None) -> str:
    """
    Accept only local relative paths to prevent an open redirect.
    """
    value = (value or "").strip()

    if not value or not value.startswith("/") or value.startswith("//"):
        return "/account/profile"

    return value


# ============================================================
# LOGIN
# ============================================================
@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next_url: str = Form(""),
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
            url="/account/login?error=1"
            + (f"&next={_safe_next(next_url)}" if next_url else ""),
            status_code=303
        )

    if not verify_password(
        password,
        user.password_hash
    ):
        return RedirectResponse(
            url="/account/login?error=1"
            + (f"&next={_safe_next(next_url)}" if next_url else ""),
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
        url=_safe_next(next_url),
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
# EDIT PROFILE
# ============================================================

@router.get("/profile/edit")
def edit_profile_page(
    request: Request,
    user=Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/account/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="edit_profile.html",
        context={"user": user, "profile": user_profile_dict(user)}
    )


@router.post("/profile/edit")
def update_profile(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    area_street: str = Form(...),
    landmark: str = Form(""),
    city: str = Form(...),
    state: str = Form(...),
    pincode: str = Form(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/account/login", status_code=303)

    raw = {
        "name": name, "email": email, "phone": phone,
        "address": address, "area_street": area_street,
        "landmark": landmark, "city": city, "state": state,
        "pincode": pincode,
    }

    try:
        profile = ProfileUpdate.model_validate(raw)
    except ValidationError as exc:
        messages = {}
        for error in exc.errors():
            field = str(error.get("loc", ["profile"])[0])
            messages[field] = error.get("msg", "Invalid value")
        return templates.TemplateResponse(
            request=request,
            name="edit_profile.html",
            context={"user": user, "profile": raw, "errors": messages, "profile_error": "Please correct the highlighted fields."},
            status_code=422
        )

    duplicate = (
        db.query(User)
        .filter(User.email == profile.email, User.id != user.id)
        .first()
    )
    if duplicate:
        raw["email"] = profile.email
        return templates.TemplateResponse(
            request=request,
            name="edit_profile.html",
            context={"user": user, "profile": raw, "errors": {"email": "This email is already registered."}, "profile_error": "Please use a different email address."},
            status_code=409
        )

    try:
        apply_profile(user, profile)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="edit_profile.html",
            context={"user": user, "profile": raw, "errors": {}, "profile_error": "We could not save your profile. Please try again."},
            status_code=500
        )

    return RedirectResponse(url="/account/profile?profile_updated=1", status_code=303)


@router.get("/profile-data")
def profile_data(
    user=Depends(get_current_user)
):
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to continue")
    return user_profile_dict(user)


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
        Enquiry.user_id == user.id
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
    "id": user.id,
    "name": user.name,
    "email": user.email
}