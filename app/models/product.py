from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    Numeric,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    Table,
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


# ============================================================
# PRODUCT ↔ CATEGORY ASSOCIATION TABLE
# ============================================================

product_categories = Table(
    "product_categories",
    Base.metadata,
    Column(
        "product_id",
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "category_id",
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True
    )
)


# ============================================================
# PRODUCT
# ============================================================

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    slug: Mapped[str] = mapped_column(
        String(220),
        nullable=False,
        unique=True,
        index=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    discount_price: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    material: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    color: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # ========================================================
    # CATEGORIES
    # ========================================================

    categories = relationship(
        "Category",
        secondary=product_categories,
        back_populates="products"
    )

    # ========================================================
    # IMAGES
    # ========================================================

    images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    @property
    def category_ids(self) -> list[int]:
        return [c.id for c in self.categories]


# ============================================================
# PRODUCT IMAGE
# ============================================================

class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    product = relationship(
        "Product",
        back_populates="images"
    )