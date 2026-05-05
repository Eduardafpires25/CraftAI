from __future__ import annotations

from functools import lru_cache

from config.logger import logger
from config.settings import settings
from src.storage.base import StorageBackend


@lru_cache(maxsize=1)
def get_storage() -> StorageBackend:
    """
    Retorna a instancia (singleton) do storage configurado.
    Backend escolhido via STORAGE_BACKEND no .env (local | s3).
    """
    backend = settings.STORAGE_BACKEND.lower().strip()

    if backend == "local":
        from src.storage.local import LocalStorage
        return LocalStorage(
            base_path=settings.IMAGES_DIR,
            public_url_base=settings.STORAGE_PUBLIC_URL_BASE,
        )

    if backend in ("s3", "spaces"):
        from src.storage.s3 import S3Storage
        if not settings.S3_BUCKET:
            raise ValueError("S3_BUCKET nao configurado no .env")
        return S3Storage(
            bucket=settings.S3_BUCKET,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            region=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL,
            public_url_base=settings.S3_PUBLIC_URL_BASE,
            default_acl=settings.S3_DEFAULT_ACL,
        )

    raise ValueError(
        f"STORAGE_BACKEND invalido: '{backend}'. Use 'local' ou 's3'."
    )
