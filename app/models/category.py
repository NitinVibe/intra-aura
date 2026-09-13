from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.product import product_categories


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )

    slug: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True,
        index=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    products = relationship(
        "Product",
        secondary=product_categories,
        back_populates="categories"
    )