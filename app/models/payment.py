from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class PaymentSetting(Base):
    __tablename__ = "payment_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    provider: Mapped[str] = mapped_column(
        String(30), default="razorpay", nullable=False
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    mode: Mapped[str] = mapped_column(
        String(10), default="test", nullable=False
    )

    key_id: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )

    # Stored server-side only. Never render this value to customers.
    key_secret: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    # Optional webhook secret configured in Razorpay Dashboard.
    webhook_secret: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
