import pytest
from uuid import uuid4
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.database.models.user import User
from src.database.models.seller_profile import SellerProfile
from src.database.models.order import Order
from src.database.models.project_iteration import ProjectIteration
from src.database.models.enums import OrderStatus, IterationStatus, UserRole

API = "/api/v1"


def _make_approved_iteration(db_session: Session, order: Order) -> ProjectIteration:
    """Helper: cria uma iteration READY para poder aprovar."""
    from uuid import uuid4 as _uuid
    it = ProjectIteration(
        id=_uuid(),
        order_id=order.id,
        version=1,
        description="desc",
        prompt="prompt",
        image_key="key",
        status=IterationStatus.READY,
    )
    db_session.add(it)
    db_session.commit()
    db_session.refresh(it)
    return it


class TestOrdersRoutes:
    """Testes para rotas de Orders (prefixo /api/v1/orders)."""

    def test_create_order(self, client: TestClient, test_seller_user: User):
        """POST /orders/ cria pedido DRAFT."""
        response = client.post(
            f"{API}/orders/",
            json={
                "seller_id": str(test_seller_user.id),
                "title": "Test Order",
                "description": "Test description",
                "product_type": "customized",
                "product_options": {"size": "medium", "color": "blue"},
                "quantity": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Order"
        assert data["status"] == OrderStatus.DRAFT.value

    def test_create_order_unauthorized(self, anon_client: TestClient, test_seller_user: User):
        response = anon_client.post(
            f"{API}/orders/",
            json={
                "seller_id": str(test_seller_user.id),
                "title": "T",
                "description": "Descrição válida",
                "product_type": "customized",
                "quantity": 1,
            },
        )
        assert response.status_code == 401

    def test_create_order_seller_not_found(self, client: TestClient):
        """Seller inexistente retorna 404."""
        response = client.post(
            f"{API}/orders/",
            json={
                "seller_id": str(uuid4()),
                "title": "Test Order",
                "description": "Descrição válida",
                "product_type": "customized",
                "quantity": 1,
            },
        )
        assert response.status_code == 404

    def test_get_order_by_id(self, client: TestClient, test_order: Order):
        response = client.get(f"{API}/orders/{test_order.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_order.id)
        assert data["title"] == "Test Order"

    def test_get_order_by_id_not_found(self, client: TestClient):
        response = client.get(f"{API}/orders/{uuid4()}")
        assert response.status_code == 404

    def test_list_my_orders(self, client: TestClient, test_order: Order):
        """GET /orders/me lista pedidos do cliente logado."""
        response = client.get(f"{API}/orders/me")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_update_order_requires_draft(self, client: TestClient, test_order: Order):
        """PATCH /orders/{id} só permitido em DRAFT; test_order está em IN_ANALYSIS → 409."""
        response = client.patch(
            f"{API}/orders/{test_order.id}",
            json={"title": "Updated Order", "description": "Updated descripcao"},
        )
        assert response.status_code == 409

    def test_update_draft_order(
        self, client: TestClient, db_session: Session, test_user: User, test_seller_user: User
    ):
        """Cria pedido (fica em DRAFT) e edita."""
        resp = client.post(
            f"{API}/orders/",
            json={
                "seller_id": str(test_seller_user.id),
                "title": "Original",
                "description": "Original desc",
                "product_type": "customized",
                "quantity": 1,
            },
        )
        assert resp.status_code == 201
        order_id = resp.json()["id"]

        resp = client.patch(
            f"{API}/orders/{order_id}",
            json={"title": "Renamed", "description": "Nova desc"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Renamed"

    def test_cancel_order(self, client: TestClient, test_order: Order):
        """POST /orders/{id}/cancel funciona em IN_ANALYSIS."""
        response = client.post(
            f"{API}/orders/{test_order.id}/cancel",
            json={"note": "Customer requested"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == OrderStatus.CANCELLED.value

    def test_seller_decision_accept(self, seller_client: TestClient, test_order: Order):
        """POST /orders/{id}/seller-decision aprova pedido."""
        response = seller_client.post(
            f"{API}/orders/{test_order.id}/seller-decision",
            json={"accept": True, "estimated_price": "60.00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == OrderStatus.APPROVED.value

    def test_seller_decision_reject(self, seller_client: TestClient, test_order: Order):
        response = seller_client.post(
            f"{API}/orders/{test_order.id}/seller-decision",
            json={"accept": False, "note": "não apropriado"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.CANCELLED.value

    def test_seller_decision_wrong_seller(self, client: TestClient, test_order: Order):
        """Cliente (não-seller) não pode usar seller-decision → 403."""
        # client está autenticado como test_user (CLIENT); nem chega a validar status pois
        # require_seller_email_verified é overridden p/ retornar test_user, mas handler checa seller_id
        response = client.post(
            f"{API}/orders/{test_order.id}/seller-decision",
            json={"accept": True},
        )
        assert response.status_code == 403

    def test_update_status_invalid_transition(self, seller_client: TestClient, test_order: Order):
        """IN_ANALYSIS não pode ir direto para SENT via PATCH /status."""
        response = seller_client.patch(
            f"{API}/orders/{test_order.id}/status",
            json={"status": OrderStatus.SENT.value},
        )
        assert response.status_code == 409

    def test_update_status_valid_transition(
        self, seller_client: TestClient, db_session: Session, test_order: Order
    ):
        """APPROVED -> PAID é válido."""
        # Move order para APPROVED primeiro
        test_order.status = OrderStatus.APPROVED
        db_session.commit()

        response = seller_client.patch(
            f"{API}/orders/{test_order.id}/status",
            json={"status": OrderStatus.PAID.value},
        )
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.PAID.value

    def test_update_status_payload_invalid(self, seller_client: TestClient, test_order: Order):
        response = seller_client.patch(
            f"{API}/orders/{test_order.id}/status",
            json={"status": "totalmente_invalido"},
        )
        assert response.status_code == 422

    def test_confirm_delivery(self, client: TestClient, db_session: Session, test_order: Order):
        """SENT → DELIVERED pelo cliente."""
        test_order.status = OrderStatus.SENT
        db_session.commit()

        response = client.patch(f"{API}/orders/{test_order.id}/confirm-delivery")
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.DELIVERED.value

    def test_confirm_delivery_invalid_status(self, client: TestClient, test_order: Order):
        """test_order em IN_ANALYSIS → 409."""
        response = client.patch(f"{API}/orders/{test_order.id}/confirm-delivery")
        assert response.status_code == 409

    def test_complete_order(self, client: TestClient, db_session: Session, test_order: Order):
        """DELIVERED → COMPLETED."""
        test_order.status = OrderStatus.DELIVERED
        db_session.commit()

        response = client.patch(f"{API}/orders/{test_order.id}/complete")
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.COMPLETED.value

    def test_list_iterations(self, client: TestClient, test_order: Order, test_iteration: ProjectIteration):
        """GET /orders/{id}/iterations retorna lista."""
        response = client.get(f"{API}/orders/{test_order.id}/iterations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["version"] == 1

    def test_approve_iteration(
        self, client: TestClient, db_session: Session, test_user: User, test_seller_user: User
    ):
        """Cliente aprova iteration READY em pedido DRAFT."""
        # Cria pedido DRAFT
        from uuid import uuid4 as _uuid
        order = Order(
            id=_uuid(),
            client_id=test_user.id,
            seller_id=test_seller_user.id,
            title="Draft Order",
            description="desc",
            product_type="customized",
            quantity=1,
            status=OrderStatus.DRAFT,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        iteration = _make_approved_iteration(db_session, order)

        response = client.post(
            f"{API}/orders/{order.id}/approve-iteration/{iteration.id}",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["approved_iteration_id"] == str(iteration.id)

    def test_get_order_with_approved_iteration(self, client: TestClient, db_session: Session, test_user: User, test_seller_user: User):
        """Testa buscar pedido com iteração aprovada (cobre linha 99)."""
        from uuid import uuid4 as _uuid
        order = Order(
            id=_uuid(),
            client_id=test_user.id,
            seller_id=test_seller_user.id,
            title="Test Order",
            description="desc",
            product_type="customized",
            quantity=1,
            status=OrderStatus.APPROVED,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        iteration = ProjectIteration(
            id=_uuid(),
            order_id=order.id,
            version=1,
            status=IterationStatus.APPROVED,
            image_key="iteration-key",
            description="Test iteration",
            prompt="Test prompt",
        )
        db_session.add(iteration)
        
        # Associar a iteração ao order como approved_iteration
        order.approved_iteration_id = iteration.id
        db_session.commit()

        response = client.get(f"{API}/orders/{order.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["approved_iteration"] is not None
        assert data["approved_iteration"]["version"] == 1

    def test_get_order_as_admin(self, client_factory, db_session: Session, test_order: Order):
        """Testa que admin pode acessar qualquer pedido (cobre linha 126)."""
        admin_user = User(
            id=uuid4(),
            email="admin@example.com",
            name="Admin",
            password_hash="hash",
            role=UserRole.ADMIN,
            email_verified=True,
        )
        db_session.add(admin_user)
        db_session.commit()

        admin_client = client_factory(admin_user)
        response = admin_client.get(f"{API}/orders/{test_order.id}")
        assert response.status_code == 200

    def test_get_order_as_seller(self, seller_client: TestClient, test_order: Order):
        """Testa que seller pode acessar pedido (cobre linha 129-130)."""
        # test_order já tem seller_id definido no fixture
        response = seller_client.get(f"{API}/orders/{test_order.id}")
        assert response.status_code == 200

    def test_get_order_forbidden(self, client: TestClient, db_session: Session, test_order: Order):
        """Testa que usuário sem acesso não pode ver pedido (cobre linha 132)."""
        other_user = User(
            id=uuid4(),
            email="other@example.com",
            name="Other",
            password_hash="hash",
            role=UserRole.CLIENT,
            email_verified=True,
        )
        db_session.add(other_user)
        db_session.commit()

        from src.api.dependencies.auth import get_current_active_user
        other_client = client.__class__(app=client.app)
        other_client.app.dependency_overrides[get_current_active_user] = lambda: other_user

        response = other_client.get(f"{API}/orders/{test_order.id}")
        assert response.status_code == 403

    def test_update_order_wrong_user(self, seller_client: TestClient, db_session: Session, test_order: Order):
        """Testa erro ao editar pedido de outro usuário (cobre linha 227)."""
        # seller_client é seller, mas test_order é de outro cliente
        test_order.status = OrderStatus.DRAFT
        db_session.commit()

        response = seller_client.patch(
            f"{API}/orders/{test_order.id}",
            json={"title": "Updated"},
        )
        assert response.status_code == 403

    def test_update_order_empty_body(self, client: TestClient, db_session: Session, test_user: User, test_seller_user: User):
        """Testa erro ao atualizar com body vazio (cobre linha 232)."""
        # Cria pedido DRAFT
        order = Order(
            id=uuid4(),
            client_id=test_user.id,
            seller_id=test_seller_user.id,
            title="Test Order",
            description="desc",
            product_type="customized",
            quantity=1,
            status=OrderStatus.DRAFT,
        )
        db_session.add(order)
        db_session.commit()

        response = client.patch(
            f"{API}/orders/{order.id}",
            json={},
        )
        assert response.status_code == 400

    def test_cancel_order_wrong_user(self, seller_client: TestClient, test_order: Order, db_session: Session):
        """Testa erro ao cancelar pedido de outro usuário (cobre linha 252)."""
        test_order.status = OrderStatus.IN_ANALYSIS
        db_session.commit()
        # seller_client é seller, não cliente do pedido, então deve retornar 403
        response = seller_client.post(
            f"{API}/orders/{test_order.id}/cancel",
            json={"note": "Cancel"},
        )
        assert response.status_code == 403

    def test_request_iteration_wrong_user(self, seller_client: TestClient, test_order: Order):
        """Testa erro ao solicitar iteração como seller (cobre linha 294-295)."""
        test_order.status = OrderStatus.DRAFT

        response = seller_client.post(
            f"{API}/orders/{test_order.id}/iterations",
            json={"description": "Test description"},
        )
        assert response.status_code == 403

    def test_request_iteration_not_draft(self, client: TestClient, test_order: Order):
        """Testa erro ao solicitar iteração em pedido não DRAFT (cobre linha 296)."""
        # test_order está em IN_ANALYSIS
        response = client.post(
            f"{API}/orders/{test_order.id}/iterations",
            json={"description": "Test description"},
        )
        assert response.status_code == 409

    def test_approve_iteration_wrong_status(self, client: TestClient, test_order: Order, test_iteration: ProjectIteration):
        """Testa erro ao aprovar iteração em pedido não DRAFT."""
        test_order.status = OrderStatus.IN_ANALYSIS
        db_session = None

        response = client.post(
            f"{API}/orders/{test_order.id}/approve-iteration/{test_iteration.id}",
        )
        assert response.status_code == 409

    def test_approve_iteration_wrong_user(self, seller_client: TestClient, test_order: Order, test_iteration: ProjectIteration):
        """Testa erro ao aprovar iteração como seller."""
        test_order.status = OrderStatus.DRAFT

        response = seller_client.post(
            f"{API}/orders/{test_order.id}/approve-iteration/{test_iteration.id}",
        )
        assert response.status_code == 403

    def test_get_iteration_not_found(self, client: TestClient, test_order: Order):
        """Testa erro ao buscar iteração inexistente (cobre linha 408-409)."""
        response = client.get(f"{API}/orders/{test_order.id}/iterations/{uuid4()}")
        assert response.status_code == 404

    def test_get_iteration_wrong_order(self, client: TestClient, test_order: Order, test_iteration: ProjectIteration, db_session: Session):
        """Testa erro ao buscar iteração de outro pedido (cobre linha 408-409)."""
        other_order = Order(
            id=uuid4(),
            client_id=test_order.client_id,
            seller_id=test_order.seller_id,
            title="Other Order",
            description="desc",
            product_type="customized",
            quantity=1,
            status=OrderStatus.DRAFT,
        )
        db_session.add(other_order)
        db_session.commit()

        response = client.get(f"{API}/orders/{other_order.id}/iterations/{test_iteration.id}")
        assert response.status_code == 404

    def test_approve_iteration_not_ready(self, client: TestClient, test_order: Order, db_session: Session):
        """Testa erro ao aprovar iteração não pronta (cobre linha 433-437)."""
        from src.database.models.enums import IterationStatus
        
        test_order.status = OrderStatus.DRAFT
        
        iteration = ProjectIteration(
            id=uuid4(),
            order_id=test_order.id,
            version=1,
            description="Test",
            status=IterationStatus.GENERATING,
        )
        db_session.add(iteration)
        db_session.commit()

        response = client.post(
            f"{API}/orders/{test_order.id}/approve-iteration/{iteration.id}",
        )
        assert response.status_code == 400

    def test_list_my_orders_with_approved_iteration_image(self, client: TestClient, test_order: Order, test_iteration: ProjectIteration, db_session: Session):
        """Testa listagem de pedidos com iteração aprovada e imagem (cobre linha 99)."""
        from src.database.models.enums import IterationStatus
        
        test_order.approved_iteration_id = test_iteration.id
        test_iteration.image_key = "test-image-key"
        test_iteration.status = IterationStatus.APPROVED
        db_session.commit()

        response = client.get(f"{API}/orders/me")
        assert response.status_code == 200
        orders = response.json()["items"]
        assert len(orders) > 0

    def test_get_iteration_success(self, client: TestClient, test_order: Order, test_iteration: ProjectIteration):
        """Testa busca de iteração com sucesso (cobre linha 410)."""
        response = client.get(f"{API}/orders/{test_order.id}/iterations/{test_iteration.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_iteration.id)

    def test_approve_iteration_not_found(self, client: TestClient, test_order: Order):
        """Testa erro ao aprovar iteração não encontrada (cobre linha 432)."""
        test_order.status = OrderStatus.DRAFT

        response = client.post(
            f"{API}/orders/{test_order.id}/approve-iteration/{uuid4()}",
        )
        assert response.status_code == 404

    def test_submit_order_success(self, client: TestClient, test_order: Order, test_iteration: ProjectIteration, db_session: Session):
        """Testa submissão de pedido com sucesso (cobre linhas 468-474)."""
        test_order.status = OrderStatus.DRAFT
        test_order.approved_iteration_id = test_iteration.id
        test_iteration.status = IterationStatus.APPROVED
        db_session.commit()

        response = client.post(f"{API}/orders/{test_order.id}/submit")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_analysis"

    def test_complete_order_wrong_status(self, client: TestClient, test_order: Order):
        """Testa erro ao completar pedido com status errado (cobre linha 613)."""
        test_order.status = OrderStatus.IN_ANALYSIS

        response = client.patch(f"{API}/orders/{test_order.id}/complete")
        assert response.status_code == 409

    def test_create_iteration_with_ai(self, client: TestClient, test_order: Order):
        """Testa criação de iteração com IA (cobre linhas 298-394)."""
        from unittest.mock import Mock, patch
        from io import BytesIO
        
        test_order.status = OrderStatus.DRAFT
        
        # Mock do AI client
        mock_ai_result = Mock()
        mock_ai_result.image_bytes = b"fake image"
        mock_ai_result.content_type = "image/png"
        mock_ai_result.prompt = "Test prompt"
        mock_ai_result.model = "test-model"
        
        mock_ai_client = Mock()
        mock_ai_client.generate_iteration_image.return_value = mock_ai_result
        
        # Mock do image_service
        mock_stored = Mock()
        mock_stored.key = "test-image-key"
        
        mock_image_service = Mock()
        mock_image_service.upload_ai_generated.return_value = mock_stored
        mock_image_service.get_url.return_value = "https://example.com/image.png"
        
        with patch("src.api.routes.orders.ai_client", mock_ai_client), \
             patch("src.api.routes.orders.image_service", mock_image_service):
            response = client.post(
                f"{API}/orders/{test_order.id}/iterations",
                json={"description": "Test description"},
            )
            assert response.status_code == 201
            mock_ai_client.generate_iteration_image.assert_called_once()
            mock_image_service.upload_ai_generated.assert_called_once()

    def test_submit_order_wrong_user(self, seller_client: TestClient, test_order: Order):
        """Testa erro ao submeter pedido como seller (cobre linha 458-459)."""
        test_order.status = OrderStatus.DRAFT

        response = seller_client.post(f"{API}/orders/{test_order.id}/submit")
        assert response.status_code == 403

    def test_submit_order_not_draft(self, client: TestClient, test_order: Order):
        """Testa erro ao submeter pedido não DRAFT (cobre linha 460)."""
        # test_order está em IN_ANALYSIS
        response = client.post(f"{API}/orders/{test_order.id}/submit")
        assert response.status_code == 409

    def test_submit_order_no_approved_iteration(self, client: TestClient, db_session: Session, test_user: User, test_seller_user: User):
        """Testa erro ao submeter pedido sem iteração aprovada (cobre linha 462-466)."""
        order = Order(
            id=uuid4(),
            client_id=test_user.id,
            seller_id=test_seller_user.id,
            title="Test Order",
            description="desc",
            product_type="customized",
            quantity=1,
            status=OrderStatus.DRAFT,
        )
        db_session.add(order)
        db_session.commit()

        response = client.post(f"{API}/orders/{order.id}/submit")
        assert response.status_code == 400

    def test_list_seller_orders(self, seller_client: TestClient, test_order: Order):
        """Testa listar pedidos do seller (cobre linha 493-496)."""
        response = seller_client.get(f"{API}/sellers/me/orders")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_seller_decision_not_found(self, seller_client: TestClient):
        """Testa erro ao decidir sobre pedido inexistente (cobre linha 514-515)."""
        response = seller_client.post(
            f"{API}/orders/{uuid4()}/seller-decision",
            json={"accept": True, "estimated_price": "100.00"},
        )
        assert response.status_code == 404

    def test_seller_decision_wrong_seller(self, client: TestClient, test_order: Order):
        """Testa erro ao decidir sobre pedido de outro seller (cobre linha 516-517)."""
        test_order.status = OrderStatus.IN_ANALYSIS

        response = client.post(
            f"{API}/orders/{test_order.id}/seller-decision",
            json={"accept": True, "estimated_price": "100.00"},
        )
        assert response.status_code == 403

    def test_update_status_not_found(self, seller_client: TestClient):
        """Testa erro ao atualizar status de pedido inexistente (cobre linha 546-547)."""
        response = seller_client.patch(
            f"{API}/orders/{uuid4()}/status",
            json={"status": OrderStatus.PAID.value},
        )
        assert response.status_code == 404

    def test_update_status_wrong_seller(self, client: TestClient, test_order: Order):
        """Testa erro ao atualizar status como não-seller (cobre linha 548-549)."""
        response = client.patch(
            f"{API}/orders/{test_order.id}/status",
            json={"status": OrderStatus.PAID.value},
        )
        assert response.status_code == 403

    def test_confirm_delivery_not_found(self, client: TestClient):
        """Testa erro ao confirmar entrega de pedido inexistente (cobre linha 580-581)."""
        response = client.patch(f"{API}/orders/{uuid4()}/confirm-delivery")
        assert response.status_code == 404

    def test_confirm_delivery_wrong_user(self, seller_client: TestClient, test_order: Order, db_session: Session):
        """Testa erro ao confirmar entrega como seller (cobre linha 582-583)."""
        test_order.status = OrderStatus.SENT
        db_session.commit()

        response = seller_client.patch(f"{API}/orders/{test_order.id}/confirm-delivery")
        assert response.status_code == 403

    def test_complete_order_not_found(self, client: TestClient):
        """Testa erro ao completar pedido inexistente (cobre linha 607-608)."""
        response = client.patch(f"{API}/orders/{uuid4()}/complete")
        assert response.status_code == 404

    def test_complete_order_wrong_user(self, seller_client: TestClient, test_order: Order, db_session: Session):
        """Testa erro ao completar pedido como seller (cobre linha 609-610)."""
        test_order.status = OrderStatus.DELIVERED
        db_session.commit()

        response = seller_client.patch(f"{API}/orders/{test_order.id}/complete")
        assert response.status_code == 403
