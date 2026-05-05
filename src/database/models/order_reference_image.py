from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.database.models.order import Order


class OrderReferenceImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Imagens de referencia enviadas pelo cliente ao criar um pedido.
    Ex.: foto de inspiracao, screenshot, esboco a mao.
    """

    __tablename__ = "order_reference_images"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    image_key: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    order: Mapped["Order"] = relationship("Order", back_populates="reference_images")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OrderReferenceImage id={self.id} order={self.order_id}>"
