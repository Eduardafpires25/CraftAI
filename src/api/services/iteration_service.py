from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.models.order import Order
from src.database.models.enums import IterationStatus
from src.database.models.project_iteration import ProjectIteration
from config.settings import settings

from config.logger import logger


class IterationService:
    """Service para gerenciar iterações com IA."""

    @staticmethod
    def get_iterations_limit(db: Session, user_id: str) -> dict:
        """
        Retorna informações sobre o limite de iterações do usuário.

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário

        Returns:
            Dict com enabled, daily_limit, used_today, remaining
        """
        if not settings.AI_ITERATIONS_LIMIT_ENABLED:
            logger.info("Limites de iterações desabilitados")
            return {
                "enabled": False,
                "daily_limit": 0,
                "used_today": 0,
                "remaining": 0,
            }

        # Contar apenas iterações bem-sucedidas (não conta FAILED)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        today_iterations = db.query(func.count(ProjectIteration.id)).join(
            Order, ProjectIteration.order_id == Order.id
        ).filter(
            Order.client_id == user_id,
            ProjectIteration.created_at >= today_start,
            ProjectIteration.status.notin_([IterationStatus.FAILED]),
        ).scalar() or 0

        remaining = max(0, settings.AI_ITERATIONS_DAILY_LIMIT - today_iterations)

        logger.info(f"Limites de iterações: enabled={settings.AI_ITERATIONS_LIMIT_ENABLED}, daily_limit={settings.AI_ITERATIONS_DAILY_LIMIT}, used_today={today_iterations}, remaining={remaining}")
        
        return {
            "enabled": True,
            "daily_limit": settings.AI_ITERATIONS_DAILY_LIMIT,
            "used_today": today_iterations,
            "remaining": remaining,
        }


iteration_service = IterationService()
