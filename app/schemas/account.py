from pydantic import BaseModel, Field, field_validator
import re


NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .\'-]{1,149}$")
MOBILE_RE = re.compile(r"^[6-9]\d{9}$")
PINCODE_RE = re.compile(r"^[1-9]\d{5}$")


def clean(value: str | None) -> str:
    return " ".join((value or "").strip().split())


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=200)
    phone: str = Field(min_length=10, max_length=10)
    address: str = Field(min_length=3, max_length=300)
    area_street: str = Field(min_length=2, max_length=200)
    landmark: str | None = Field(default=None, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    pincode: str = Field(min_length=6, max_length=6)

    @field_validator("name", "address", "area_street", "city", "state", "landmark", mode="before")
    @classmethod
    def normalize_text(cls, value):
        value = clean(value)
        return value or None if value is not None else value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return str(value or "").strip().lower()

    @field_validator("phone", "pincode", mode="before")
    @classmethod
    def normalize_digits(cls, value):
        return str(value or "").strip().replace(" ", "")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value or not NAME_RE.fullmatch(value):
            raise ValueError("Enter a valid full name")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if not MOBILE_RE.fullmatch(value):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return value

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, value):
        if not PINCODE_RE.fullmatch(value):
            raise ValueError("Enter a valid 6-digit Indian pincode")
        return value

    @field_validator("address", "area_street", "city", "state")
    @classmethod
    def validate_required_text(cls, value):
        if not value or not value.strip():
            raise ValueError("This field is required")
        return value

    @field_validator("landmark")
    @classmethod
    def validate_landmark(cls, value):
        if value is not None and not value.strip():
            return None
        return value


class CheckoutItem(BaseModel):
    id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)


class CheckoutRequest(BaseModel):
    items: list[CheckoutItem] = Field(min_length=1, max_length=100)
    profile: ProfileUpdate | None = None
