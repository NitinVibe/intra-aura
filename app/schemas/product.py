from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# CREATE PRODUCT
# ============================================================

class ProductCreate(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=150
    )

    slug: str = Field(
        min_length=2,
        max_length=180
    )

    description: str | None = None

    price: float = Field(
        gt=0
    )

    discount_price: float | None = Field(
        default=None,
        gt=0
    )

    stock: int = Field(
        default=0,
        ge=0
    )

    material: str | None = None

    color: str | None = None

    # MULTIPLE CATEGORIES
    category_ids: list[int] = Field(
        min_length=1
    )


# ============================================================
# UPDATE PRODUCT
# ============================================================

class ProductUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=180
    )

    description: str | None = None

    price: float | None = Field(
        default=None,
        gt=0
    )

    discount_price: float | None = Field(
        default=None,
        gt=0
    )

    stock: int | None = Field(
        default=None,
        ge=0
    )

    material: str | None = None

    color: str | None = None

    # MULTIPLE CATEGORIES
    category_ids: list[int] | None = None

    is_active: bool | None = None


# ============================================================
# PRODUCT RESPONSE
# ============================================================
class ProductResponse(BaseModel):

    id: int
    name: str
    slug: str
    description: str | None

    price: float
    discount_price: float | None

    stock: int

    material: str | None
    color: str | None

    is_active: bool

    category_ids: list[int]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):

        if hasattr(obj, "categories"):

            data = {
                "id": obj.id,
                "name": obj.name,
                "slug": obj.slug,
                "description": obj.description,
                "price": obj.price,
                "discount_price": obj.discount_price,
                "stock": obj.stock,
                "material": obj.material,
                "color": obj.color,
                "is_active": obj.is_active,
                "category_ids": [
                    category.id
                    for category in obj.categories
                ],
                "created_at": obj.created_at,
                "updated_at": obj.updated_at,
            }

            return super().model_validate(
                data,
                *args,
                **kwargs
            )

        return super().model_validate(
            obj,
            *args,
            **kwargs
        )