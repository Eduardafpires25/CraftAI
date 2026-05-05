import pytest
from fastapi import status
from unittest.mock import patch


class TestEmailVerificationRoutes:
    """Testes para rotas de verificação de email."""

    def test_send_verification_success(self, client_factory, db_session):
        """Testa envio de código de verificação com sucesso."""
        from uuid import uuid4
        from src.database.models.user import User
        from src.database.models.enums import UserRole
        
        user = User(
            id=uuid4(),
            email="unverified@example.com",
            name="Unverified User",
            password_hash="hash",
            role=UserRole.CLIENT,
            email_verified=False,
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated_client = client_factory(user)
        
        with patch('src.api.services.email_service.email_service.send_verification_email') as mock_send:
            mock_send.return_value = (True, "123456")
            
            response = authenticated_client.post("/api/v1/email/send-verification")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email_sent"] is True
            assert "Código de verificação enviado" in data["message"]

    def test_send_verification_already_verified(self, client_factory, db_session):
        """Testa erro ao enviar código para email já verificado."""
        from uuid import uuid4
        from src.database.models.user import User
        from src.database.models.enums import UserRole
        
        user = User(
            id=uuid4(),
            email="verified@example.com",
            name="Verified User",
            password_hash="hash",
            role=UserRole.CLIENT,
            email_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated_client = client_factory(user)
        response = authenticated_client.post("/api/v1/email/send-verification")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email já verificado" in response.json()["detail"]

    def test_send_verification_unauthorized(self, anon_client):
        """Testa envio sem autenticação."""
        response = anon_client.post("/api/v1/email/send-verification")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_email_success(self, client_factory, db_session):
        """Testa verificação de email com sucesso."""
        from uuid import uuid4
        from src.database.models.user import User
        from src.database.models.enums import UserRole
        
        user = User(
            id=uuid4(),
            email="unverified3@example.com",
            name="Unverified User 3",
            password_hash="hash",
            role=UserRole.CLIENT,
            email_verified=False,
            email_verification_code="123456",
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated_client = client_factory(user)
        response = authenticated_client.post(
            "/api/v1/email/verify",
            json={"code": "123456"},
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email_verified"] is True
        assert "verificado com sucesso" in data["message"]

    def test_verify_email_already_verified(self, client_factory, db_session):
        """Testa erro ao verificar email já verificado."""
        from uuid import uuid4
        from src.database.models.user import User
        from src.database.models.enums import UserRole
        
        user = User(
            id=uuid4(),
            email="verified2@example.com",
            name="Verified User 2",
            password_hash="hash",
            role=UserRole.CLIENT,
            email_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated_client = client_factory(user)
        response = authenticated_client.post(
            "/api/v1/email/verify",
            json={"code": "123456"},
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email já verificado" in response.json()["detail"]

    def test_verify_email_no_pending_code(self, client_factory, db_session):
        """Testa erro quando não há código pendente."""
        from uuid import uuid4
        from src.database.models.user import User
        from src.database.models.enums import UserRole
        
        user = User(
            id=uuid4(),
            email="unverified4@example.com",
            name="Unverified User 4",
            password_hash="hash",
            role=UserRole.CLIENT,
            email_verified=False,
            email_verification_code=None,
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated_client = client_factory(user)
        response = authenticated_client.post(
            "/api/v1/email/verify",
            json={"code": "123456"},
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Nenhum código de verificação pendente" in response.json()["detail"]

    def test_verify_email_invalid_code(self, client_factory, db_session):
        """Testa erro com código inválido."""
        from uuid import uuid4
        from src.database.models.user import User
        from src.database.models.enums import UserRole
        
        user = User(
            id=uuid4(),
            email="unverified5@example.com",
            name="Unverified User 5",
            password_hash="hash",
            role=UserRole.CLIENT,
            email_verified=False,
            email_verification_code="123456",
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated_client = client_factory(user)
        response = authenticated_client.post(
            "/api/v1/email/verify",
            json={"code": "wrongcode"},
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Código de verificação inválido" in response.json()["detail"]

    def test_verify_email_case_insensitive(self, client_factory, db_session):
        """Testa verificação de código case-insensitive."""
        from uuid import uuid4
        from src.database.models.user import User
        from src.database.models.enums import UserRole
        
        user = User(
            id=uuid4(),
            email="unverified6@example.com",
            name="Unverified User 6",
            password_hash="hash",
            role=UserRole.CLIENT,
            email_verified=False,
            email_verification_code="ABCDEF",
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated_client = client_factory(user)
        response = authenticated_client.post(
            "/api/v1/email/verify",
            json={"code": "abcdef"},
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_verify_email_with_spaces(self, client_factory, db_session):
        """Testa verificação de código com espaços."""
        from uuid import uuid4
        from src.database.models.user import User
        from src.database.models.enums import UserRole
        
        user = User(
            id=uuid4(),
            email="unverified7@example.com",
            name="Unverified User 7",
            password_hash="hash",
            role=UserRole.CLIENT,
            email_verified=False,
            email_verification_code="123456",
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated_client = client_factory(user)
        response = authenticated_client.post(
            "/api/v1/email/verify",
            json={"code": " 123456 "},
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_verify_email_unauthorized(self, anon_client):
        """Testa verificação sem autenticação."""
        response = anon_client.post(
            "/api/v1/email/verify",
            json={"code": "123456"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_verification_status_verified(self, client_factory, db_session):
        """Testa status de verificação para email verificado."""
        from uuid import uuid4
        from src.database.models.user import User
        from src.database.models.enums import UserRole
        
        user = User(
            id=uuid4(),
            email="verified3@example.com",
            name="Verified User 3",
            password_hash="hash",
            role=UserRole.CLIENT,
            email_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated_client = client_factory(user)
        response = authenticated_client.get("/api/v1/email/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email_verified"] is True
        assert "Email verificado" in data["message"]

    def test_get_verification_status_unverified(self, client_factory, db_session):
        """Testa status de verificação para email não verificado."""
        from uuid import uuid4
        from src.database.models.user import User
        from src.database.models.enums import UserRole
        
        user = User(
            id=uuid4(),
            email="unverified8@example.com",
            name="Unverified User 8",
            password_hash="hash",
            role=UserRole.CLIENT,
            email_verified=False,
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated_client = client_factory(user)
        response = authenticated_client.get("/api/v1/email/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email_verified"] is False
        assert "ainda não verificado" in data["message"]

    def test_get_verification_status_unauthorized(self, anon_client):
        """Testa status sem autenticação."""
        response = anon_client.get("/api/v1/email/status")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
