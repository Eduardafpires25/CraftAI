from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO, Optional


@dataclass
class StoredFile:
    """Metadados de um arquivo armazenado."""
    key: str           # Caminho/chave interna (ex.: "users/abc/avatar.png")
    url: str           # URL publica para acessar
    size_bytes: int
    content_type: str


class StorageBackend(ABC):
    """
    Interface abstrata para backends de armazenamento de arquivos.

    Implementacoes:
      - LocalStorage: filesystem local
      - S3Storage: AWS S3, DigitalOcean Spaces, MinIO (qualquer S3-compatible)
    """

    @abstractmethod
    def save(
        self,
        key: str,
        file: BinaryIO,
        content_type: str = "application/octet-stream",
        public: bool = True,
    ) -> StoredFile:
        """
        Salva arquivo no storage.
        - key: caminho/chave (ex.: "users/abc-123/avatar.png")
        - file: stream binaria do arquivo
        - content_type: MIME type
        - public: se True, gera URL publica
        """

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove arquivo. Retorna True se removido, False se nao existia."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Verifica se arquivo existe."""

    @abstractmethod
    def get_url(self, key: str) -> str:
        """Retorna URL publica para acessar o arquivo."""

    @abstractmethod
    def get_signed_url(self, key: str, expires_seconds: int = 3600) -> str:
        """
        Retorna URL assinada com tempo de expiracao (para arquivos privados).
        Backends que nao suportam (local) podem retornar a URL publica.
        """

    @abstractmethod
    def open(self, key: str) -> BinaryIO:
        """Abre arquivo para leitura. Lanca FileNotFoundError se nao existir."""
