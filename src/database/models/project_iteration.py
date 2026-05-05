from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from src.database.models.enums import IterationStatus

if TYPE_CHECKING:
    from src.database.models.order import Order
    from src.database.models.ai_generation import AIGeneration


class ProjectIteration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Cada versão/rascunho de um pedido personalizado.

    Um Order possui várias iterações conforme o cliente refina a descrição
    e regenera a imagem. Uma delas pode ser apontada como `approved_iteration`
    no Order.
    """

    __tablename__ = "project_iterations"
    __table_args__ = (
        UniqueConstraint("order_id", "version", name="uq_iteration_order_version"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Chave interna do storage (URL gerada via image_service)
    image_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    status: Mapped[IterationStatus] = mapped_column(
        SAEnum(IterationStatus, name="iteration_status", native_enum=False, length=20),
        nullable=False,
        default=IterationStatus.PENDING,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="iterations",
        foreign_keys=[order_id],
    )
    generation: Mapped[Optional["AIGeneration"]] = relationship(
        "AIGeneration",
        back_populates="iteration",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ProjectIteration id={self.id} order_id={self.order_id} v{self.version}>"
