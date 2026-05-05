"""Testes de integração para o fluxo completo de pedidos."""
import pytest
from uuid import uuid4
from unittest.mock import Mock, patch
from io import BytesIO

from src.database.models.enums import OrderStatus, IterationStatus, UserRole
from src.database.models.user import User
from src.database.models.seller_profile import SellerProfile
from src.database.models.order import Order


class TestOrderFlowIntegration:
    """Testa o fluxo completo de um pedido desde a criação até a conclusão."""

    def test_complete_order_flow(
        self, 
        client_factory, 
        db_session,
        test_seller_user: User,
        test_seller: SellerProfile
    ):
        """Testa o fluxo completo: criação -> aprovação -> submissão -> entrega -> conclusão."""
        # Criar cliente
        client_user = User(
            id=uuid4(),
            email="client@example.com",
            email_verified=True,
            name="Client User",
            password_hash="hashed_password",
            role=UserRole.CLIENT,
        )
        db_session.add(client_user)
        db_session.commit()

        # Criar clientes autenticados
        client = client_factory(client_user)
        seller_client = client_factory(test_seller_user)

        # 1. Cliente cria um pedido (DRAFT)
        response = client.post(
            "/api/v1/orders/",
            json={
                "seller_id": str(test_seller_user.id),  # ID do usuário seller, não do perfil
                "title": "Caneca Personalizada",
                "description": "Caneca com foto do cachorro",
                "product_type": "mug",
                "quantity": 1,
            },
        )
        assert response.status_code == 201
        order_data = response.json()
        order_id = order_data["id"]
        assert order_data["status"] == "draft"

        # 2. Cliente atualiza o pedido
        response = client.patch(
            f"/api/v1/orders/{order_id}",
            json={
                "title": "Caneca Personalizada Atualizada",
                "description": "Caneca com foto do cachorro e nome",
            },
        )
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["title"] == "Caneca Personalizada Atualizada"

        # 3. Mock do AI client para criar iteração
        mock_ai_result = Mock()
        mock_ai_result.image_bytes = b"fake image"
        mock_ai_result.content_type = "image/png"
        mock_ai_result.prompt = "Test prompt"
        mock_ai_result.model = "test-model"

        mock_ai_client = Mock()
        mock_ai_client.generate_iteration_image.return_value = mock_ai_result

        mock_stored = Mock()
        mock_stored.key = "test-image-key"

        mock_image_service = Mock()
        mock_image_service.upload_ai_generated.return_value = mock_stored
        mock_image_service.get_url.return_value = "https://example.com/image.png"

        # 4. Cliente cria iteração com IA
        with patch("src.api.routes.orders.ai_client", mock_ai_client), \
             patch("src.api.routes.orders.image_service", mock_image_service):
            response = client.post(
                f"/api/v1/orders/{order_id}/iterations",
                json={"description": "Caneca azul com foto do cachorro"},
            )
            assert response.status_code == 201
            iteration_data = response.json()
            iteration_id = iteration_data["id"]
            assert iteration_data["status"] == "ready"

        # 5. Cliente aprova a iteração
        response = client.post(
            f"/api/v1/orders/{order_id}/approve-iteration/{iteration_id}",
        )
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["approved_iteration_id"] == iteration_id

        # 6. Cliente submete o pedido para análise
        response = client.post(f"/api/v1/orders/{order_id}/submit")
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["status"] == "in_analysis"

        # 7. Seller aprova o pedido
        response = seller_client.post(
            f"/api/v1/orders/{order_id}/seller-decision",
            json={"accept": True, "estimated_price": "50.00"},
        )
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["status"] == "approved"
        assert order_data["estimated_price"] == "50.00"

        # 8. Seller marca como pago
        response = seller_client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "paid"},
        )
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["status"] == "paid"

        # 9. Seller marca como em produção
        response = seller_client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "in_production"},
        )
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["status"] == "in_production"

        # 10. Seller marca como enviado
        response = seller_client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "sent"},
        )
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["status"] == "sent"

        # 11. Cliente confirma entrega
        response = client.patch(f"/api/v1/orders/{order_id}/confirm-delivery")
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["status"] == "delivered"

        # 12. Cliente marca como concluído
        response = client.patch(f"/api/v1/orders/{order_id}/complete")
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["status"] == "completed"

        # 12. Verificar que o pedido está concluído
        response = client.get(f"/api/v1/orders/{order_id}")
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["status"] == "completed"
        assert order_data["completed_at"] is not None


    def test_order_flow_with_rejection(
        self, 
        client_factory, 
        db_session,
        test_seller_user: User,
        test_seller: SellerProfile
    ):
        """Testa o fluxo com rejeição de iteração."""
        # Criar cliente
        client_user = User(
            id=uuid4(),
            email="client2@example.com",
            email_verified=True,
            name="Client User 2",
            password_hash="hashed_password",
            role=UserRole.CLIENT,
        )
        db_session.add(client_user)
        db_session.commit()

        # Criar clientes autenticados
        client = client_factory(client_user)

        # 1. Cliente cria um pedido
        response = client.post(
            "/api/v1/orders/",
            json={
                "seller_id": str(test_seller_user.id),  # ID do usuário seller, não do perfil
                "title": "Camiseta Personalizada",
                "description": "Camiseta com logo",
                "product_type": "shirt",
                "quantity": 2,
            },
        )
        assert response.status_code == 201
        order_data = response.json()
        order_id = order_data["id"]

        # 2. Mock do AI client para criar iteração
        mock_ai_result = Mock()
        mock_ai_result.image_bytes = b"fake image"
        mock_ai_result.content_type = "image/png"
        mock_ai_result.prompt = "Test prompt"
        mock_ai_result.model = "test-model"

        mock_ai_client = Mock()
        mock_ai_client.generate_iteration_image.return_value = mock_ai_result

        mock_stored = Mock()
        mock_stored.key = "test-image-key"

        mock_image_service = Mock()
        mock_image_service.upload_ai_generated.return_value = mock_stored
        mock_image_service.get_url.return_value = "https://example.com/image.png"

        # 3. Cliente cria primeira iteração
        with patch("src.api.routes.orders.ai_client", mock_ai_client), \
             patch("src.api.routes.orders.image_service", mock_image_service):
            response = client.post(
                f"/api/v1/orders/{order_id}/iterations",
                json={"description": "Camiseta vermelha com logo"},
            )
            assert response.status_code == 201
            iteration_data = response.json()
            iteration_id_1 = iteration_data["id"]

        # 4. Cliente cria segunda iteração (refinamento)
        with patch("src.api.routes.orders.ai_client", mock_ai_client), \
             patch("src.api.routes.orders.image_service", mock_image_service):
            response = client.post(
                f"/api/v1/orders/{order_id}/iterations",
                json={"description": "Camiseta azul com logo maior"},
            )
            assert response.status_code == 201
            iteration_data = response.json()
            iteration_id_2 = iteration_data["id"]

        # 5. Cliente aprova a segunda iteração
        response = client.post(
            f"/api/v1/orders/{order_id}/approve-iteration/{iteration_id_2}",
        )
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["approved_iteration_id"] == iteration_id_2

        # 6. Verificar que a primeira iteração não está aprovada
        response = client.get(f"/api/v1/orders/{order_id}/iterations/{iteration_id_1}")
        assert response.status_code == 200
        iteration_data = response.json()
        assert iteration_data["status"] != "approved"


    def test_order_flow_cancellation(
        self, 
        client_factory, 
        db_session,
        test_seller_user: User,
        test_seller: SellerProfile
    ):
        """Testa o fluxo com cancelamento do pedido."""
        # Criar cliente
        client_user = User(
            id=uuid4(),
            email="client3@example.com",
            email_verified=True,
            name="Client User 3",
            password_hash="hashed_password",
            role=UserRole.CLIENT,
        )
        db_session.add(client_user)
        db_session.commit()

        # Criar clientes autenticados
        client = client_factory(client_user)
        seller_client = client_factory(test_seller_user)

        # 1. Cliente cria um pedido
        response = client.post(
            "/api/v1/orders/",
            json={
                "seller_id": str(test_seller_user.id),  # ID do usuário seller, não do perfil
                "title": "Boné Personalizado",
                "description": "Boné com nome",
                "product_type": "cap",
                "quantity": 1,
            },
        )
        assert response.status_code == 201
        order_data = response.json()
        order_id = order_data["id"]

        # 2. Cliente cancela o pedido
        response = client.post(
            f"/api/v1/orders/{order_id}/cancel",
            json={"note": "Pedido cancelado"},
        )
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["status"] == "cancelled"

        # 3. Verificar que não é possível criar iteração em pedido cancelado
        mock_ai_client = Mock()
        mock_ai_client.generate_iteration_image.return_value = Mock(
            image_bytes=b"fake image",
            content_type="image/png",
            prompt="Test prompt",
            model="test-model",
        )

        with patch("src.api.routes.orders.ai_client", mock_ai_client):
            response = client.post(
                f"/api/v1/orders/{order_id}/iterations",
                json={"description": "Test iteration"},
            )
            # O endpoint retorna 409 quando o pedido não está em DRAFT
            assert response.status_code == 409
