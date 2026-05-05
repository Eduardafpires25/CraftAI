from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.database.models.user import User
    from src.database.models.seller_product_spec import SellerProductSpec
    from src.database.models.order import Order


class CartItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Item no carrinho de compras de um usuário.
    Pode ser:
    - Produto não personalizável (vindo diretamente de SellerProductSpec)
    - Pedido personalizável aceito (vindo de Order após seller aprovar e definir preço)
    """

    __tablename__ = "cart_items"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Produto não personalizável (opcional)
    product_spec_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seller_product_specs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Pedido personalizável aceito (opcional)
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Opções de personalização escolhidas (JSON)
    # Para produtos personalizáveis, ex: {"size": "250ml", "material": "ceramic"}
    selected_options: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Quantidade do item
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Preço unitário no momento de adicionar ao carrinho
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Preço total (quantity * unit_price)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Nome do produto/serviço (snapshot para não depender do produto original)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Descrição adicional (opcional)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # URL da imagem do produto (opcional)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ID do seller para agrupar itens por loja no carrinho
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
    )
    product_spec: Mapped[Optional["SellerProductSpec"]] = relationship(
        "SellerProductSpec",
        foreign_keys=[product_spec_id],
    )
    order: Mapped[Optional["Order"]] = relationship(
        "Order",
        foreign_keys=[order_id],
    )
    seller: Mapped["User"] = relationship(
        "User",
        foreign_keys=[seller_id],
    )

    def __repr__(self) -> str:
        return f"<CartItem id={self.id} user_id={self.user_id} quantity={self.quantity} total_price={self.total_price}>"
