from __future__ import annotations

import hashlib
import base64
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

import bcrypt
from fastapi import BackgroundTasks
from jose import JWTError, jwt

from config.logger import logger
from config.settings import settings
from src.database.models.user import User
from src.database.models.enums import UserRole
from src.api.repositories.auth_repository import UserRepository, TokenRepository
from src.api.services.email_service import email_service


class AuthService:
    def __init__(self) -> None:
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def _prepare_password_for_bcrypt(self, password: str) -> str:
        sha256_hash = hashlib.sha256(password.encode("utf-8")).digest()
        return base64.b64encode(sha256_hash).decode("utf-8")

    def get_password_hash(self, password: str) -> str:
        prepared = self._prepare_password_for_bcrypt(password)
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(prepared.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        prepared = self._prepare_password_for_bcrypt(plain_password)
        try:
            return bcrypt.checkpw(prepared.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception as e:
            logger.error("Erro ao verificar senha: %s", e)
            return False

    def _create_token(self, data: Dict[str, Any], token_type: str, expires_delta: timedelta) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire, "type": token_type, "jti": str(uuid.uuid4())})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        delta = expires_delta or timedelta(minutes=self.access_token_expire_minutes)
        return self._create_token(data, "access", delta)

    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        delta = expires_delta or timedelta(days=self.refresh_token_expire_days)
        return self._create_token(data, "refresh", delta)

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                logger.warning("Tipo de token incorreto: esperado %s, recebido %s", token_type, payload.get("type"))
                return None
            exp = payload.get("exp")
            if exp is None or datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
                logger.warning("Token expirado")
                return None
            return payload
        except JWTError as e:
            logger.warning("Erro JWT: %s", e)
            return None

    def register_user(
        self,
        user_repo: UserRepository,
        *,
        name: str,
        email: str,
        password: str,
        role: UserRole = UserRole.CLIENT,
        phone: Optional[str] = None,
    ) -> User:
        if role == UserRole.ADMIN:
            raise ValueError("Não é possível registrar um administrador via registro público.")

        existing = user_repo.get_by_email(email)
        if existing:
            raise ValueError("E-mail já cadastrado.")

        password_hash = self.get_password_hash(password)
        user = user_repo.create(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
            phone=phone,
        )

        return user

    def register_user_with_background_email(
        self,
        user_repo: UserRepository,
        background_tasks: BackgroundTasks,
        *,
        name: str,
        email: str,
        password: str,
        role: UserRole = UserRole.CLIENT,
        phone: Optional[str] = None,
        on_email_sent: Optional[Callable[[str, str], None]] = None,
    ) -> User:
        """
        Registra usuário e envia email de verificação em background (para sellers).
        """
        user = self.register_user(
            user_repo,
            name=name,
            email=email,
            password=password,
            role=role,
            phone=phone,
        )

        # Envia email de verificação em background para sellers
        if role == UserRole.SELLER:
            code = email_service.send_verification_email_background(
                background_tasks=background_tasks,
                to_email=user.email,
                name=user.name,
                on_complete=on_email_sent,
            )
            # Salva código imediatamente (mesmo que email ainda não tenha sido enviado)
            user_repo.set_email_verification_code(user, code)
            logger.info("Código de verificação gerado para seller (envio em background): %s", user.email)

        logger.info("Usuário registrado: %s (%s)", user.email, user.role.value)
        return user

    def authenticate_user(
        self,
        user_repo: UserRepository,
        email: str,
        password: str,
    ) -> Optional[User]:
        user = user_repo.get_by_email(email)
        if not user:
            logger.warning("Usuário não encontrado: %s", email)
            return None
        if not user.is_active:
            logger.warning("Usuário inativo tentou login: %s", email)
            return None
        if not self.verify_password(password, user.password_hash):
            logger.warning("Senha incorreta para: %s", email)
            return None
        logger.info("Usuário autenticado: %s", email)
        return user

    def create_user_tokens(
        self,
        user: User,
        token_repo: TokenRepository,
    ) -> Dict[str, Any]:
        access_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
        refresh_data = {"sub": str(user.id)}

        access_expires = timedelta(minutes=self.access_token_expire_minutes)
        refresh_expires = timedelta(days=self.refresh_token_expire_days)

        access_token = self.create_access_token(access_data, expires_delta=access_expires)
        refresh_token = self.create_refresh_token(refresh_data, expires_delta=refresh_expires)

        now = datetime.now(timezone.utc)
        token_repo.create(user_id=user.id, token=access_token, token_type="access", expires_at=now + access_expires)
        token_repo.create(user_id=user.id, token=refresh_token, token_type="refresh", expires_at=now + refresh_expires)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_expires.total_seconds()),
        }

    def refresh_access_token(
        self,
        refresh_token: str,
        user_repo: UserRepository,
        token_repo: TokenRepository,
    ) -> Optional[Dict[str, Any]]:
        stored = token_repo.get_by_token(refresh_token)
        if not stored or stored.token_type != "refresh":
            return None

        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = user_repo.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            return None

        token_repo.invalidate(refresh_token)

        return self.create_user_tokens(user, token_repo)

    def logout(self, access_token: str, token_repo: TokenRepository) -> None:
        payload = self.verify_token(access_token, "access")
        if not payload:
            return
        user_id = payload.get("sub")
        if user_id:
            token_repo.invalidate_all_for_user(uuid.UUID(user_id))

    def get_current_user_from_token(
        self,
        token: str,
        user_repo: UserRepository,
        token_repo: TokenRepository,
    ) -> Optional[User]:
        try:
            token_repo.cleanup_expired()
        except Exception as e:
            logger.warning("Falha ao limpar tokens expirados: %s", e)

        stored = token_repo.get_by_token(token)
        if not stored or not stored.is_active:
            return None

        payload = self.verify_token(token, "access")
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        try:
            user = user_repo.get_by_id(uuid.UUID(user_id))
            if user and not user.is_active:
                return None
            return user
        except ValueError:
            logger.warning("UUID inválido no token sub: %s", user_id)
            return None


auth_service = AuthService()
