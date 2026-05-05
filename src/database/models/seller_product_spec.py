from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, ForeignKey, JSON, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.database.models.seller_profile import SellerProfile
    from src.database.models.seller_product_image import SellerProductImage


class SellerProductSpec(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Especificacao de um produto que um vendedor faz.
    Ex.: "Caneca 250ml branca", "Caneca 350ml preta", "Camiseta P/M/G algodao".

    O campo `attributes` (JSON) guarda detalhes flexiveis (volume, cor, tamanho)
    que sao usados pela IA para guiar perguntas ao cliente.
    """

    __tablename__ = "seller_product_specs"

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seller_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Atributos livres (volume, cor, material, tamanho, etc)
    # Ex.: {"volume_ml": 250, "color": "white", "material": "ceramic"}
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Se o produto e personalizavel pelo cliente (usando IA)
    is_customizable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')

    # Opcoes de personalizacao (tamanhos, materiais, etc)
    # Obrigatorio apenas quando is_customizable=True
    # Ex.: {"sizes": ["250ml", "300ml", "500ml"], "materials": ["ceramic", "glass"]}
    customization_options: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Preco base (opcional, pode ser orcamento por pedido)
    base_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    seller: Mapped["SellerProfile"] = relationship(
        "SellerProfile",
        back_populates="product_specs",
    )
    images: Mapped[List["SellerProductImage"]] = relationship(
        "SellerProductImage",
        back_populates="product_spec",
        cascade="all, delete-orphan",
        order_by="SellerProductImage.position",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SellerProductSpec id={self.id} name={self.name}>"
