from __future__ import annotations

from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models.user import User
from src.database.models.enums import UserRole
from src.api.repositories.auth_repository import UserRepository, TokenRepository
from src.api.services.auth_service import auth_service

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user_repo = UserRepository(db)
    token_repo = TokenRepository(db)

    user = auth_service.get_current_user_from_token(token, user_repo, token_repo)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo.",
        )
    return current_user


class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente.",
            )
        return current_user


require_admin = RoleChecker([UserRole.ADMIN])
require_seller = RoleChecker([UserRole.SELLER, UserRole.ADMIN])
require_client = RoleChecker([UserRole.CLIENT, UserRole.ADMIN])


def require_seller_email_verified(
    current_user: User = Depends(require_seller),
) -> User:
    """
    Verifica se o vendedor tem o email verificado.
    Lança HTTPException se não estiver verificado.
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não verificado. Verifique seu email para continuar.",
        )
    return current_user
