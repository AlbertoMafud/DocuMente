"""Dependency injection para la API.

FastAPI's `Depends` consume estos providers para inyectar repos y clients
en cada handler. Centralizando aquí evita repetir instanciación + facilita
mock en tests.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends

from src.config import Settings, get_settings
from src.llm import AnthropicClient
from src.storage.repositories import (
    DocumentoRepository,
    EstadoEntrevistaRepository,
    VersionRepository,
)


def get_doc_repo() -> Generator[DocumentoRepository, None, None]:
    """Provee un DocumentoRepository por request."""
    yield DocumentoRepository()


def get_entrevista_repo() -> Generator[EstadoEntrevistaRepository, None, None]:
    """Provee un EstadoEntrevistaRepository por request."""
    yield EstadoEntrevistaRepository()


def get_version_repo() -> Generator[VersionRepository, None, None]:
    """Provee un VersionRepository por request."""
    yield VersionRepository()


def get_llm_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnthropicClient | None:
    """Devuelve un AnthropicClient si hay API key configurada, None si no.

    Los use cases que requieran LLM deben validar `if llm is None` y manejar
    el caso gracefully (ej. ExportarDocumento sin polish, entrevista con
    error claro).
    """
    if not settings.anthropic_api_key:
        return None
    return AnthropicClient()


DocRepoDep = Annotated[DocumentoRepository, Depends(get_doc_repo)]
EntrevistaRepoDep = Annotated[EstadoEntrevistaRepository, Depends(get_entrevista_repo)]
VersionRepoDep = Annotated[VersionRepository, Depends(get_version_repo)]
LlmClientDep = Annotated[AnthropicClient | None, Depends(get_llm_client)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
