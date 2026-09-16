import re

from pydantic import BaseModel, Field, field_validator


EMAIL_RE = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
PHONE_RE = re.compile(r"^[6-9]\d{9}$")


class SignupData(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: str = Field(max_length=200)
    phone: str = Field(min_length=10, max_length=10)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value):
        value = str(value or "").strip()
        if not value or not re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,148}", value):
            raise ValueError("Enter a valid full name")
        return value

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value):
        value = str(value or "").strip().lower()
        if not EMAIL_RE.fullmatch(value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, value):
        value = str(value or "").strip().replace(" ", "")
        if not PHONE_RE.fullmatch(value):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return value

    @field_validator("password")
    @classmethod
    def strong_password(cls, value):
        if len(value) < 8 or not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("Password must be at least 8 characters and contain a letter and a number")
        return value

    @field_validator("confirm_password")
    @classmethod
    def matching_password(cls, value, info):
        password = info.data.get("password")
        if password is not None and value != password:
            raise ValueError("Passwords do not match")
        return value
