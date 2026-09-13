from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    Integer,
    ForeignKey,
    Numeric
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class Order(Base):

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    total_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Pending",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="orders"
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )


class OrderItem(Base):

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    product_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    order = relationship(
        "Order",
        back_populates="items"
    )

    product = relationship(
        "Product"
    )