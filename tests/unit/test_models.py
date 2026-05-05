import pytest
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import ValidationError
from src.api.models.order import (
    OrderCreateRequest,
    OrderUpdateRequest,
    OrderResponse,
    OrderListItem,
    StatusUpdateRequest,
    CancelRequest,
)
from src.api.models.seller import (
    SellerProfileUpdate,
    SellerProfileResponse,
    SellerProfileListItem,
)
from src.api.models.cart import (
    CartCheckoutRequest,
    CartCheckoutResponse,
)
from src.database.models.enums import OrderStatus, SellerCategory


class TestOrderModels:
    """Testes para modelos Pydantic de Order."""

    def test_order_create_request_valid(self):
        """Testa criação de OrderCreateRequest válido."""
        seller_id = uuid4()
        request = OrderCreateRequest(
            seller_id=seller_id,
            title="Test Order",
            description="Test description",
            product_type="customized",
            product_options={"size": "medium", "color": "blue"},
            quantity=1,
        )
        assert request.title == "Test Order"
        assert request.product_type == "customized"
        assert request.quantity == 1
        assert request.product_options == {"size": "medium", "color": "blue"}
        assert request.quantity == 1

    def test_order_create_request_missing_title(self):
        """Testa erro ao criar OrderCreateRequest sem título."""
        with pytest.raises(ValidationError):
            OrderCreateRequest(
                description="Test description",
                product_type="customized",
                quantity=1,
            )

    def test_order_create_request_invalid_quantity(self):
        """Testa erro ao criar OrderCreateRequest com quantidade inválida."""
        with pytest.raises(ValidationError):
            OrderCreateRequest(
                title="Test Order",
                description="Test description",
                product_type="customized",
                quantity=0,
            )

    def test_order_update_request_valid(self):
        """Testa criação de OrderUpdateRequest válido."""
        request = OrderUpdateRequest(
            title="Updated Order",
            description="Updated description",
        )
        assert request.title == "Updated Order"
        assert request.description == "Updated description"

    def test_order_response_valid(self):
        """Testa criação de OrderResponse válido."""
        order_id = uuid4()
        client_id = uuid4()
        seller_id = uuid4()
        
        response = OrderResponse(
            id=order_id,
            title="Test Order",
            description="Test description",
            product_type="customized",
            product_options={"size": "medium"},
            quantity=1,
            estimated_price=Decimal("50.00"),
            status=OrderStatus.IN_ANALYSIS,
            client_id=client_id,
            seller_id=seller_id,
            approved_iteration_id=None,
            submitted_at=datetime.now(timezone.utc),
            approved_at=None,
            completed_at=None,
            shipping_address=None,
            shipping_city=None,
            shipping_state=None,
            shipping_zip_code=None,
            shipping_phone=None,
            image_url=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            iterations=[],
            approved_iteration=None,
        )
        assert response.id == order_id
        assert response.status == OrderStatus.IN_ANALYSIS

    def test_order_list_item_valid(self):
        """Testa criação de OrderListItem válido."""
        order_id = uuid4()
        client_id = uuid4()
        
        item = OrderListItem(
            id=order_id,
            title="Test Order",
            product_type="customized",
            quantity=1,
            estimated_price=Decimal("50.00"),
            status=OrderStatus.IN_ANALYSIS,
            client_id=client_id,
            seller_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            cover_url=None,
        )
        assert item.id == order_id
        assert item.cover_url is None

    def test_status_update_request_valid(self):
        """Testa criação de StatusUpdateRequest válido."""
        request = StatusUpdateRequest(status=OrderStatus.IN_PRODUCTION)
        assert request.status == OrderStatus.IN_PRODUCTION

    def test_status_update_request_invalid_status(self):
        """Testa erro ao criar StatusUpdateRequest com status inválido."""
        with pytest.raises(ValidationError):
            StatusUpdateRequest(status="invalid_status")

    def test_cancel_request_valid(self):
        """Testa criação de CancelRequest válido."""
        request = CancelRequest(note="Customer requested cancellation")
        assert request.note == "Customer requested cancellation"

    def test_cancel_request_empty_note(self):
        """Testa CancelRequest com note vazio."""
        request = CancelRequest(note="")
        assert request.note == ""


class TestSellerModels:
    """Testes para modelos Pydantic de Seller."""

    def test_seller_profile_update_request_valid(self):
        """Testa criação de SellerProfileUpdate válido."""
        request = SellerProfileUpdate(
            store_name="Updated Store",
            description="Updated description",
            category=SellerCategory.SHIRT,
            city="Rio de Janeiro",
            state="RJ",
            whatsapp="21999999999",
            instagram="updated_store",
            estimated_days=10,
        )
        assert request.store_name == "Updated Store"
        assert request.category == SellerCategory.SHIRT
        assert request.state == "RJ"

    def test_seller_profile_update_request_partial(self):
        """Testa SellerProfileUpdate com campos parciais."""
        request = SellerProfileUpdate(
            store_name="Updated Store",
        )
        assert request.store_name == "Updated Store"
        assert request.description is None
        assert request.category is None

    def test_seller_response_valid(self):
        """Testa criação de SellerProfileResponse válido."""
        seller_id = uuid4()
        user_id = uuid4()
        
        response = SellerProfileResponse(
            id=seller_id,
            user_id=user_id,
            store_name="Test Store",
            slug="test-store",
            category=SellerCategory.MUG,
            city="São Paulo",
            state="SP",
            whatsapp="11999999999",
            instagram="test_store",
            accepts_custom_designs=True,
            min_order_quantity=1,
            estimated_days=7,
            is_open=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert response.id == seller_id
        assert response.store_name == "Test Store"

    def test_seller_list_item_valid(self):
        """Testa criação de SellerProfileListItem válido."""
        seller_id = uuid4()
        
        item = SellerProfileListItem(
            id=seller_id,
            store_name="Test Store",
            slug="test-store",
            category=SellerCategory.MUG,
            city="São Paulo",
            state="SP",
            min_order_quantity=1,
            estimated_days=7,
            accepts_custom_designs=True,
            is_open=True,
        )
        assert item.id == seller_id
        assert item.slug == "test-store"


class TestCartModels:
    """Testes para modelos Pydantic de Cart."""

    def test_cart_checkout_request_valid(self):
        """Testa criação de CartCheckoutRequest válido."""
        seller_ids = [uuid4(), uuid4()]
        
        request = CartCheckoutRequest(
            seller_ids=seller_ids,
            shipping_address="Rua Teste, 123",
            shipping_city="São Paulo",
            shipping_state="SP",
            shipping_zip_code="01234-567",
            shipping_phone="11999999999",
            notes="Test note",
        )
        assert len(request.seller_ids) == 2

    def test_cart_checkout_response_valid(self):
        """Testa criação de CartCheckoutResponse válido."""
        order_ids = [uuid4(), uuid4()]
        
        response = CartCheckoutResponse(
            order_ids=order_ids,
            total_amount=Decimal("100.00"),
            message="Checkout successful",
        )
        assert len(response.order_ids) == 2
        assert response.total_amount == Decimal("100.00")
        assert response.message == "Checkout successful"
