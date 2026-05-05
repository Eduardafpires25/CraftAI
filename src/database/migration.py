from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from config.logger import logger


def run_migrations() -> None:
    project_root = Path(__file__).resolve().parents[2]
    alembic_ini = project_root / "alembic.ini"
    if not alembic_ini.exists():
        logger.warning("alembic.ini não encontrado em %s; pulando migrations.", alembic_ini)
        return

    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(project_root / "alembic"))
    logger.info("Executando migrations do Alembic...")
    command.upgrade(cfg, "head")
    logger.info("Migrations concluídas.")
