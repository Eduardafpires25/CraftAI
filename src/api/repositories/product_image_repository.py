from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import update
from sqlalchemy.orm import Session

from src.database.models.seller_product_image import SellerProductImage


class SellerProductImageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, image_id: uuid.UUID) -> Optional[SellerProductImage]:
        return (
            self.db.query(SellerProductImage)
            .filter(SellerProductImage.id == image_id)
            .first()
        )

    def list_by_product(self, product_spec_id: uuid.UUID) -> List[SellerProductImage]:
        return (
            self.db.query(SellerProductImage)
            .filter(SellerProductImage.product_spec_id == product_spec_id)
            .order_by(SellerProductImage.position, SellerProductImage.created_at)
            .all()
        )

    def get_cover(self, product_spec_id: uuid.UUID) -> Optional[SellerProductImage]:
        """Retorna a imagem de capa do produto."""
        return (
            self.db.query(SellerProductImage)
            .filter(
                SellerProductImage.product_spec_id == product_spec_id,
                SellerProductImage.is_cover == True,
            )
            .first()
        )

    def count_by_product(self, product_spec_id: uuid.UUID) -> int:
        return (
            self.db.query(SellerProductImage)
            .filter(SellerProductImage.product_spec_id == product_spec_id)
            .count()
        )

    def create(
        self,
        *,
        product_spec_id: uuid.UUID,
        image_key: str,
        alt_text: Optional[str] = None,
        is_cover: bool = False,
        position: Optional[int] = None,
    ) -> SellerProductImage:
        # Se for definida como capa, remove flag das outras
        if is_cover:
            self._unset_cover(product_spec_id)

        # Posicao default: ultima
        if position is None:
            position = self.count_by_product(product_spec_id)

        # Se for a primeira imagem, marca como capa automaticamente
        is_first = self.count_by_product(product_spec_id) == 0
        if is_first:
            is_cover = True

        image = SellerProductImage(
            product_spec_id=product_spec_id,
            image_key=image_key,
            alt_text=alt_text,
            is_cover=is_cover,
            position=position,
        )
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return image

    def update(self, image: SellerProductImage, **kwargs) -> SellerProductImage:
        # Se setar is_cover=True, remove flag das outras antes
        if kwargs.get("is_cover") is True:
            self._unset_cover(image.product_spec_id, exclude_id=image.id)

        for key, value in kwargs.items():
            if hasattr(image, key):
                setattr(image, key, value)
        self.db.commit()
        self.db.refresh(image)
        return image

    def delete(self, image: SellerProductImage) -> str:
        """Remove a imagem do banco e retorna a chave para o caller deletar do storage."""
        key = image.image_key
        product_id = image.product_spec_id
        was_cover = image.is_cover

        self.db.delete(image)
        self.db.commit()

        # Se era a capa, promove a primeira restante
        if was_cover:
            next_image = (
                self.db.query(SellerProductImage)
                .filter(SellerProductImage.product_spec_id == product_id)
                .order_by(SellerProductImage.position)
                .first()
            )
            if next_image:
                next_image.is_cover = True
                self.db.commit()

        return key

    def _unset_cover(
        self,
        product_spec_id: uuid.UUID,
        exclude_id: Optional[uuid.UUID] = None,
    ) -> None:
        q = update(SellerProductImage).where(
            SellerProductImage.product_spec_id == product_spec_id,
            SellerProductImage.is_cover == True,
        )
        if exclude_id:
            q = q.where(SellerProductImage.id != exclude_id)
        self.db.execute(q.values(is_cover=False))
        self.db.commit()
