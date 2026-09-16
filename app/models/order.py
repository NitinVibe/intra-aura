from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    total_amount: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    # Fulfilment status.
    status: Mapped[str] = mapped_column(
        String(30), default="Pending", nullable=False
    )

    # Payment lifecycle is deliberately separate from fulfilment status.
    payment_status: Mapped[str] = mapped_column(
        String(30), default="Pending", nullable=False
    )

    razorpay_order_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )

    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )

    payment_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # Stock is reserved by decrementing Product.stock when the local order
    # is created. Failed/cancelled unpaid orders release it exactly once.
    stock_released: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Delivery snapshot. This preserves the address used for this order even
    # if the customer later edits their profile.
    shipping_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    shipping_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    shipping_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    shipping_area_street: Mapped[str | None] = mapped_column(String(200), nullable=True)
    shipping_landmark: Mapped[str | None] = mapped_column(String(200), nullable=True)
    shipping_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_pincode: Mapped[str | None] = mapped_column(String(6), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="orders")

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

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
        String(200), nullable=False
    )

    price: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
