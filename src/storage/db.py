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

import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import DateTime, String, Text, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)


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


_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine():  # type: ignore[no-untyped-def]
    """Devuelve el engine de SQLAlchemy (lazy-init)."""
    global _engine
    if _engine is None:
        _engine = create_engine(_resolver_database_url(), echo=False, future=True)
        Base.metadata.create_all(_engine)
    return _engine


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
