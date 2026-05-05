from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, delete, update
from sqlalchemy.orm import Session

from src.database.models.user import User
from src.database.models.token import Token
from src.database.models.enums import UserRole


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.CLIENT,
        phone: Optional[str] = None,
    ) -> User:
        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
            phone=phone,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate(self, user: User) -> User:
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_email_verification_code(self, user: User, code: str) -> User:
        """Define o código de verificação de email para o usuário."""
        user.email_verification_code = code
        self.db.commit()
        self.db.refresh(user)
        return user

    def verify_email(self, user: User) -> User:
        """Marca o email do usuário como verificado."""
        user.email_verified = True
        user.email_verification_code = None
        user.email_verified_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        return user


class TokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: uuid.UUID,
        token: str,
        token_type: str,
        expires_at: datetime,
    ) -> Token:
        db_token = Token(
            user_id=user_id,
            token=token,
            token_type=token_type,
            expires_at=expires_at,
            is_active=True,
        )
        self.db.add(db_token)
        self.db.commit()
        self.db.refresh(db_token)
        return db_token

    def get_by_token(self, token: str) -> Optional[Token]:
        return (
            self.db.query(Token)
            .filter(and_(Token.token == token, Token.is_active == True))
            .first()
        )

    def invalidate(self, token: str) -> None:
        self.db.execute(
            update(Token).where(Token.token == token).values(is_active=False)
        )
        self.db.commit()

    def invalidate_all_for_user(self, user_id: uuid.UUID) -> None:
        self.db.execute(
            update(Token)
            .where(and_(Token.user_id == user_id, Token.is_active == True))
            .values(is_active=False)
        )
        self.db.commit()

    def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        result = self.db.execute(
            delete(Token).where(Token.expires_at < now)
        )
        self.db.commit()
        return result.rowcount  # type: ignore[return-value]
