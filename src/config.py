"""Configuración centralizada (pydantic-settings).

Lee variables de entorno desde `.env` y las expone tipadas a la app.
Cambiar de local a EC2 = cambiar valores de env, no código.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Configuración global de DocuMente."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    anthropic_api_key: str = Field(default="", description="Llave de API de Anthropic.")
    claude_model: str = Field(
        default="claude-opus-4-7",
        description=(
            "Modelo de Claude a usar para drafting / entrevista. "
            "Opus 4.7 = más capable, adaptive thinking only, sin temperature."
        ),
    )

    # Persistencia
    database_url: str = Field(
        default=f"sqlite:///{PROJECT_ROOT / 'data' / 'documente.db'}",
        description="URL de SQLAlchemy. Cambia a postgresql://... al migrar.",
    )
    exports_path: str = Field(
        default=str(PROJECT_ROOT / "data"),
        description="Path de Storage local. Al migrar: bucket S3.",
    )

    # App
    user_id: str = Field(
        default="default",
        description="ID del usuario actual (single-user en MVP).",
    )
    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    """Devuelve la instancia singleton de Settings."""
    return Settings()
