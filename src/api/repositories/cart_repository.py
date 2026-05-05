from __future__ import annotations

import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from src.database.models.cart_item import CartItem
from src.database.models.seller_product_spec import SellerProductSpec
from src.database.models.order import Order
from src.database.models.user import User


class CartRepository:
    """Repositório para operações de carrinho de compras."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, cart_item_id: uuid.UUID) -> Optional[CartItem]:
        """Busca um item do carrinho por ID."""
        return self.db.query(CartItem).filter(CartItem.id == cart_item_id).first()

    def list_for_user(self, user_id: uuid.UUID) -> List[CartItem]:
        """Lista todos os itens do carrinho de um usuário."""
        return self.db.query(CartItem).filter(CartItem.user_id == user_id).all()

    def list_for_user_grouped_by_seller(self, user_id: uuid.UUID) -> dict[uuid.UUID, List[CartItem]]:
        """Lista itens do carrinho agrupados por seller."""
        items = self.list_for_user(user_id)
        grouped: dict[uuid.UUID, List[CartItem]] = {}
        for item in items:
            if item.seller_id not in grouped:
                grouped[item.seller_id] = []
            grouped[item.seller_id].append(item)
        return grouped

    def create(
        self,
        user_id: uuid.UUID,
        seller_id: uuid.UUID,
        quantity: int,
        unit_price: Decimal,
        name: str,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        selected_options: Optional[str] = None,
        product_spec_id: Optional[uuid.UUID] = None,
        order_id: Optional[uuid.UUID] = None,
    ) -> CartItem:
        """Cria um novo item no carrinho."""
        total_price = unit_price * quantity
        cart_item = CartItem(
            user_id=user_id,
            seller_id=seller_id,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            name=name,
            description=description,
            image_url=image_url,
            selected_options=selected_options,
            product_spec_id=product_spec_id,
            order_id=order_id,
        )
        self.db.add(cart_item)
        self.db.commit()
        self.db.refresh(cart_item)
        return cart_item

    def update_quantity(self, cart_item: CartItem, quantity: int) -> CartItem:
        """Atualiza a quantidade de um item no carrinho."""
        cart_item.quantity = quantity
        cart_item.total_price = cart_item.unit_price * quantity
        self.db.commit()
        self.db.refresh(cart_item)
        return cart_item

    def delete(self, cart_item: CartItem) -> None:
        """Remove um item do carrinho."""
        self.db.delete(cart_item)
        self.db.commit()

    def clear_user_cart(self, user_id: uuid.UUID) -> None:
        """Remove todos os itens do carrinho de um usuário."""
        self.db.query(CartItem).filter(CartItem.user_id == user_id).delete()
        self.db.commit()

    def get_cart_total(self, user_id: uuid.UUID) -> Decimal:
        """Calcula o valor total do carrinho de um usuário."""
        items = self.list_for_user(user_id)
        return sum(item.total_price for item in items)

    def count_for_user(self, user_id: uuid.UUID) -> int:
        """Conta o número total de itens no carrinho de um usuário (soma das quantidades)."""
        items = self.list_for_user(user_id)
        return sum(item.quantity for item in items)

    def find_existing_item(
        self,
        user_id: uuid.UUID,
        product_spec_id: Optional[uuid.UUID] = None,
        order_id: Optional[uuid.UUID] = None,
        selected_options: Optional[str] = None,
    ) -> Optional[CartItem]:
        """
        Busca um item existente no carrinho que seja idêntico (mesmo produto/pedido e opções).
        Se não houver opções, ignora esse filtro.
        """
        query = self.db.query(CartItem).filter(CartItem.user_id == user_id)

        if product_spec_id:
            query = query.filter(CartItem.product_spec_id == product_spec_id)
        elif order_id:
            query = query.filter(CartItem.order_id == order_id)
        else:
            return None

        if selected_options:
            query = query.filter(CartItem.selected_options == selected_options)

        return query.first()
