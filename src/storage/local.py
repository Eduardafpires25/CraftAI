from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import BinaryIO

from config.logger import logger
from src.storage.base import StorageBackend, StoredFile


class LocalStorage(StorageBackend):
    """Storage backend usando filesystem local."""

    def __init__(self, base_path: str, public_url_base: str) -> None:
        self.base_path = Path(base_path).resolve()
        self.public_url_base = public_url_base.rstrip("/")
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info("LocalStorage inicializado em: %s", self.base_path)

    def _full_path(self, key: str) -> Path:
        # Normaliza e protege contra path traversal
        key_path = Path(key.lstrip("/"))
        full = (self.base_path / key_path).resolve()
        if not str(full).startswith(str(self.base_path)):
            raise ValueError(f"Caminho invalido (path traversal): {key}")
        return full

    def save(
        self,
        key: str,
        file: BinaryIO,
        content_type: str = "application/octet-stream",
        public: bool = True,
    ) -> StoredFile:
        full = self._full_path(key)
        full.parent.mkdir(parents=True, exist_ok=True)

        # Reset cursor se possivel
        try:
            file.seek(0)
        except Exception:
            pass

        with open(full, "wb") as out:
            shutil.copyfileobj(file, out)

        size = full.stat().st_size
        logger.info("Arquivo salvo (local): %s (%d bytes)", key, size)

        return StoredFile(
            key=key,
            url=self.get_url(key),
            size_bytes=size,
            content_type=content_type,
        )

    def delete(self, key: str) -> bool:
        full = self._full_path(key)
        if full.exists():
            full.unlink()
            logger.info("Arquivo removido (local): %s", key)
            return True
        return False

    def exists(self, key: str) -> bool:
        return self._full_path(key).exists()

    def get_url(self, key: str) -> str:
        return f"{self.public_url_base}/{key.lstrip('/')}"

    def get_signed_url(self, key: str, expires_seconds: int = 3600) -> str:
        # Local nao tem URLs assinadas; retorna a URL publica
        return self.get_url(key)

    def open(self, key: str) -> BinaryIO:
        full = self._full_path(key)
        if not full.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {key}")
        return open(full, "rb")
