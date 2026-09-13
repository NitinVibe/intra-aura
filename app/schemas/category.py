from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=120)
    description: str | None = None


class CategoryUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=120
    )

    description: str | None = None

    image_url: str | None = None


class CategoryResponse(BaseModel):

    id: int
    name: str
    slug: str
    description: str | None
    image_url: str | None

    model_config = ConfigDict(
        from_attributes=True
    )