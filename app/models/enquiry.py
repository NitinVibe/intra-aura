from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class Enquiry(Base):
    __tablename__ = "enquiries"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    cart_data: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    cart_total: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    calculator_data: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    estimated_price: Mapped[float | None] = mapped_column(
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="new",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    product = relationship("Product")

    user = relationship(
        "User",
        back_populates="enquiries"
    )