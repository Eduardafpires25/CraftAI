import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from src.api.repositories.product_image_repository import SellerProductImageRepository
from src.database.models.seller_product_image import SellerProductImage
from src.database.models.seller_product_spec import SellerProductSpec


class TestSellerProductImageRepository:
    """Testes para SellerProductImageRepository."""

    def test_get_by_id_found(self, db_session: Session):
        """Testa buscar imagem por ID quando existe."""
        repo = SellerProductImageRepository(db_session)
        
        image = SellerProductImage(
            id=uuid4(),
            product_spec_id=uuid4(),
            image_key="test-key",
            position=0,
            is_cover=True,
        )
        db_session.add(image)
        db_session.commit()
        
        result = repo.get_by_id(image.id)
        assert result is not None
        assert result.id == image.id
        assert result.image_key == "test-key"

    def test_get_by_id_not_found(self, db_session: Session):
        """Testa buscar imagem por ID quando não existe."""
        repo = SellerProductImageRepository(db_session)
        result = repo.get_by_id(uuid4())
        assert result is None

    def test_list_by_product(self, db_session: Session):
        """Testa listar imagens de um produto."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        image1 = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="key1",
            position=1,
            is_cover=False,
        )
        image2 = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="key2",
            position=0,
            is_cover=True,
        )
        
        db_session.add(image1)
        db_session.add(image2)
        db_session.commit()
        
        result = repo.list_by_product(product_id)
        assert len(result) == 2
        # Deve estar ordenado por position
        assert result[0].position == 0
        assert result[1].position == 1

    def test_list_by_product_empty(self, db_session: Session):
        """Testa listar imagens de produto sem imagens."""
        repo = SellerProductImageRepository(db_session)
        result = repo.list_by_product(uuid4())
        assert result == []

    def test_get_cover_found(self, db_session: Session):
        """Testa buscar capa quando existe."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        image = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="cover-key",
            position=0,
            is_cover=True,
        )
        db_session.add(image)
        db_session.commit()
        
        result = repo.get_cover(product_id)
        assert result is not None
        assert result.is_cover is True

    def test_get_cover_not_found(self, db_session: Session):
        """Testa buscar capa quando não existe."""
        repo = SellerProductImageRepository(db_session)
        result = repo.get_cover(uuid4())
        assert result is None

    def test_count_by_product(self, db_session: Session):
        """Testa contar imagens de um produto."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        for i in range(3):
            image = SellerProductImage(
                id=uuid4(),
                product_spec_id=product_id,
                image_key=f"key{i}",
                position=i,
                is_cover=False,
            )
            db_session.add(image)
        db_session.commit()
        
        count = repo.count_by_product(product_id)
        assert count == 3

    def test_count_by_product_zero(self, db_session: Session):
        """Testa contar imagens de produto sem imagens."""
        repo = SellerProductImageRepository(db_session)
        count = repo.count_by_product(uuid4())
        assert count == 0

    def test_create_first_image_becomes_cover(self, db_session: Session):
        """Testa que primeira imagem vira capa automaticamente."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        image = repo.create(
            product_spec_id=product_id,
            image_key="first-key",
        )
        
        assert image.is_cover is True
        assert image.position == 0

    def test_create_with_position(self, db_session: Session):
        """Testa criar imagem com posição definida."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        image = repo.create(
            product_spec_id=product_id,
            image_key="key",
            position=5,
        )
        
        assert image.position == 5

    def test_create_with_cover_flag_unsets_previous(self, db_session: Session):
        """Testa que definir capa remove flag de anteriores."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        # Criar primeira imagem (vira capa)
        image1 = repo.create(
            product_spec_id=product_id,
            image_key="key1",
        )
        assert image1.is_cover is True
        
        # Criar segunda com is_cover=True
        image2 = repo.create(
            product_spec_id=product_id,
            image_key="key2",
            is_cover=True,
        )
        assert image2.is_cover is True
        
        # Primeira não deve mais ser capa
        db_session.refresh(image1)
        assert image1.is_cover is False

    def test_update_image(self, db_session: Session):
        """Testa atualizar imagem."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        image = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="old-key",
            alt_text="old alt",
            position=0,
            is_cover=False,
        )
        db_session.add(image)
        db_session.commit()
        
        updated = repo.update(image, alt_text="new alt", position=5)
        
        assert updated.alt_text == "new alt"
        assert updated.position == 5

    def test_update_set_cover_unsets_previous(self, db_session: Session):
        """Testa que atualizar para capa remove flag de anteriores."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        image1 = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="key1",
            position=0,
            is_cover=True,
        )
        image2 = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="key2",
            position=1,
            is_cover=False,
        )
        db_session.add(image1)
        db_session.add(image2)
        db_session.commit()
        
        repo.update(image2, is_cover=True)
        
        db_session.refresh(image1)
        assert image1.is_cover is False

    def test_delete_image(self, db_session: Session):
        """Testa deletar imagem."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        image = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="key",
            position=0,
            is_cover=True,
        )
        db_session.add(image)
        db_session.commit()
        
        key = repo.delete(image)
        
        assert key == "key"
        result = repo.get_by_id(image.id)
        assert result is None

    def test_delete_cover_promotes_next(self, db_session: Session):
        """Testa que deletar capa promove próxima."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        image1 = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="key1",
            position=0,
            is_cover=True,
        )
        image2 = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="key2",
            position=1,
            is_cover=False,
        )
        db_session.add(image1)
        db_session.add(image2)
        db_session.commit()
        
        repo.delete(image1)
        
        db_session.refresh(image2)
        assert image2.is_cover is True

    def test_delete_non_cover_no_promotion(self, db_session: Session):
        """Testa que deletar imagem não capa não promove."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        image1 = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="key1",
            position=0,
            is_cover=True,
        )
        image2 = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="key2",
            position=1,
            is_cover=False,
        )
        db_session.add(image1)
        db_session.add(image2)
        db_session.commit()
        
        repo.delete(image2)
        
        db_session.refresh(image1)
        assert image1.is_cover is True

    def test_unset_cover_all(self, db_session: Session):
        """Testa remover capa de todas as imagens."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        for i in range(3):
            image = SellerProductImage(
                id=uuid4(),
                product_spec_id=product_id,
                image_key=f"key{i}",
                position=i,
                is_cover=True,
            )
            db_session.add(image)
        db_session.commit()
        
        repo._unset_cover(product_id)
        
        images = repo.list_by_product(product_id)
        assert all(img.is_cover is False for img in images)

    def test_unset_cover_exclude_id(self, db_session: Session):
        """Testa remover capa exceto uma imagem."""
        repo = SellerProductImageRepository(db_session)
        
        product_id = uuid4()
        
        image1 = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="key1",
            position=0,
            is_cover=True,
        )
        image2 = SellerProductImage(
            id=uuid4(),
            product_spec_id=product_id,
            image_key="key2",
            position=1,
            is_cover=True,
        )
        db_session.add(image1)
        db_session.add(image2)
        db_session.commit()
        
        repo._unset_cover(product_id, exclude_id=image1.id)
        
        db_session.refresh(image1)
        db_session.refresh(image2)
        assert image1.is_cover is True
        assert image2.is_cover is False
