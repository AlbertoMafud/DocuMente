"""Lector de TXT — devuelve el contenido como string UTF-8 con fallback latin-1."""

from __future__ import annotations

from typing import IO


def leer_txt(archivo: IO[bytes]) -> str:
    """Lee el archivo como UTF-8; si falla, intenta latin-1 antes de rendirse."""
    archivo.seek(0)
    raw = archivo.read()
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")
