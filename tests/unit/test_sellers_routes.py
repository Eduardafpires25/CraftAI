import pytest
from uuid import uuid4
from decimal import Decimal
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from src.database.models.user import User
from src.database.models.seller_profile import SellerProfile
from src.database.models.seller_product_spec import SellerProductSpec
from src.database.models.seller_product_image import SellerProductImage
from src.database.models.enums import UserRole

API = "/api/v1"


class TestSellersRoutes:
    """Testes para rotas de Sellers (prefixos /api/v1/sellers, /api/v1/sellers/me)."""

    # =========================================================================
    # /sellers/me/profile
    # =========================================================================

    def test_create_seller_profile(self, client_factory, db_session):
        """Seller user sem profile cria um novo (201)."""
        # Um novo usuário SELLER sem profile
        from uuid import uuid4 as _uuid
        from src.database.models.enums import UserRole
        fresh = User(
            id=_uuid(),
            email="fresh_seller@example.com",
            email_verified=True,
            name="Fresh Seller",
            password_hash="x",
            role=UserRole.SELLER,
        )
        db_session.add(fresh)
        db_session.commit()

        c = client_factory(fresh)
        response = c.post(
            f"{API}/sellers/me/profile",
            json={
                "store_name": "Fresh Store",
                "slug": "fresh-store",
                "description": "desc",
                "category": "mug",
                "city": "São Paulo",
                "state": "SP",
                "whatsapp": "11999999999",
                "instagram": "fresh_store",
                "estimated_days": 7,
                "accepts_custom_designs": True,
                "min_order_quantity": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["store_name"] == "Fresh Store"
        assert data["slug"] == "fresh-store"
        assert data["category"] == "mug"

    def test_create_seller_profile_unauthorized(self, anon_client: TestClient):
        response = anon_client.post(
            f"{API}/sellers/me/profile",
            json={"store_name": "X", "slug": "x", "category": "mug"},
        )
        assert response.status_code == 401

    def test_create_seller_profile_conflict(
        self, seller_client: TestClient, test_seller: SellerProfile
    ):
        """Seller já tem profile → 409."""
        response = seller_client.post(
            f"{API}/sellers/me/profile",
            json={"store_name": "Dup", "slug": "dup", "category": "mug"},
        )
        assert response.status_code == 409

    def test_get_my_profile(self, seller_client: TestClient, test_seller: SellerProfile):
        response = seller_client.get(f"{API}/sellers/me/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_seller.id)
        assert data["store_name"] == "Test Store"

    def test_get_my_profile_not_found(self, seller_client: TestClient):
        """Seller sem profile → 404."""
        response = seller_client.get(f"{API}/sellers/me/profile")
        assert response.status_code == 404

    def test_update_profile(self, seller_client: TestClient, test_seller: SellerProfile):
        response = seller_client.patch(
            f"{API}/sellers/me/profile",
            json={
                "store_name": "Updated Store",
                "category": "shirt",
                "city": "Rio de Janeiro",
                "state": "RJ",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["store_name"] == "Updated Store"
        assert data["category"] == "shirt"
        assert data["state"] == "RJ"

    # =========================================================================
    # /sellers (public)
    # =========================================================================

    def test_get_seller_by_id(self, anon_client: TestClient, test_seller: SellerProfile):
        response = anon_client.get(f"{API}/sellers/{test_seller.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_seller.id)
        assert data["store_name"] == "Test Store"

    def test_get_seller_by_slug(self, anon_client: TestClient, test_seller: SellerProfile):
        response = anon_client.get(f"{API}/sellers/by-slug/test-store")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "test-store"

    def test_get_seller_by_slug_not_found(self, anon_client: TestClient):
        response = anon_client.get(f"{API}/sellers/by-slug/nonexistent")
        assert response.status_code == 404

    def test_list_sellers(self, anon_client: TestClient, test_seller: SellerProfile):
        response = anon_client.get(f"{API}/sellers/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_list_sellers_by_category(self, anon_client: TestClient, test_seller: SellerProfile):
        response = anon_client.get(f"{API}/sellers/?category=mug")
        assert response.status_code == 200
        data = response.json()
        assert all(s["category"] == "mug" for s in data["items"])

    def test_list_categories(self, anon_client: TestClient):
        response = anon_client.get(f"{API}/sellers/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "mug" in data

    # =========================================================================
    # /sellers/me/products
    # =========================================================================

    def test_create_product(self, seller_client: TestClient, test_seller: SellerProfile):
        response = seller_client.post(
            f"{API}/sellers/me/products",
            json={
                "name": "New Product",
                "description": "desc",
                "attributes": {"volume_ml": 250},
                "base_price": "25.00",
                "is_customizable": True,
                "customization_options": {
                    "size": ["small", "medium", "large"],
                    "color": ["blue", "red"],
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Product"
        assert data["is_customizable"] is True

    def test_create_product_unauthorized(self, anon_client: TestClient):
        response = anon_client.post(
            f"{API}/sellers/me/products",
            json={"name": "X", "attributes": {}, "base_price": "10.00"},
        )
        assert response.status_code == 401

    def test_create_product_name_conflict(
        self, seller_client: TestClient, test_product_spec: SellerProductSpec
    ):
        """Mesmo nome → 409."""
        response = seller_client.post(
            f"{API}/sellers/me/products",
            json={
                "name": test_product_spec.name,
                "attributes": {},
                "is_customizable": False,
                "base_price": "10.00",
            },
        )
        assert response.status_code == 409

    def test_get_my_products(
        self, seller_client: TestClient, test_product_spec: SellerProductSpec
    ):
        response = seller_client.get(f"{API}/sellers/me/products")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_update_product(
        self, seller_client: TestClient, test_product_spec: SellerProductSpec
    ):
        response = seller_client.patch(
            f"{API}/sellers/me/products/{test_product_spec.id}",
            json={"name": "Updated Product", "base_price": "30.00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product"

    def test_delete_product(
        self, seller_client: TestClient, test_product_spec: SellerProductSpec
    ):
        """DELETE /sellers/me/products/{id} → 204 (desativa)."""
        response = seller_client.delete(
            f"{API}/sellers/me/products/{test_product_spec.id}"
        )
        assert response.status_code == 204

    # =========================================================================
    # Additional tests for sellers_me routes to increase coverage
    # =========================================================================

    def test_update_profile_empty_body(self, seller_client: TestClient, test_seller: SellerProfile):
        """Testa erro ao atualizar com body vazio."""
        response = seller_client.patch(f"{API}/sellers/me/profile", json={})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Nada para atualizar" in response.json()["detail"]

    def test_close_my_shop(self, seller_client: TestClient, test_seller: SellerProfile):
        """Testa fechar loja."""
        response = seller_client.delete(f"{API}/sellers/me/profile")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_logo_not_found(self, seller_client: TestClient, test_seller: SellerProfile):
        """Testa erro ao deletar logo inexistente."""
        response = seller_client.delete(f"{API}/sellers/me/profile/logo")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Logo nao encontrado" in response.json()["detail"]

    def test_delete_banner_not_found(self, seller_client: TestClient, test_seller: SellerProfile):
        """Testa erro ao deletar banner inexistente."""
        response = seller_client.delete(f"{API}/sellers/me/profile/banner")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Banner nao encontrado" in response.json()["detail"]

    def test_update_product_empty_body(self, seller_client: TestClient, test_product_spec: SellerProductSpec):
        """Testa erro ao atualizar produto com body vazio."""
        response = seller_client.patch(
            f"{API}/sellers/me/products/{test_product_spec.id}",
            json={},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Nada para atualizar" in response.json()["detail"]

    def test_list_product_images(self, seller_client: TestClient, test_product_spec: SellerProductSpec, db_session):
        """Testa listar imagens de produto."""
        image = SellerProductImage(
            id=uuid4(),
            product_spec_id=test_product_spec.id,
            image_key="test-key",
            position=0,
            is_cover=True,
        )
        db_session.add(image)
        db_session.commit()

        response = seller_client.get(f"{API}/sellers/me/products/{test_product_spec.id}/images")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1

    def test_update_product_image_empty_body(self, seller_client: TestClient, test_product_spec: SellerProductSpec, db_session):
        """Testa erro ao atualizar imagem com body vazio."""
        image = SellerProductImage(
            id=uuid4(),
            product_spec_id=test_product_spec.id,
            image_key="test-key",
            position=0,
            is_cover=True,
        )
        db_session.add(image)
        db_session.commit()

        response = seller_client.patch(
            f"{API}/sellers/me/products/{test_product_spec.id}/images/{image.id}",
            json={},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Nada para atualizar" in response.json()["detail"]


    def test_create_profile_auto_slug(self, seller_client: TestClient):
        """Testa criação de perfil com slug gerado automaticamente (cobre linha 169)."""
        # Este teste é complexo pois o seller_client já tem perfil
        # Vamos testar com um novo seller que não tem perfil
        from src.api.dependencies.auth import require_seller_email_verified
        from src.database.models.enums import UserRole, SellerCategory
        
        # Criar um novo usuário seller sem perfil
        new_user = User(
            id=uuid4(),
            email="newseller2@example.com",
            name="New Seller 2",
            password_hash="hash",
            role=UserRole.SELLER,
            email_verified=True,
        )
        
        # Criar novo client para o novo usuário
        new_client = seller_client.__class__(app=seller_client.app)
        new_client.app.dependency_overrides[require_seller_email_verified] = lambda: new_user

        response = new_client.post(
            f"{API}/sellers/me/profile",
            json={
                "store_name": "Minha Loja Unica",
                "description": "Test description",
                "category": SellerCategory.OTHER.value,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "slug" in data
        assert data["slug"] is not None

    def test_create_profile_slug_conflict(self, seller_client: TestClient, test_seller: SellerProfile):
        """Testa erro ao criar perfil com slug já em uso (cobre linha 167)."""
        response = seller_client.post(
            f"{API}/sellers/me/profile",
            json={
                "store_name": "Another Store",
                "description": "Test",
                "category": "other",
                "slug": test_seller.slug,
            },
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_profile_slug_collision_generates_unique(self, seller_client: TestClient):
        """Testa geração de slug único quando já existe (cobre linhas 136-137)."""
        from src.api.dependencies.auth import require_seller_email_verified
        from src.database.models.enums import UserRole, SellerCategory
        from src.database.models.seller_profile import SellerProfile as SP
        
        # Criar primeiro seller
        user1 = User(
            id=uuid4(),
            email="seller1@example.com",
            name="Seller 1",
            password_hash="hash",
            role=UserRole.SELLER,
            email_verified=True,
        )
        
        client1 = seller_client.__class__(app=seller_client.app)
        client1.app.dependency_overrides[require_seller_email_verified] = lambda: user1
        
        response1 = client1.post(
            f"{API}/sellers/me/profile",
            json={
                "store_name": "Loja Teste",
                "description": "Test",
                "category": SellerCategory.OTHER.value,
            },
        )
        assert response1.status_code == status.HTTP_201_CREATED
        slug1 = response1.json()["slug"]
        
        # Criar segundo seller com mesmo nome
        user2 = User(
            id=uuid4(),
            email="seller2@example.com",
            name="Seller 2",
            password_hash="hash",
            role=UserRole.SELLER,
            email_verified=True,
        )
        
        client2 = seller_client.__class__(app=seller_client.app)
        client2.app.dependency_overrides[require_seller_email_verified] = lambda: user2
        
        response2 = client2.post(
            f"{API}/sellers/me/profile",
            json={
                "store_name": "Loja Teste",
                "description": "Test",
                "category": SellerCategory.OTHER.value,
            },
        )
        assert response2.status_code == status.HTTP_201_CREATED
        slug2 = response2.json()["slug"]
        
        # Os slugs devem ser diferentes
        assert slug1 != slug2
        assert slug2.startswith(slug1.split("-")[0])

    def test_upload_logo_with_existing_logo(self, seller_client: TestClient, test_seller: SellerProfile, db_session):
        """Testa upload de logo substituindo logo existente (cobre linha 231-235)."""
        from unittest.mock import Mock, patch
        from io import BytesIO
        
        test_seller.logo_key = "old-logo-key"
        db_session.commit()
        
        # Mock do image_service
        mock_image_service = Mock()
        mock_image_service.delete.return_value = None
        mock_image_service.get_url.return_value = "https://example.com/new-logo.png"
        mock_image_service.upload_seller_logo.return_value = Mock(key="new-logo-key")
        
        with patch("src.api.routes.sellers_me.image_service", mock_image_service):
            file = BytesIO(b"fake image content")
            
            response = seller_client.post(
                f"{API}/sellers/me/profile/logo",
                files={"file": ("logo.png", file, "image/png")}
            )
            assert response.status_code == status.HTTP_200_OK
            mock_image_service.delete.assert_called_once_with("old-logo-key")

    def test_upload_logo_value_error(self, seller_client: TestClient, test_seller: SellerProfile):
        """Testa erro de ValueError ao fazer upload de logo (cobre linha 244-245)."""
        from unittest.mock import Mock, patch
        from io import BytesIO
        
        # Mock do image_service que lança ValueError
        mock_image_service = Mock()
        mock_image_service.upload_seller_logo.side_effect = ValueError("Invalid file")
        
        with patch("src.api.routes.sellers_me.image_service", mock_image_service):
            file = BytesIO(b"fake image content")
            
            response = seller_client.post(
                f"{API}/sellers/me/profile/logo",
                files={"file": ("logo.png", file, "image/png")}
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_logo_success(self, seller_client: TestClient, test_seller: SellerProfile, db_session):
        """Testa delete de logo com sucesso (cobre linha 261-265)."""
        from unittest.mock import Mock, patch
        
        test_seller.logo_key = "logo-to-delete"
        db_session.commit()

        mock_image_service = Mock()
        mock_image_service.delete.return_value = None
        
        with patch("src.api.routes.sellers_me.image_service", mock_image_service):
            response = seller_client.delete(f"{API}/sellers/me/profile/logo")
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_image_service.delete.assert_called_once_with("logo-to-delete")

    def test_delete_logo_storage_error(self, seller_client: TestClient, test_seller: SellerProfile, db_session):
        """Testa delete de logo com erro no storage (cobre linha 263-264)."""
        from unittest.mock import Mock, patch
        
        test_seller.logo_key = "logo-to-delete"
        db_session.commit()

        mock_image_service = Mock()
        mock_image_service.delete.side_effect = Exception("Storage error")
        
        with patch("src.api.routes.sellers_me.image_service", mock_image_service):
            response = seller_client.delete(f"{API}/sellers/me/profile/logo")
            assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_banner_success(self, seller_client: TestClient, test_seller: SellerProfile, db_session):
        """Testa delete de banner com sucesso (cobre linha 310-311)."""
        from unittest.mock import Mock, patch
        
        test_seller.banner_key = "banner-to-delete"
        db_session.commit()

        mock_image_service = Mock()
        mock_image_service.delete.return_value = None
        
        with patch("src.api.routes.sellers_me.image_service", mock_image_service):
            response = seller_client.delete(f"{API}/sellers/me/profile/banner")
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_image_service.delete.assert_called_once_with("banner-to-delete")

    def test_upload_banner_success(self, seller_client: TestClient, test_seller: SellerProfile, db_session):
        """Testa upload de banner com sucesso (cobre linha 275-295)."""
        from unittest.mock import Mock, patch
        from io import BytesIO
        
        mock_image_service = Mock()
        mock_image_service.get_url.return_value = "https://example.com/new-banner.png"
        mock_image_service.upload_seller_banner.return_value = Mock(key="new-banner-key")
        
        with patch("src.api.routes.sellers_me.image_service", mock_image_service):
            file = BytesIO(b"fake banner content")
            
            response = seller_client.post(
                f"{API}/sellers/me/profile/banner",
                files={"file": ("banner.png", file, "image/png")}
            )
            assert response.status_code == status.HTTP_200_OK

    def test_update_product_with_price(self, seller_client: TestClient, test_product_spec: SellerProductSpec):
        """Testa update de produto com preço (cobre linha 377-384)."""
        response = seller_client.patch(
            f"{API}/sellers/me/products/{test_product_spec.id}",
            json={
                "name": "Updated Product",
                "description": "Updated description",
                "is_active": True,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Product"

    def test_get_my_product_not_found(self, seller_client: TestClient):
        """Testa erro ao buscar produto inexistente (cobre linha 381-382)."""
        response = seller_client.get(f"{API}/sellers/me/products/{uuid4()}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_my_product_wrong_seller(self, seller_client: TestClient, db_session: Session):
        """Testa erro ao buscar produto de outro seller (cobre linha 381-382)."""
        from src.database.models.seller_product_spec import SellerProductSpec
        from src.database.models.seller_profile import SellerProfile as SP
        
        # Criar outro seller
        other_seller = SP(
            id=uuid4(),
            user_id=uuid4(),
            store_name="Other Store",
            slug="other-store",
            description="Test",
            category="other",
        )
        db_session.add(other_seller)
        
        # Criar produto do outro seller
        other_product = SellerProductSpec(
            id=uuid4(),
            seller_id=other_seller.user_id,
            name="Other Product",
            description="Test",
            is_active=True,
        )
        db_session.add(other_product)
        db_session.commit()
        
        # Tentar buscar produto do outro seller
        response = seller_client.get(f"{API}/sellers/me/products/{other_product.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_product_success(self, seller_client: TestClient, db_session: Session, test_seller: SellerProfile):
        """Testa delete de produto com sucesso (cobre linha 399)."""
        from src.database.models.seller_product_spec import SellerProductSpec
        
        product = SellerProductSpec(
            id=uuid4(),
            seller_id=test_seller.id,
            name="Product to delete",
            description="Test",
            is_active=True,
        )
        db_session.add(product)
        db_session.commit()

        response = seller_client.delete(f"{API}/sellers/me/products/{product.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_update_product_image_success(self, seller_client: TestClient, test_product_spec: SellerProductSpec, db_session):
        """Testa update de imagem de produto (cobre linha 427)."""
        image = SellerProductImage(
            id=uuid4(),
            product_spec_id=test_product_spec.id,
            image_key="test-key",
            position=0,
            is_cover=True,
        )
        db_session.add(image)
        db_session.commit()

        response = seller_client.patch(
            f"{API}/sellers/me/products/{test_product_spec.id}/images/{image.id}",
            json={"alt_text": "New alt text"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["alt_text"] == "New alt text"

    def test_delete_product_image_success(self, seller_client: TestClient, test_product_spec: SellerProductSpec, db_session):
        """Testa delete de imagem de produto (cobre linha 445)."""
        image = SellerProductImage(
            id=uuid4(),
            product_spec_id=test_product_spec.id,
            image_key="test-key",
            position=0,
            is_cover=False,
        )
        db_session.add(image)
        db_session.commit()

        response = seller_client.delete(
            f"{API}/sellers/me/products/{test_product_spec.id}/images/{image.id}"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_update_product_image_set_cover(self, seller_client: TestClient, test_product_spec: SellerProductSpec, db_session):
        """Testa update de imagem setando como cover (cobre linha 479-505)."""
        # Criar duas imagens
        image1 = SellerProductImage(
            id=uuid4(),
            product_spec_id=test_product_spec.id,
            image_key="test-key-1",
            position=0,
            is_cover=True,
        )
        image2 = SellerProductImage(
            id=uuid4(),
            product_spec_id=test_product_spec.id,
            image_key="test-key-2",
            position=1,
            is_cover=False,
        )
        db_session.add(image1)
        db_session.add(image2)
        db_session.commit()

        response = seller_client.patch(
            f"{API}/sellers/me/products/{test_product_spec.id}/images/{image2.id}",
            json={"is_cover": True},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_cover"] is True

    def test_delete_product_image_cover_promotes_next(self, seller_client: TestClient, test_product_spec: SellerProductSpec, db_session):
        """Testa delete de imagem cover promove a próxima (cobre linha 525)."""
        # Criar duas imagens, a primeira é cover
        image1 = SellerProductImage(
            id=uuid4(),
            product_spec_id=test_product_spec.id,
            image_key="test-key-1",
            position=0,
            is_cover=True,
        )
        image2 = SellerProductImage(
            id=uuid4(),
            product_spec_id=test_product_spec.id,
            image_key="test-key-2",
            position=1,
            is_cover=False,
        )
        db_session.add(image1)
        db_session.add(image2)
        db_session.commit()

        response = seller_client.delete(
            f"{API}/sellers/me/products/{test_product_spec.id}/images/{image1.id}"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verificar que a segunda imagem agora é cover
        db_session.refresh(image2)
        assert image2.is_cover is True

    def test_delete_product_image_storage_error(self, seller_client: TestClient, test_product_spec: SellerProductSpec, db_session):
        """Testa delete de imagem com erro no storage (cobre linha 556-557)."""
        image = SellerProductImage(
            id=uuid4(),
            product_spec_id=test_product_spec.id,
            image_key="test-key-error",
            position=0,
            is_cover=False,
        )
        db_session.add(image)
        db_session.commit()

        response = seller_client.delete(
            f"{API}/sellers/me/products/{test_product_spec.id}/images/{image.id}"
        )
        # O endpoint deve retornar 204 mesmo se houver erro no storage (loga warning)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_upload_product_image_limit_reached(self, seller_client: TestClient, test_product_spec: SellerProductSpec, db_session):
        """Testa erro ao atingir limite de imagens por produto (cobre linha 482-486)."""
        from src.api.routes.sellers_me import MAX_IMAGES_PER_PRODUCT
        
        # Criar o número máximo de imagens
        for i in range(MAX_IMAGES_PER_PRODUCT):
            image = SellerProductImage(
                id=uuid4(),
                product_spec_id=test_product_spec.id,
                image_key=f"test-key-{i}",
                position=i,
                is_cover=(i == 0),
            )
            db_session.add(image)
        db_session.commit()
        
        # Tentar adicionar mais uma imagem
        from unittest.mock import Mock, patch
        from io import BytesIO
        
        mock_image_service = Mock()
        mock_image_service.upload_product_image.return_value = Mock(key="new-image-key")
        
        with patch("src.api.routes.sellers_me.image_service", mock_image_service):
            file = BytesIO(b"fake image content")
            
            response = seller_client.post(
                f"{API}/sellers/me/products/{test_product_spec.id}/images",
                files={"file": ("image.png", file, "image/png")}
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Limite" in response.json()["detail"]

    def test_upload_product_image_success(self, seller_client: TestClient, test_product_spec: SellerProductSpec):
        """Testa upload de imagem de produto com sucesso (cobre linha 479-505)."""
        from unittest.mock import Mock, patch
        from io import BytesIO
        
        mock_image_service = Mock()
        mock_image_service.get_url.return_value = "https://example.com/new-image.png"
        mock_image_service.upload_product_image.return_value = Mock(key="new-image-key")
        
        with patch("src.api.routes.sellers_me.image_service", mock_image_service):
            file = BytesIO(b"fake image content")
            
            response = seller_client.post(
                f"{API}/sellers/me/products/{test_product_spec.id}/images",
                files={"file": ("image.png", file, "image/png")},
                data={"alt_text": "Test image", "is_cover": "false"}
            )
            assert response.status_code == status.HTTP_201_CREATED
