import pytest
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock

from src.api.services.auth_service import AuthService
from src.database.models.user import User
from src.database.models.enums import UserRole
from src.api.repositories.auth_repository import UserRepository, TokenRepository


class TestAuthService:
    """Testes para AuthService."""

    def test_get_password_hash(self):
        """Testa geração de hash de senha."""
        service = AuthService()
        password = "test_password"
        hashed = service.get_password_hash(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Testa verificação de senha correta."""
        service = AuthService()
        password = "test_password"
        hashed = service.get_password_hash(password)
        
        assert service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Testa verificação de senha incorreta."""
        service = AuthService()
        password = "test_password"
        wrong_password = "wrong_password"
        hashed = service.get_password_hash(password)
        
        assert service.verify_password(wrong_password, hashed) is False

    def test_verify_password_invalid_hash(self):
        """Testa verificação com hash inválido."""
        service = AuthService()
        
        assert service.verify_password("test", "invalid_hash") is False

    def test_create_access_token(self):
        """Testa criação de access token."""
        service = AuthService()
        data = {"sub": str(uuid4()), "email": "test@example.com"}
        
        token = service.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_custom_expires(self):
        """Testa criação de access token com expiração customizada."""
        service = AuthService()
        data = {"sub": str(uuid4()), "email": "test@example.com"}
        custom_delta = timedelta(hours=2)
        
        token = service.create_access_token(data, expires_delta=custom_delta)
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Testa criação de refresh token."""
        service = AuthService()
        data = {"sub": str(uuid4())}
        
        token = service.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid(self):
        """Testa verificação de token válido."""
        service = AuthService()
        data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = service.create_access_token(data)
        
        payload = service.verify_token(token, "access")
        
        assert payload is not None
        assert payload["sub"] == data["sub"]
        assert payload["email"] == data["email"]
        assert payload["type"] == "access"

    def test_verify_token_invalid_type(self):
        """Testa verificação de token com tipo incorreto."""
        service = AuthService()
        data = {"sub": str(uuid4())}
        token = service.create_refresh_token(data)
        
        payload = service.verify_token(token, "access")
        
        assert payload is None

    def test_verify_token_invalid(self):
        """Testa verificação de token inválido."""
        service = AuthService()
        
        payload = service.verify_token("invalid_token", "access")
        
        assert payload is None

    def test_register_user_success(self):
        """Testa registro de usuário com sucesso."""
        service = AuthService()
        user_repo = Mock(spec=UserRepository)
        user_repo.get_by_email.return_value = None
        user_repo.create.return_value = Mock(id=uuid4(), email="test@example.com")
        
        user = service.register_user(
            user_repo,
            name="Test User",
            email="test@example.com",
            password="password123",
            role=UserRole.CLIENT,
        )
        
        assert user is not None
        user_repo.create.assert_called_once()

    def test_register_user_admin_forbidden(self):
        """Testa erro ao tentar registrar admin."""
        service = AuthService()
        user_repo = Mock(spec=UserRepository)
        
        with pytest.raises(ValueError, match="Não é possível registrar um administrador"):
            service.register_user(
                user_repo,
                name="Admin",
                email="admin@example.com",
                password="password123",
                role=UserRole.ADMIN,
            )

    def test_register_user_email_exists(self):
        """Testa erro ao registrar com email já cadastrado."""
        service = AuthService()
        user_repo = Mock(spec=UserRepository)
        user_repo.get_by_email.return_value = Mock(id=uuid4())
        
        with pytest.raises(ValueError, match="E-mail já cadastrado"):
            service.register_user(
                user_repo,
                name="Test User",
                email="test@example.com",
                password="password123",
            )

    def test_register_user_with_background_email_client(self):
        """Testa registro de cliente sem email de verificação."""
        service = AuthService()
        user_repo = Mock(spec=UserRepository)
        user_repo.get_by_email.return_value = None
        user_repo.create.return_value = Mock(id=uuid4(), email="test@example.com")
        background_tasks = Mock()
        
        user = service.register_user_with_background_email(
            user_repo,
            background_tasks,
            name="Test User",
            email="test@example.com",
            password="password123",
            role=UserRole.CLIENT,
        )
        
        assert user is not None
        # Cliente não deve receber email de verificação
        assert not background_tasks.add_task.called

    def test_register_user_with_background_email_seller(self):
        """Testa registro de seller com email de verificação."""
        service = AuthService()
        user_repo = Mock(spec=UserRepository)
        user_repo.get_by_email.return_value = None
        user_repo.create.return_value = Mock(id=uuid4(), email="seller@example.com")
        background_tasks = Mock()
        
        with patch('src.api.services.auth_service.email_service') as mock_email_service:
            mock_email_service.send_verification_email_background.return_value = "123456"
            
            user = service.register_user_with_background_email(
                user_repo,
                background_tasks,
                name="Test Seller",
                email="seller@example.com",
                password="password123",
                role=UserRole.SELLER,
            )
            
            assert user is not None
            mock_email_service.send_verification_email_background.assert_called_once()
            user_repo.set_email_verification_code.assert_called_once()

    def test_authenticate_user_success(self):
        """Testa autenticação de usuário com sucesso."""
        service = AuthService()
        user_repo = Mock(spec=UserRepository)
        user = Mock(
            id=uuid4(),
            email="test@example.com",
            password_hash=service.get_password_hash("password123"),
            is_active=True,
        )
        user_repo.get_by_email.return_value = user
        
        result = service.authenticate_user(user_repo, "test@example.com", "password123")
        
        assert result == user

    def test_authenticate_user_not_found(self):
        """Testa autenticação com usuário não encontrado."""
        service = AuthService()
        user_repo = Mock(spec=UserRepository)
        user_repo.get_by_email.return_value = None
        
        result = service.authenticate_user(user_repo, "test@example.com", "password123")
        
        assert result is None

    def test_authenticate_user_inactive(self):
        """Testa autenticação de usuário inativo."""
        service = AuthService()
        user_repo = Mock(spec=UserRepository)
        user = Mock(
            id=uuid4(),
            email="test@example.com",
            password_hash=service.get_password_hash("password123"),
            is_active=False,
        )
        user_repo.get_by_email.return_value = user
        
        result = service.authenticate_user(user_repo, "test@example.com", "password123")
        
        assert result is None

    def test_authenticate_user_wrong_password(self):
        """Testa autenticação com senha incorreta."""
        service = AuthService()
        user_repo = Mock(spec=UserRepository)
        user = Mock(
            id=uuid4(),
            email="test@example.com",
            password_hash=service.get_password_hash("password123"),
            is_active=True,
        )
        user_repo.get_by_email.return_value = user
        
        result = service.authenticate_user(user_repo, "test@example.com", "wrong_password")
        
        assert result is None

    def test_create_user_tokens(self):
        """Testa criação de tokens para usuário."""
        service = AuthService()
        user = Mock(
            id=uuid4(),
            email="test@example.com",
            role=UserRole.CLIENT,
        )
        token_repo = Mock(spec=TokenRepository)
        
        tokens = service.create_user_tokens(user, token_repo)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert "expires_in" in tokens
        assert token_repo.create.call_count == 2

    def test_refresh_access_token_success(self):
        """Testa refresh de access token com sucesso."""
        service = AuthService()
        user_id = uuid4()
        user = Mock(id=user_id, email="test@example.com", is_active=True)
        user.role = UserRole.CLIENT
        
        refresh_token = service.create_refresh_token({"sub": str(user_id)})
        
        user_repo = Mock(spec=UserRepository)
        user_repo.get_by_id.return_value = user
        token_repo = Mock(spec=TokenRepository)
        token_repo.get_by_token.return_value = Mock(token_type="refresh", is_active=True)
        
        new_tokens = service.refresh_access_token(refresh_token, user_repo, token_repo)
        
        assert new_tokens is not None
        assert "access_token" in new_tokens
        token_repo.invalidate.assert_called_once_with(refresh_token)

    def test_refresh_access_token_invalid_token(self):
        """Testa refresh com token inválido."""
        service = AuthService()
        user_repo = Mock(spec=UserRepository)
        token_repo = Mock(spec=TokenRepository)
        token_repo.get_by_token.return_value = None
        
        result = service.refresh_access_token("invalid", user_repo, token_repo)
        
        assert result is None

    def test_refresh_access_token_wrong_type(self):
        """Testa refresh com tipo de token incorreto."""
        service = AuthService()
        user_id = uuid4()
        
        access_token = service.create_access_token({"sub": str(user_id)})
        
        user_repo = Mock(spec=UserRepository)
        token_repo = Mock(spec=TokenRepository)
        token_repo.get_by_token.return_value = Mock(token_type="access", is_active=True)
        
        result = service.refresh_access_token(access_token, user_repo, token_repo)
        
        assert result is None

    def test_refresh_access_token_user_not_found(self):
        """Testa refresh com usuário não encontrado."""
        service = AuthService()
        user_id = uuid4()
        
        refresh_token = service.create_refresh_token({"sub": str(user_id)})
        
        user_repo = Mock(spec=UserRepository)
        user_repo.get_by_id.return_value = None
        token_repo = Mock(spec=TokenRepository)
        token_repo.get_by_token.return_value = Mock(token_type="refresh", is_active=True)
        
        result = service.refresh_access_token(refresh_token, user_repo, token_repo)
        
        assert result is None

    def test_logout_success(self):
        """Testa logout com sucesso."""
        service = AuthService()
        user_id = uuid4()
        
        access_token = service.create_access_token({"sub": str(user_id)})
        
        token_repo = Mock(spec=TokenRepository)
        
        service.logout(access_token, token_repo)
        
        token_repo.invalidate_all_for_user.assert_called_once()

    def test_logout_invalid_token(self):
        """Testa logout com token inválido."""
        service = AuthService()
        token_repo = Mock(spec=TokenRepository)
        
        service.logout("invalid", token_repo)
        
        assert not token_repo.invalidate_all_for_user.called

    def test_get_current_user_from_token_success(self):
        """Testa obtenção de usuário a partir de token com sucesso."""
        service = AuthService()
        user_id = uuid4()
        user = Mock(id=user_id, email="test@example.com", is_active=True)
        
        access_token = service.create_access_token({"sub": str(user_id), "email": "test@example.com"})
        
        user_repo = Mock(spec=UserRepository)
        user_repo.get_by_id.return_value = user
        token_repo = Mock(spec=TokenRepository)
        token_repo.get_by_token.return_value = Mock(is_active=True)
        
        result = service.get_current_user_from_token(access_token, user_repo, token_repo)
        
        assert result == user
        token_repo.cleanup_expired.assert_called_once()

    def test_get_current_user_from_token_invalid_token(self):
        """Testa obtenção de usuário com token inválido."""
        service = AuthService()
        user_repo = Mock(spec=UserRepository)
        token_repo = Mock(spec=TokenRepository)
        token_repo.get_by_token.return_value = None
        
        result = service.get_current_user_from_token("invalid", user_repo, token_repo)
        
        assert result is None

    def test_get_current_user_from_token_inactive_user(self):
        """Testa obtenção de usuário inativo."""
        service = AuthService()
        user_id = uuid4()
        user = Mock(id=user_id, email="test@example.com", is_active=False)
        
        access_token = service.create_access_token({"sub": str(user_id), "email": "test@example.com"})
        
        user_repo = Mock(spec=UserRepository)
        user_repo.get_by_id.return_value = user
        token_repo = Mock(spec=TokenRepository)
        token_repo.get_by_token.return_value = Mock(is_active=True)
        
        result = service.get_current_user_from_token(access_token, user_repo, token_repo)
        
        assert result is None

    def test_get_current_user_from_token_invalid_uuid(self):
        """Testa obtenção de usuário com UUID inválido."""
        service = AuthService()
        
        access_token = service.create_access_token({"sub": "invalid-uuid", "email": "test@example.com"})
        
        user_repo = Mock(spec=UserRepository)
        user_repo.get_by_id.side_effect = ValueError("Invalid UUID")
        token_repo = Mock(spec=TokenRepository)
        token_repo.get_by_token.return_value = Mock(is_active=True)
        
        result = service.get_current_user_from_token(access_token, user_repo, token_repo)
        
        assert result is None
