import pytest
from unittest.mock import patch
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    """Render JSONB as JSON when running on SQLite (used in tests)."""
    return "JSON"


from src.database.session import Base
from src.database.models.user import User
from src.database.models.seller_profile import SellerProfile
from src.database.models.order import Order
from src.database.models.project_iteration import ProjectIteration
from src.database.models.seller_product_spec import SellerProductSpec
from src.database.models.cart_item import CartItem
from src.database.models.ai_generation import AIGeneration
from src.database.models.enums import OrderStatus, SellerCategory, UserRole
from src.api.models.order import OrderCreateRequest, OrderUpdateRequest
from src.api.models.seller import SellerProfileUpdate

from fastapi.testclient import TestClient


def _utcnow():
    return datetime.now(timezone.utc)


@pytest.fixture(autouse=True)
def mock_email_service():
    """Mock global para o serviço de email em todos os testes."""
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.send_verification_email.return_value = (True, "123456")
    mock.send_password_reset_email.return_value = True

    with patch('src.api.services.email_service.email_service', mock):
        yield mock


@pytest.fixture(autouse=True)
def disable_ai_iterations_limit():
    """Desabilita o limite de iterações com IA durante os testes."""
    with patch('config.settings.settings.AI_ITERATIONS_LIMIT_ENABLED', False):
        yield


@pytest.fixture
def client_factory(db_session: Session):
    """Factory fixture that returns a TestClient with dependency overrides.

    Usage:
        c = client_factory(user)   # authenticated as `user`
        c = client_factory(None)   # unauthenticated (real auth dep runs -> 401)
    """
    from src.api.main import app
    from src.database.session import get_db
    from src.api.dependencies.auth import (
        get_current_user,
        get_current_active_user,
        require_seller,
        require_client,
        require_admin,
        require_seller_email_verified,
    )

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def _make(current_user=None) -> TestClient:
        app.dependency_overrides[get_db] = override_get_db
        if current_user is not None:
            app.dependency_overrides[get_current_user] = lambda: current_user
            app.dependency_overrides[get_current_active_user] = lambda: current_user
            app.dependency_overrides[require_seller] = lambda: current_user
            app.dependency_overrides[require_client] = lambda: current_user
            app.dependency_overrides[require_admin] = lambda: current_user
            app.dependency_overrides[require_seller_email_verified] = lambda: current_user
        return TestClient(app)

    yield _make
    app.dependency_overrides.clear()


@pytest.fixture
def client(client_factory, test_user):
    """TestClient authenticated as the test CLIENT user."""
    return client_factory(test_user)


@pytest.fixture
def seller_client(client_factory, test_seller_user):
    """TestClient authenticated as the test SELLER user."""
    return client_factory(test_seller_user)


@pytest.fixture
def anon_client(client_factory):
    """TestClient without any auth override (real get_current_user -> 401)."""
    return client_factory(None)


@pytest.fixture(scope="function")
def db_engine(tmp_path):
    """Create a test database engine using a temporary file."""
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test client user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        email_verified=True,
        name="Test User",
        password_hash="hashed_password",
        role=UserRole.CLIENT,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_seller_user(db_session: Session):
    """Create a test user with role=SELLER (used as Order.seller_id)."""
    user = User(
        id=uuid4(),
        email="seller@example.com",
        email_verified=True,
        name="Test Seller User",
        password_hash="hashed_password",
        role=UserRole.SELLER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_seller(db_session: Session, test_seller_user: User):
    """Create a test seller profile attached to a seller user."""
    seller = SellerProfile(
        id=uuid4(),
        user_id=test_seller_user.id,
        store_name="Test Store",
        slug="test-store",
        description="Test description",
        category=SellerCategory.MUG,
        city="São Paulo",
        state="SP",
        whatsapp="11999999999",
        instagram="test_store",
        estimated_days=7,
        accepts_custom_designs=True,
        min_order_quantity=1,
        is_open=True,
    )
    db_session.add(seller)
    db_session.commit()
    db_session.refresh(seller)
    return seller


@pytest.fixture
def test_order(db_session: Session, test_user: User, test_seller_user: User):
    """Create a test order. Order.seller_id references users.id."""
    order = Order(
        id=uuid4(),
        client_id=test_user.id,
        seller_id=test_seller_user.id,
        title="Test Order",
        description="Test description",
        product_type="customized",
        product_options={"size": "medium", "color": "blue"},
        quantity=1,
        estimated_price=Decimal("50.00"),
        status=OrderStatus.IN_ANALYSIS,
        submitted_at=_utcnow(),
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def test_product_spec(db_session: Session, test_seller: SellerProfile):
    """Create a test product spec (SellerProductSpec has no `category` field)."""
    product = SellerProductSpec(
        id=uuid4(),
        seller_id=test_seller.id,
        name="Test Product",
        description="Test product description",
        attributes={"volume_ml": 250},
        base_price=Decimal("25.00"),
        is_customizable=True,
        customization_options={"size": ["small", "medium", "large"], "color": ["blue", "red"]},
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def test_cart_item(
    db_session: Session,
    test_user: User,
    test_seller_user: User,
    test_product_spec: SellerProductSpec,
):
    """Create a test cart item matching the real CartItem schema."""
    unit_price = Decimal("25.00")
    quantity = 2
    cart_item = CartItem(
        id=uuid4(),
        user_id=test_user.id,
        seller_id=test_seller_user.id,
        product_spec_id=test_product_spec.id,
        quantity=quantity,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        name=test_product_spec.name,
        description="Cart item description",
        selected_options='{"size": "medium", "color": "blue"}',
    )
    db_session.add(cart_item)
    db_session.commit()
    db_session.refresh(cart_item)
    return cart_item


@pytest.fixture
def test_iteration(db_session: Session, test_order: Order):
    """Create a test iteration. ProjectIteration.description is NOT NULL."""
    iteration = ProjectIteration(
        id=uuid4(),
        order_id=test_order.id,
        version=1,
        description="Iteration description",
        image_key="test_image_key",
        prompt="Test prompt",
    )
    db_session.add(iteration)
    db_session.commit()
    db_session.refresh(iteration)
    return iteration


# Pydantic model fixtures
@pytest.fixture
def order_create_request():
    """Create a test OrderCreateRequest."""
    return OrderCreateRequest(
        title="Test Order",
        description="Test description",
        product_type="customized",
        product_options={"size": "medium", "color": "blue"},
        quantity=1,
    )


@pytest.fixture
def order_update_request():
    """Create a test OrderUpdateRequest."""
    return OrderUpdateRequest(
        title="Updated Order",
        description="Updated description",
    )


@pytest.fixture
def seller_profile_update_request():
    """Create a test SellerProfileUpdate."""
    return SellerProfileUpdate(
        store_name="Updated Store",
        description="Updated description",
        category=SellerCategory.SHIRT,
        city="Rio de Janeiro",
        state="RJ",
        whatsapp="21999999999",
        instagram="updated_store",
        estimated_days=10,
    )
