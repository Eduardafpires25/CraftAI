from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.database.models.seller_product_spec import SellerProductSpec


class SellerProductImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Imagens de um produto (SellerProductSpec).
    Um produto pode ter multiplas imagens; uma delas marcada como capa (is_cover).
    """

    __tablename__ = "seller_product_images"

    product_spec_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seller_product_specs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Chave no storage (ex.: "products/abc-123/uuid.png")
    image_key: Mapped[str] = mapped_column(String(500), nullable=False)

    # Texto alternativo para acessibilidade
    alt_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Posicao para ordenar (galeria)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Capa do produto (mostrada em listagens)
    is_cover: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    product_spec: Mapped["SellerProductSpec"] = relationship(
        "SellerProductSpec", back_populates="images"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SellerProductImage id={self.id} product={self.product_spec_id} cover={self.is_cover}>"
