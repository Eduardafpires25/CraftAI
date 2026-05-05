"""
Geradores de imagens placeholder (sem chamadas a IA externa).
Usados em desenvolvimento para evitar custos com OpenAI.
"""
from __future__ import annotations

import struct
import zlib
from typing import Optional


def _png_chunk(name: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + name
        + data
        + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
    )


def generate_solid_color_png(
    width: int = 512,
    height: int = 512,
    color: tuple[int, int, int] = (0, 255, 0),
) -> bytes:
    """Gera PNG 8-bit RGB de uma cor solida."""
    signature = b"\x89PNG\r\n\x1a\n"
    # IHDR: width, height, bit_depth=8, color_type=2 (RGB), compression, filter, interlace
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    pixel = bytes(color)
    row = b"\x00" + (pixel * width)  # filter=None + pixels
    raw = row * height
    idat = zlib.compress(raw, 9)

    return (
        signature
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", idat)
        + _png_chunk(b"IEND", b"")
    )


# Cache em memoria do PNG verde (uniforme, gerado uma vez)
_GREEN_CACHE: Optional[bytes] = None


def get_green_placeholder(width: int = 512, height: int = 512) -> bytes:
    """Retorna PNG 512x512 verde (#00FF00) cacheado em memoria."""
    global _GREEN_CACHE
    if _GREEN_CACHE is None:
        _GREEN_CACHE = generate_solid_color_png(width, height, (0, 255, 0))
    return _GREEN_CACHE
