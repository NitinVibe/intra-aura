from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        index=True,
        nullable=False
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    # Delivery profile fields. Nullable for backward compatibility with
    # existing customers; checkout enforces them when an order is placed.
    address: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )

    area_street: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    landmark: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    pincode: Mapped[str | None] = mapped_column(
        String(6),
        nullable=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    enquiries = relationship(
        "Enquiry",
        back_populates="user"
    )
    orders = relationship(
        "Order",
        back_populates="user"
    )