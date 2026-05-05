from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from src.database.models.enums import OrderStatus

if TYPE_CHECKING:
    from src.database.models.order import Order
    from src.database.models.user import User


class OrderStatusHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Auditoria de mudanças de status de um pedido."""

    __tablename__ = "order_status_history"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[Optional[OrderStatus]] = mapped_column(
        SAEnum(OrderStatus, name="order_status", native_enum=False, length=30),
        nullable=True,
    )
    to_status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status", native_enum=False, length=30),
        nullable=False,
    )
    changed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="status_history")
    changed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[changed_by_id])
