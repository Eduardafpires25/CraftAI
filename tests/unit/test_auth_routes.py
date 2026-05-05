import pytest
from uuid import uuid4
from fastapi import status

from src.api.models.auth import RegisterRequest, LoginRequest, RefreshTokenRequest
from src.database.models.enums import UserRole


class TestAuthRoutes:
    """Testes para rotas de autenticação."""

    def test_register_client_success(self, client):
        """Testa registro de cliente com sucesso."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "New Client",
                "email": "newclient@example.com",
                "password": "StrongP@ssw0rd!2024",
                "role": "client",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newclient@example.com"
        assert data["name"] == "New Client"
        assert data["role"] == "client"

    def test_register_seller_success(self, client):
        """Testa registro de seller com sucesso."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "New Seller",
                "email": "newseller@example.com",
                "password": "StrongP@ssw0rd!2024",
                "role": "seller",
                "phone": "11999999999",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newseller@example.com"
        assert data["name"] == "New Seller"
        assert data["role"] == "seller"

    def test_register_email_conflict(self, client, test_user):
        """Testa erro ao registrar com email já existente."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": test_user.email,
                "password": "StrongP@ssw0rd!2024",
                "role": "client",
            },
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "E-mail já cadastrado" in response.json()["detail"]

    def test_login_success(self, client, db_session):
        """Testa login com sucesso."""
        from src.database.models.user import User
        from src.api.services.auth_service import auth_service
        from src.api.repositories.auth_repository import UserRepository
        
        user_repo = UserRepository(db_session)
        user = auth_service.register_user(
            user_repo,
            name="Login User",
            email="login@example.com",
            password="StrongP@ssw0rd!2024",
            role=UserRole.CLIENT,
        )
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "StrongP@ssw0rd!2024",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_email(self, client):
        """Testa login com email incorreto."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "E-mail ou senha incorretos" in response.json()["detail"]

    def test_login_wrong_password(self, client, db_session):
        """Testa login com senha incorreta."""
        from src.database.models.user import User
        from src.api.services.auth_service import auth_service
        from src.api.repositories.auth_repository import UserRepository
        
        user_repo = UserRepository(db_session)
        user = auth_service.register_user(
            user_repo,
            name="Login User",
            email="login2@example.com",
            password="StrongP@ssw0rd!2024",
            role=UserRole.CLIENT,
        )
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "login2@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "E-mail ou senha incorretos" in response.json()["detail"]

    def test_refresh_token_success(self, client, db_session):
        """Testa refresh de token com sucesso."""
        from src.api.services.auth_service import auth_service
        from src.api.repositories.auth_repository import UserRepository, TokenRepository
        
        user_repo = UserRepository(db_session)
        token_repo = TokenRepository(db_session)
        
        user = auth_service.register_user(
            user_repo,
            name="Refresh User",
            email="refresh@example.com",
            password="StrongP@ssw0rd!2024",
            role=UserRole.CLIENT,
        )
        
        tokens = auth_service.create_user_tokens(user, token_repo)
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": tokens["refresh_token"],
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client):
        """Testa refresh com token inválido."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": "invalid_token",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Refresh token inválido ou expirado" in response.json()["detail"]

    def test_logout_success(self, client, db_session):
        """Testa logout com sucesso."""
        from src.api.services.auth_service import auth_service
        from src.api.repositories.auth_repository import UserRepository, TokenRepository
        
        user_repo = UserRepository(db_session)
        token_repo = TokenRepository(db_session)
        
        user = auth_service.register_user(
            user_repo,
            name="Logout User",
            email="logout@example.com",
            password="StrongP@ssw0rd!2024",
            role=UserRole.CLIENT,
        )
        
        tokens = auth_service.create_user_tokens(user, token_repo)
        
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "Logout realizado com sucesso" in response.json()["detail"]

    def test_logout_no_token(self, client):
        """Testa logout sem token."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Token não fornecido" in response.json()["detail"]

    def test_me_success(self, client_factory, test_user):
        """Testa endpoint /me com sucesso."""
        authenticated_client = client_factory(test_user)
        response = authenticated_client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name

    def test_me_unauthorized(self, anon_client):
        """Testa endpoint /me sem autenticação."""
        response = anon_client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
