from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class SiteContent(Base):
    """Persistent CMS content for Vercel/serverless deployments."""

    __tablename__ = "site_content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
