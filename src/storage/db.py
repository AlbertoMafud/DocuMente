"""Configuración de SQLAlchemy + esquema de tablas.

Decisiones que pagan dividendos en la migración a EC2:
- URL de la base viene de `.env` (variable `DATABASE_URL`); cambiar de SQLite
  a PostgreSQL solo requiere cambiar el valor de la variable.
- El modelo `DocumentoRow` guarda el JSON serializado del Documento Pydantic
  completo. Esto evita tener que mantener un esquema relacional paralelo al
  modelo de dominio durante el MVP (más rápido, más flexible). Cuando el
  schema sea estable, podemos refactor a tablas relacionales si se justifica.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Boolean, Column, DateTime, String, Text, create_engine, inspect, text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

logger = logging.getLogger(__name__)


def _resolver_database_url() -> str:
    """Lee DATABASE_URL del entorno o cae a SQLite local."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    # Default: SQLite en data/documente.db relativo al proyecto.
    proyecto_dir = Path(__file__).resolve().parent.parent.parent
    db_path = proyecto_dir / "data" / "documente.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


class Base(DeclarativeBase):
    """Base declarativa de SQLAlchemy."""


class DocumentoRow(Base):
    """Tabla de documentos. Guarda el Pydantic Documento serializado a JSON."""

    __tablename__ = "documentos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    tipo: Mapped[str] = mapped_column(String(32), default="model_development")
    estado: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    nombre_modelo: Mapped[str] = mapped_column(String(256), default="")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    # Columnas de visibilidad (Fase A.5).
    archivado: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    en_papelera: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    # `archivado_en` es nullable y SQLAlchemy en Python 3.14 tiene un quirk con
    # `Mapped[datetime | None]` — usamos la forma Column clásica (sin Mapped)
    # que sigue siendo válida en SQLAlchemy 2.x.
    archivado_en = Column(DateTime, nullable=True, default=None)


class EstadoEntrevistaRow(Base):
    """Tabla de estados conversacionales de entrevista, uno por (documento, sección)."""

    __tablename__ = "estados_entrevista"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    """Clave compuesta: '{documento_id}::{seccion_id}'."""
    documento_id: Mapped[str] = mapped_column(String(36), index=True)
    seccion_id: Mapped[str] = mapped_column(String(64), index=True)
    cerrada: Mapped[bool] = mapped_column(default=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    actualizada_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


class VersionRow(Base):
    """Tabla de versiones (snapshots inmutables del Documento) — Fase C.2."""

    __tablename__ = "versiones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    documento_id: Mapped[str] = mapped_column(String(36), index=True)
    numero: Mapped[int] = mapped_column(default=1)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    hash_contenido: Mapped[str] = mapped_column(String(64), index=True)
    comentario: Mapped[str] = mapped_column(Text, default="")
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine():  # type: ignore[no-untyped-def]
    """Devuelve el engine de SQLAlchemy (lazy-init)."""
    global _engine
    if _engine is None:
        _engine = create_engine(_resolver_database_url(), echo=False, future=True)
        Base.metadata.create_all(_engine)
        _aplicar_migraciones_aditivas(_engine)
    return _engine


def _aplicar_migraciones_aditivas(engine) -> None:  # type: ignore[no-untyped-def]
    """Aplica migraciones aditivas idempotentes al boot.

    NUNCA destructivas — solo `ALTER TABLE ... ADD COLUMN` con default seguro.
    Si la columna ya existe, se ignora. Esto cubre BD viejas creadas antes
    de que se agregaran columnas nuevas.

    Migraciones aplicadas:
    - Fase A.5: columnas `archivado`, `en_papelera`, `archivado_en` en `documentos`.
    """
    inspector = inspect(engine)
    if "documentos" not in inspector.get_table_names():
        return  # tabla aún no existe (no debería pasar tras create_all)

    cols_existentes = {col["name"] for col in inspector.get_columns("documentos")}
    migraciones: list[tuple[str, str]] = [
        # (nombre_columna, DDL para agregarla)
        ("archivado", "ALTER TABLE documentos ADD COLUMN archivado BOOLEAN NOT NULL DEFAULT 0"),
        (
            "en_papelera",
            "ALTER TABLE documentos ADD COLUMN en_papelera BOOLEAN NOT NULL DEFAULT 0",
        ),
        ("archivado_en", "ALTER TABLE documentos ADD COLUMN archivado_en DATETIME"),
    ]

    with engine.connect() as conn:
        for nombre_col, ddl in migraciones:
            if nombre_col not in cols_existentes:
                try:
                    conn.execute(text(ddl))
                    conn.commit()
                    logger.info("Migración aditiva aplicada: columna '%s' agregada.", nombre_col)
                except Exception as exc:
                    logger.warning(
                        "No se pudo aplicar migración aditiva '%s' (%s) — "
                        "puede que ya esté aplicada en otra conexión.",
                        nombre_col,
                        exc.__class__.__name__,
                    )


def get_session_factory() -> sessionmaker[Session]:
    """Devuelve la session factory (lazy-init)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager que abre una sesión y hace commit/rollback automático."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
