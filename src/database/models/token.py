from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.database.models.user import User


class Token(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    token_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "access" | "refresh"
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship("User", back_populates="tokens")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Token id={self.id} type={self.token_type} user_id={self.user_id} active={self.is_active}>"
