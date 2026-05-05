from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models.user import User
from src.database.models.enums import UserRole
from src.api.dependencies.auth import get_current_active_user
from src.api.repositories.auth_repository import UserRepository
from src.api.services.email_service import email_service
from config.logger import logger

router = APIRouter(prefix="/email", tags=["email-verification"])


class VerificationRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=10, description="Código de verificação enviado por email")


class VerificationResponse(BaseModel):
    message: str
    email_verified: bool


class ResendCodeResponse(BaseModel):
    message: str
    email_sent: bool


@router.post("/send-verification", response_model=ResendCodeResponse)
def send_verification_email(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Envia (ou reenvia) o código de verificação por email.
    Requer autenticação.
    """
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já verificado.",
        )

    user_repo = UserRepository(db)

    # Gera e envia novo código
    success, code = email_service.send_verification_email(
        to_email=current_user.email,
        name=current_user.name,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao enviar email de verificação. Tente novamente mais tarde.",
        )

    # Salva código no banco
    user_repo.set_email_verification_code(current_user, code)

    logger.info("Código de verificação enviado para %s", current_user.email)

    return ResendCodeResponse(
        message="Código de verificação enviado para seu email.",
        email_sent=True,
    )


@router.post("/verify", response_model=VerificationResponse)
def verify_email(
    body: VerificationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Verifica o email do usuário usando o código recebido.
    Requer autenticação.
    """
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já verificado.",
        )

    if not current_user.email_verification_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum código de verificação pendente. Solicite um novo código.",
        )

    # Compara códigos (case-insensitive, remove espaços)
    provided_code = body.code.strip().upper()
    expected_code = current_user.email_verification_code.upper()

    if provided_code != expected_code:
        logger.warning("Tentativa de verificação com código inválido: %s", current_user.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de verificação inválido.",
        )

    # Marca email como verificado
    user_repo = UserRepository(db)
    user_repo.verify_email(current_user)

    logger.info("Email verificado com sucesso: %s", current_user.email)

    return VerificationResponse(
        message="Email verificado com sucesso!",
        email_verified=True,
    )


@router.get("/status", response_model=VerificationResponse)
def get_verification_status(
    current_user: User = Depends(get_current_active_user),
):
    """Retorna o status de verificação do email do usuário logado."""
    if current_user.email_verified:
        return VerificationResponse(
            message="Email verificado.",
            email_verified=True,
        )
    return VerificationResponse(
        message="Email ainda não verificado. Use o endpoint /send-verification para receber o código.",
        email_verified=False,
    )
