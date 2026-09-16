from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from app.template_config import Jinja2Templates

from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext
import hashlib
import hmac
import secrets
import re

from app.content.store import load_content
from app.config.database import get_db
from app.config.settings import settings
from app.models.user import User
from app.models.enquiry import Enquiry
from app.models.otp import AuthOTP
from app.models.auth_attempt import AuthLoginAttempt
from app.schemas.account import ProfileUpdate
from pydantic import ValidationError
from app.schemas.auth import SignupData
from app.services.email import send_auth_otp, smtp_configured


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
# AUTH / OTP HELPERS
# ============================================================

OTP_PURPOSE_SIGNUP = "signup"
OTP_PURPOSE_RESET = "password_reset"
OTP_PURPOSES = {OTP_PURPOSE_SIGNUP, OTP_PURPOSE_RESET}


def _utcnow() -> datetime:
    return datetime.utcnow()


def _otp_hash(code: str) -> str:
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        code.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _issue_otp(db: Session, *, user: User, purpose: str, target: str) -> AuthOTP:
    if purpose not in OTP_PURPOSES:
        raise ValueError("Invalid OTP purpose")
    if not smtp_configured():
        raise RuntimeError("Customer OTP email service is not configured.")

    now = _utcnow()
    existing = (
        db.query(AuthOTP)
        .filter(
            AuthOTP.user_id == user.id,
            AuthOTP.purpose == purpose,
            AuthOTP.used_at.is_(None),
        )
        .order_by(AuthOTP.created_at.desc())
        .first()
    )

    if existing and existing.last_sent_at and existing.expires_at > now:
        elapsed = (now - existing.last_sent_at).total_seconds()
        if elapsed < settings.OTP_RESEND_COOLDOWN_SECONDS:
            remaining = max(1, int(settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed))
            raise ValueError(f"Please wait {remaining} seconds before requesting another OTP.")
        if existing.resend_count >= settings.OTP_MAX_RESENDS:
            raise ValueError("Maximum OTP resend limit reached. Please try again later.")
        existing.resend_count += 1
        existing.attempts = 0
        otp = _generate_otp()
        existing.code_hash = _otp_hash(otp)
        existing.expires_at = now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        existing.last_sent_at = now
        db.flush()
    else:
        otp = _generate_otp()
        existing = AuthOTP(
            user_id=user.id,
            purpose=purpose,
            target=target,
            code_hash=_otp_hash(otp),
            expires_at=now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
            attempts=0,
            resend_count=0,
            last_sent_at=now,
        )
        db.add(existing)
        db.flush()

    # Send only after the DB row is ready; if delivery fails, caller rolls back.
    send_auth_otp(target, otp, purpose)
    return existing


def _create_login_response(user: User, next_url: str | None = None, request: Request | None = None) -> RedirectResponse:
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    token = jwt.encode(
        {"sub": str(user.id), "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    response = RedirectResponse(url=_safe_next(next_url), status_code=303)
    response.set_cookie(
        key="customer_token",
        value=token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        samesite="lax",
        secure=bool(request and request.url.scheme == "https"),
    )
    return response


def _safe_next(value: str | None) -> str:
    """Accept only local relative paths to prevent open redirects."""
    value = (value or "").strip()
    if not value or not value.startswith("/") or value.startswith("//"):
        return "/account/profile"
    return value


def _auth_error_message(exc: Exception) -> str:
    message = str(exc)
    if "OTP email service is not configured" in message:
        return "Email OTP is not configured yet. Please contact the administrator."
    return message or "Unable to continue. Please try again."


def _login_client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _login_is_locked(db: Session, email: str, client_key: str) -> bool:
    row = (
        db.query(AuthLoginAttempt)
        .filter(AuthLoginAttempt.email == email, AuthLoginAttempt.client_key == client_key)
        .first()
    )
    return bool(row and row.locked_until and row.locked_until > _utcnow())


def _record_login_failure(db: Session, email: str, client_key: str) -> None:
    now = _utcnow()
    row = (
        db.query(AuthLoginAttempt)
        .filter(AuthLoginAttempt.email == email, AuthLoginAttempt.client_key == client_key)
        .first()
    )
    if not row:
        row = AuthLoginAttempt(email=email, client_key=client_key, failed_attempts=0)
        db.add(row)
        db.flush()
    row.failed_attempts += 1
    row.last_attempt_at = now
    if row.failed_attempts >= settings.LOGIN_MAX_FAILED_ATTEMPTS:
        row.locked_until = now + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
    db.commit()


def _clear_login_failures(db: Session, email: str, client_key: str) -> None:
    row = (
        db.query(AuthLoginAttempt)
        .filter(AuthLoginAttempt.email == email, AuthLoginAttempt.client_key == client_key)
        .first()
    )
    if row:
        db.delete(row)
        db.commit()


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
    client_key = _login_client_key(request)

    if _login_is_locked(db, email, client_key):
        return RedirectResponse(
            url="/account/login?error=locked" + (f"&next={_safe_next(next_url)}" if next_url else ""),
            status_code=303,
        )

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password_hash):
        _record_login_failure(db, email, client_key)
        return RedirectResponse(
            url="/account/login?error=1" + (f"&next={_safe_next(next_url)}" if next_url else ""),
            status_code=303,
        )

    _clear_login_failures(db, email, client_key)

    if not user.is_verified:
        return RedirectResponse(
            url=f"/account/verify-otp?purpose={OTP_PURPOSE_SIGNUP}&email={email}&next={_safe_next(next_url)}&error=unverified",
            status_code=303,
        )

    return _create_login_response(user, next_url, request)

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
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "form": {},
            "next_url": _safe_next(request.query_params.get("next")),
        },
    )


@router.post("/register")
def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    next_url: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        data = SignupData(
            name=name,
            email=email,
            phone=phone,
            password=password,
            confirm_password=confirm_password,
        )
    except ValidationError as exc:
        errors = {}
        for error in exc.errors():
            field = str(error.get("loc", ["form"])[0])
            errors[field] = error.get("msg", "Invalid value")
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "errors": errors,
                "form_error": "Please correct the highlighted fields.",
                "form": {"name": name, "email": email, "phone": phone},
                "next_url": _safe_next(next_url),
            },
            status_code=422,
        )

    existing_user = db.query(User).filter(User.email == data.email).first()
    phone_user = (
        db.query(User)
        .filter(User.phone == data.phone, User.email != data.email)
        .first()
    )

    if phone_user:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "form_error": "This mobile number is already registered.",
                "errors": {"phone": "This mobile number is already registered."},
                "form": {"name": data.name, "email": data.email, "phone": data.phone},
                "next_url": _safe_next(next_url),
            },
            status_code=409,
        )

    try:
        if existing_user and existing_user.is_verified:
            return templates.TemplateResponse(
                request=request,
                name="register.html",
                context={
                    "form_error": "An account with this email already exists. Please sign in.",
                    "errors": {"email": "This email is already registered."},
                    "form": {"name": data.name, "email": data.email, "phone": data.phone},
                    "next_url": _safe_next(next_url),
                },
                status_code=409,
            )

        if existing_user and not existing_user.is_verified:
            user = existing_user
            user.name = data.name
            user.email = data.email
            user.phone = data.phone
            user.password_hash = hash_password(data.password)
        else:
            user = User(
                name=data.name,
                email=data.email,
                phone=data.phone,
                password_hash=hash_password(data.password),
                is_verified=False,
            )
            db.add(user)
            db.flush()

        otp = _issue_otp(
            db,
            user=user,
            purpose=OTP_PURPOSE_SIGNUP,
            target=user.email,
        )
        db.commit()

    except ValueError as exc:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "form_error": _auth_error_message(exc),
                "form": {"name": data.name, "email": data.email, "phone": data.phone},
                "next_url": _safe_next(next_url),
            },
            status_code=429,
        )
    except Exception as exc:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "form_error": _auth_error_message(exc),
                "form": {"name": data.name, "email": data.email, "phone": data.phone},
                "next_url": _safe_next(next_url),
            },
            status_code=503,
        )

    return RedirectResponse(
        url=f"/account/verify-otp?purpose={OTP_PURPOSE_SIGNUP}&email={user.email}&next={_safe_next(next_url)}",
        status_code=303,
    )


# ============================================================
# OTP VERIFICATION
# ============================================================

@router.get("/verify-otp")
def verify_otp_page(request: Request):
    purpose = request.query_params.get("purpose", OTP_PURPOSE_SIGNUP)
    if purpose not in OTP_PURPOSES:
        purpose = OTP_PURPOSE_SIGNUP
    return templates.TemplateResponse(
        request=request,
        name="verify_otp.html",
        context={
            "email": request.query_params.get("email", "").strip().lower(),
            "purpose": purpose,
            "next_url": _safe_next(request.query_params.get("next")),
            "error": request.query_params.get("error", ""),
        },
    )


@router.post("/verify-otp")
def verify_otp(
    request: Request,
    email: str = Form(...),
    otp: str = Form(...),
    purpose: str = Form(...),
    next_url: str = Form(""),
    db: Session = Depends(get_db),
):
    email = email.strip().lower()
    otp = otp.strip()
    if purpose not in OTP_PURPOSES or not re.fullmatch(r"\d{6}", otp):
        return RedirectResponse(
            url=f"/account/verify-otp?purpose={OTP_PURPOSE_SIGNUP}&email={email}&next={_safe_next(next_url)}&error=invalid",
            status_code=303,
        )

    user = db.query(User).filter(User.email == email).first()
    record = None
    if user:
        record = (
            db.query(AuthOTP)
            .filter(
                AuthOTP.user_id == user.id,
                AuthOTP.purpose == purpose,
                AuthOTP.target == email,
                AuthOTP.used_at.is_(None),
            )
            .order_by(AuthOTP.created_at.desc())
            .first()
        )

    now = _utcnow()
    if not record or record.expires_at <= now:
        return RedirectResponse(
            url=f"/account/verify-otp?purpose={purpose}&email={email}&next={_safe_next(next_url)}&error=expired",
            status_code=303,
        )

    if record.attempts >= settings.OTP_MAX_ATTEMPTS:
        return RedirectResponse(
            url=f"/account/verify-otp?purpose={purpose}&email={email}&next={_safe_next(next_url)}&error=attempts",
            status_code=303,
        )

    record.attempts += 1
    if not hmac.compare_digest(record.code_hash, _otp_hash(otp)):
        db.commit()
        return RedirectResponse(
            url=f"/account/verify-otp?purpose={purpose}&email={email}&next={_safe_next(next_url)}&error=invalid",
            status_code=303,
        )

    record.used_at = now
    if purpose == OTP_PURPOSE_SIGNUP:
        user.is_verified = True
        db.commit()
        return _create_login_response(user, next_url, request)

    # Password-reset OTP grants only a short-lived, HttpOnly reset session.
    db.commit()
    reset_exp = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    reset_token = jwt.encode(
        {"sub": str(user.id), "purpose": "password_reset", "exp": reset_exp},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    response = RedirectResponse(url="/account/reset-password", status_code=303)
    response.set_cookie(
        key="password_reset_token",
        value=reset_token,
        httponly=True,
        max_age=settings.OTP_EXPIRY_MINUTES * 60,
        samesite="lax",
        secure=request.url.scheme == "https",
    )
    return response


@router.post("/resend-otp")
def resend_otp(
    email: str = Form(...),
    purpose: str = Form(...),
    next_url: str = Form(""),
    db: Session = Depends(get_db),
):
    email = email.strip().lower()
    if purpose not in OTP_PURPOSES:
        raise HTTPException(status_code=400, detail="Invalid OTP purpose")

    user = db.query(User).filter(User.email == email).first()
    if not user or (purpose == OTP_PURPOSE_SIGNUP and user.is_verified):
        # Do not disclose whether an account exists.
        return RedirectResponse(
            url=f"/account/verify-otp?purpose={purpose}&email={email}&next={_safe_next(next_url)}&resent=1",
            status_code=303,
        )

    try:
        _issue_otp(db, user=user, purpose=purpose, target=email)
        db.commit()
    except ValueError as exc:
        db.rollback()
        return RedirectResponse(
            url=f"/account/verify-otp?purpose={purpose}&email={email}&next={_safe_next(next_url)}&error=rate",
            status_code=303,
        )
    except Exception:
        db.rollback()
        return RedirectResponse(
            url=f"/account/verify-otp?purpose={purpose}&email={email}&next={_safe_next(next_url)}&error=delivery",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/account/verify-otp?purpose={purpose}&email={email}&next={_safe_next(next_url)}&resent=1",
        status_code=303,
    )


# ============================================================
# FORGOT / RESET PASSWORD
# ============================================================

@router.get("/forgot-password")
def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={"email": request.query_params.get("email", ""), "sent": request.query_params.get("sent")},
    )


@router.post("/forgot-password")
def forgot_password(
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user:
        try:
            _issue_otp(db, user=user, purpose=OTP_PURPOSE_RESET, target=email)
            db.commit()
        except Exception:
            db.rollback()
            # Keep the outward response generic.
    return RedirectResponse(
        url=f"/account/forgot-password?sent=1&email={email}",
        status_code=303,
    )


@router.get("/reset-password")
def reset_password_page(request: Request):
    token = request.cookies.get("password_reset_token")
    valid = False
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            valid = payload.get("purpose") == "password_reset" and bool(payload.get("sub"))
        except JWTError:
            valid = False
    if not valid:
        return RedirectResponse(url="/account/forgot-password", status_code=303)
    return templates.TemplateResponse(request=request, name="reset_password.html")


@router.post("/reset-password")
def reset_password(
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    token = request.cookies.get("password_reset_token") if request else None
    try:
        payload = jwt.decode(token or "", SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise JWTError()
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        return RedirectResponse(url="/account/forgot-password?error=expired", status_code=303)

    if new_password != confirm_password:
        return RedirectResponse(url="/account/reset-password?error=match", status_code=303)
    if len(new_password) < 8 or not re.search(r"[A-Za-z]", new_password) or not re.search(r"\\d", new_password):
        return RedirectResponse(url="/account/reset-password?error=weak", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/account/forgot-password?error=expired", status_code=303)

    user.password_hash = hash_password(new_password)
    db.commit()
    response = RedirectResponse(url="/account/login?reset=1", status_code=303)
    response.delete_cookie("password_reset_token")
    return response


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