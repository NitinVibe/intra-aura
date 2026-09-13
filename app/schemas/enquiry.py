from pydantic import BaseModel, EmailStr


class EnquiryCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    product_id: int | None = None
    message: str | None = None