from __future__ import annotations

import io
from typing import BinaryIO, Optional

from config.logger import logger
from src.storage.base import StorageBackend, StoredFile


class S3Storage(StorageBackend):
    """
    Storage backend para S3 / DigitalOcean Spaces / MinIO.
    Qualquer servico S3-compatible funciona.
    """

    def __init__(
        self,
        bucket: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        endpoint_url: Optional[str] = None,
        public_url_base: str = "",
        default_acl: str = "public-read",
    ) -> None:
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise ImportError(
                "boto3 nao instalado. Instale com: pip install boto3"
            )

        self.bucket = bucket
        self.endpoint_url = endpoint_url
        self.region = region
        self.default_acl = default_acl
        self.public_url_base = public_url_base.rstrip("/") if public_url_base else ""

        self.client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )
        logger.info(
            "S3Storage inicializado: bucket=%s, endpoint=%s",
            bucket,
            endpoint_url or "AWS",
        )

    def _default_public_url(self, key: str) -> str:
        """Constroi URL publica padrao quando public_url_base nao foi configurado."""
        key = key.lstrip("/")
        if self.endpoint_url:
            # Spaces/MinIO: https://{endpoint}/{bucket}/{key}
            base = self.endpoint_url.rstrip("/")
            return f"{base}/{self.bucket}/{key}"
        # AWS S3 padrao
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

    def save(
        self,
        key: str,
        file: BinaryIO,
        content_type: str = "application/octet-stream",
        public: bool = True,
    ) -> StoredFile:
        try:
            file.seek(0)
        except Exception:
            pass

        # Le tudo pra calcular tamanho (e pq boto3 precisa de bytes seekable)
        data = file.read()
        size = len(data)

        extra: dict = {"ContentType": content_type}
        if public:
            extra["ACL"] = self.default_acl

        self.client.put_object(
            Bucket=self.bucket,
            Key=key.lstrip("/"),
            Body=data,
            **extra,
        )

        logger.info("Arquivo salvo (s3): %s (%d bytes)", key, size)
        return StoredFile(
            key=key,
            url=self.get_url(key),
            size_bytes=size,
            content_type=content_type,
        )

    def delete(self, key: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key.lstrip("/"))
            logger.info("Arquivo removido (s3): %s", key)
            return True
        except Exception as e:
            logger.warning("Erro ao remover %s: %s", key, e)
            return False

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key.lstrip("/"))
            return True
        except Exception:
            return False

    def get_url(self, key: str) -> str:
        key = key.lstrip("/")
        if self.public_url_base:
            return f"{self.public_url_base}/{key}"
        return self._default_public_url(key)

    def get_signed_url(self, key: str, expires_seconds: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key.lstrip("/")},
            ExpiresIn=expires_seconds,
        )

    def open(self, key: str) -> BinaryIO:
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=key.lstrip("/"))
            return io.BytesIO(obj["Body"].read())
        except self.client.exceptions.NoSuchKey:
            raise FileNotFoundError(f"Arquivo nao encontrado: {key}")
