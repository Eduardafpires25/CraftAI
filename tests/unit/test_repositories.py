import pytest
from uuid import uuid4, UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from src.database.session import Base
from src.database.models.user import User
from src.database.models.seller_profile import SellerProfile
from src.database.models.order import Order
from src.database.models.project_iteration import ProjectIteration
from src.database.models.seller_product_spec import SellerProductSpec
from src.database.models.cart_item import CartItem
from src.database.models.enums import OrderStatus, SellerCategory
from src.api.repositories.order_repository import OrderRepository, IterationRepository
from src.api.repositories.seller_repository import SellerRepository, SellerProductSpecRepository
from src.api.repositories.cart_repository import CartRepository


class TestOrderRepository:
    """Testes para OrderRepository (API real: create/update/change_status)."""

    def test_create_order(self, db_session: Session, test_user: User, test_seller_user: User):
        """Testa criação de order."""
        repo = OrderRepository(db_session)

        order = repo.create(
            client_id=test_user.id,
            seller_id=test_seller_user.id,
            title="Test Order",
            description="Test description",
            product_type="customized",
            product_options={"size": "medium", "color": "blue"},
            quantity=1,
        )

        assert order.id is not None
        assert order.title == "Test Order"
        assert order.status == OrderStatus.DRAFT
        assert order.client_id == test_user.id
        assert order.seller_id == test_seller_user.id

    def test_get_order_by_id(self, db_session: Session, test_order: Order):
        """Testa busca de order por ID."""
        repo = OrderRepository(db_session)
        order = repo.get_by_id(test_order.id)
        assert order is not None
        assert order.id == test_order.id

    def test_get_order_by_id_not_found(self, db_session: Session):
        """Testa busca de order por ID não encontrado."""
        repo = OrderRepository(db_session)
        assert repo.get_by_id(uuid4()) is None

    def test_list_for_client(self, db_session: Session, test_user: User, test_seller_user: User):
        """Testa busca de orders por cliente."""
        repo = OrderRepository(db_session)
        for i in range(3):
            repo.create(
                client_id=test_user.id,
                seller_id=test_seller_user.id,
                title=f"Order {i}",
                description=f"desc {i}",
                product_type="customized",
                quantity=1,
            )

        orders = repo.list_for_client(test_user.id)
        assert len(orders) >= 3
        assert all(o.client_id == test_user.id for o in orders)

    def test_list_for_seller(self, db_session: Session, test_user: User, test_seller_user: User):
        """Testa busca de orders por seller (ignora DRAFT/COMPLETED/CANCELLED)."""
        repo = OrderRepository(db_session)
        for i in range(2):
            order = repo.create(
                client_id=test_user.id,
                seller_id=test_seller_user.id,
                title=f"Order {i}",
                description=f"desc {i}",
                product_type="customized",
                quantity=1,
            )
            repo.change_status(order, OrderStatus.IN_ANALYSIS)

        orders = repo.list_for_seller(test_seller_user.id)
        assert len(orders) >= 2
        assert all(o.seller_id == test_seller_user.id for o in orders)

    def test_change_status_approved(self, db_session: Session, test_order: Order):
        """Testa transição de status para APPROVED (seta approved_at)."""
        repo = OrderRepository(db_session)
        updated = repo.change_status(test_order, OrderStatus.APPROVED)
        assert updated.status == OrderStatus.APPROVED
        assert updated.approved_at is not None

    def test_change_status_completed(self, db_session: Session, test_order: Order):
        """Testa transição para COMPLETED (seta completed_at)."""
        repo = OrderRepository(db_session)
        updated = repo.change_status(test_order, OrderStatus.COMPLETED)
        assert updated.status == OrderStatus.COMPLETED
        assert updated.completed_at is not None

    def test_update(self, db_session: Session, test_order: Order):
        """Testa atualização de campos via update()."""
        repo = OrderRepository(db_session)
        updated = repo.update(test_order, title="New Title", quantity=5)
        assert updated.title == "New Title"
        assert updated.quantity == 5


class TestIterationRepository:
    """Testes para IterationRepository."""

    def test_create_iteration(self, db_session: Session, test_order: Order):
        """Testa criação de iteration com versão auto-incremental."""
        repo = IterationRepository(db_session)
        it = repo.create(
            order_id=test_order.id,
            description="Iteration description",
            prompt="Test prompt",
            image_key="test_image_key",
        )
        assert it.id is not None
        assert it.order_id == test_order.id
        assert it.version == 1

    def test_list_by_order(self, db_session: Session, test_iteration: ProjectIteration):
        """Testa listagem de iterations por order."""
        repo = IterationRepository(db_session)
        items = repo.list_by_order(test_iteration.order_id)
        assert len(items) == 1
        assert items[0].id == test_iteration.id

    def test_next_version(self, db_session: Session, test_iteration: ProjectIteration):
        """Testa cálculo de próxima versão."""
        repo = IterationRepository(db_session)
        assert repo.next_version(test_iteration.order_id) == 2

    def test_mark_approved_unique(self, db_session: Session, test_iteration: ProjectIteration):
        """Testa marcação de iteration como aprovada."""
        repo = IterationRepository(db_session)
        approved = repo.mark_approved_unique(test_iteration)
        from src.database.models.enums import IterationStatus
        assert approved.status == IterationStatus.APPROVED


class TestSellerRepository:
    """Testes para SellerRepository (API real: create/update/list_active)."""

    def test_create(self, db_session: Session, test_seller_user: User):
        """Testa criação de perfil de seller."""
        repo = SellerRepository(db_session)
        seller = repo.create(
            user_id=test_seller_user.id,
            store_name="New Store",
            slug="new-store",
            category=SellerCategory.MUG,
            description="Test description",
            city="São Paulo",
            state="SP",
            whatsapp="11999999999",
            instagram="new_store",
            estimated_days=7,
            accepts_custom_designs=True,
            min_order_quantity=1,
        )
        assert seller.id is not None
        assert seller.store_name == "New Store"
        assert seller.category == SellerCategory.MUG

    def test_get_by_id(self, db_session: Session, test_seller: SellerProfile):
        repo = SellerRepository(db_session)
        seller = repo.get_by_id(test_seller.id)
        assert seller is not None
        assert seller.store_name == "Test Store"

    def test_get_by_slug(self, db_session: Session, test_seller: SellerProfile):
        repo = SellerRepository(db_session)
        seller = repo.get_by_slug("test-store")
        assert seller is not None
        assert seller.slug == "test-store"

    def test_get_by_user_id(self, db_session: Session, test_seller: SellerProfile):
        repo = SellerRepository(db_session)
        seller = repo.get_by_user_id(test_seller.user_id)
        assert seller is not None

    def test_update(self, db_session: Session, test_seller: SellerProfile):
        """Testa atualização via update(seller, **kwargs)."""
        repo = SellerRepository(db_session)
        updated = repo.update(
            test_seller,
            store_name="Updated Store",
            category=SellerCategory.SHIRT,
            state="RJ",
        )
        assert updated.store_name == "Updated Store"
        assert updated.category == SellerCategory.SHIRT
        assert updated.state == "RJ"

    def test_list_active(self, db_session: Session, test_seller: SellerProfile):
        """Testa listagem de sellers ativos."""
        repo = SellerRepository(db_session)
        sellers = repo.list_active()
        assert len(sellers) >= 1
        assert test_seller.id in [s.id for s in sellers]

    def test_list_active_by_category(self, db_session: Session, test_seller: SellerProfile):
        repo = SellerRepository(db_session)
        sellers = repo.list_active(category=SellerCategory.MUG)
        assert len(sellers) >= 1
        assert all(s.category == SellerCategory.MUG for s in sellers)

    def test_slug_exists(self, db_session: Session, test_seller: SellerProfile):
        repo = SellerRepository(db_session)
        assert repo.slug_exists("test-store") is True
        assert repo.slug_exists("non-existent") is False

    def test_close_shop(self, db_session: Session, test_seller: SellerProfile):
        repo = SellerRepository(db_session)
        closed = repo.close_shop(test_seller)
        assert closed.is_open is False


class TestSellerProductSpecRepository:
    """Testes para SellerProductSpecRepository."""

    def test_create(self, db_session: Session, test_seller: SellerProfile):
        repo = SellerProductSpecRepository(db_session)
        spec = repo.create(
            seller_id=test_seller.id,
            name="New Product",
            description="desc",
            attributes={"volume_ml": 250},
            is_customizable=False,
            base_price=Decimal("20.00"),
        )
        assert spec.id is not None
        assert spec.name == "New Product"
        assert spec.is_active is True

    def test_list_by_seller(self, db_session: Session, test_product_spec: SellerProductSpec):
        repo = SellerProductSpecRepository(db_session)
        specs = repo.list_by_seller(test_product_spec.seller_id)
        assert len(specs) >= 1

    def test_deactivate(self, db_session: Session, test_product_spec: SellerProductSpec):
        repo = SellerProductSpecRepository(db_session)
        updated = repo.deactivate(test_product_spec)
        assert updated.is_active is False


class TestCartRepository:
    """Testes para CartRepository (API real: create/update_quantity/delete/clear_user_cart)."""

    def test_create_item(
        self,
        db_session: Session,
        test_user: User,
        test_seller_user: User,
        test_product_spec: SellerProductSpec,
    ):
        """Testa criação de item no carrinho."""
        repo = CartRepository(db_session)
        item = repo.create(
            user_id=test_user.id,
            seller_id=test_seller_user.id,
            quantity=2,
            unit_price=Decimal("25.00"),
            name="Test Product",
            product_spec_id=test_product_spec.id,
            selected_options='{"size": "medium"}',
        )
        assert item.id is not None
        assert item.quantity == 2
        assert item.total_price == Decimal("50.00")

    def test_update_quantity(self, db_session: Session, test_cart_item: CartItem):
        """Testa atualização de quantidade (recalcula total)."""
        repo = CartRepository(db_session)
        updated = repo.update_quantity(test_cart_item, 5)
        assert updated.quantity == 5
        assert updated.total_price == updated.unit_price * 5

    def test_delete(self, db_session: Session, test_cart_item: CartItem):
        """Testa remoção de item."""
        repo = CartRepository(db_session)
        item_id = test_cart_item.id
        repo.delete(test_cart_item)
        assert db_session.query(CartItem).filter(CartItem.id == item_id).first() is None

    def test_clear_user_cart(self, db_session: Session, test_cart_item: CartItem):
        """Testa limpeza do carrinho de um usuário."""
        repo = CartRepository(db_session)
        user_id = test_cart_item.user_id
        repo.clear_user_cart(user_id)
        assert repo.list_for_user(user_id) == []

    def test_list_for_user(self, db_session: Session, test_cart_item: CartItem):
        repo = CartRepository(db_session)
        items = repo.list_for_user(test_cart_item.user_id)
        assert len(items) == 1

    def test_get_cart_total(self, db_session: Session, test_cart_item: CartItem):
        repo = CartRepository(db_session)
        total = repo.get_cart_total(test_cart_item.user_id)
        assert total == test_cart_item.total_price

    def test_count_for_user(self, db_session: Session, test_cart_item: CartItem):
        repo = CartRepository(db_session)
        count = repo.count_for_user(test_cart_item.user_id)
        assert count == test_cart_item.quantity

    def test_list_for_user_grouped_by_seller(self, db_session: Session, test_cart_item: CartItem):
        repo = CartRepository(db_session)
        grouped = repo.list_for_user_grouped_by_seller(test_cart_item.user_id)
        assert test_cart_item.seller_id in grouped
        assert len(grouped[test_cart_item.seller_id]) == 1

    def test_find_existing_item(self, db_session: Session, test_cart_item: CartItem):
        repo = CartRepository(db_session)
        found = repo.find_existing_item(
            user_id=test_cart_item.user_id,
            product_spec_id=test_cart_item.product_spec_id,
            selected_options=test_cart_item.selected_options,
        )
        assert found is not None
        assert found.id == test_cart_item.id
