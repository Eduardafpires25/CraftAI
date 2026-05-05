from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class AIError(Exception):
    """Erro genérico do módulo de IA."""


@dataclass
class GeneratedIterationImage:
    """Bytes da imagem gerada (placeholder ou IA real) prontos para upload."""
    image_bytes: bytes
    content_type: str
    prompt: str
    model: str
    duration_ms: int
    cost_usd: Optional[float] = None


class ImageGenerationResult(BaseModel):
    """Resultado de uma geração de imagem."""

    model: str
    prompt: str
    revised_prompt: Optional[str] = None
    # Apenas um dos dois deve estar preenchido, dependendo do response_format do provider
    url: Optional[str] = None
    b64_json: Optional[str] = Field(
        default=None,
        description="Imagem codificada em base64 quando o provider retorna bytes inline.",
    )
    size: Optional[str] = None
    duration_ms: Optional[int] = None
    raw: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Payload bruto retornado pelo provider (para auditoria).",
        exclude=True,
    )


class CompletionResult(BaseModel, Generic[T]):
    """Resultado de uma completion estruturada (parsed em um schema Pydantic)."""

    model: str
    parsed: T
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    duration_ms: Optional[int] = None
    raw: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
