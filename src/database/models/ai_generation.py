from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.database.models.project_iteration import ProjectIteration


class AIGeneration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Log de uma chamada à IA (geração de imagem ou completion estruturado)."""

    __tablename__ = "ai_generations"

    iteration_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_iterations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    kind: Mapped[str] = mapped_column(String(30), nullable=False)  # "image" | "completion"
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="openai")
    model: Mapped[str] = mapped_column(String(100), nullable=False)

    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    response_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True)

    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    iteration: Mapped[Optional["ProjectIteration"]] = relationship(
        "ProjectIteration", back_populates="generation"
    )
