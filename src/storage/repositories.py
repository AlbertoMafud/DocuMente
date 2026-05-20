"""Repository pattern para Documento y EstadoEntrevista.

Aísla la lógica de negocio de SQLAlchemy. Migrar de SQLite a PostgreSQL
implica solo cambiar `DATABASE_URL` en `.env` — estas clases no cambian.

Visibilidad (Fase A.5):
- `listar_por_usuario` filtra `archivado=False` y `en_papelera=False` por
  default. Use `incluir_archivados=True` o `solo_papelera=True` para casos
  específicos (vistas de "Archivados", "Papelera", "Admin papelera").
- Las mutaciones de visibilidad (`archivar`, `desarchivar`, etc.) son
  métodos finitos del repositorio. La lógica de orquestación + audit event
  vive en `src/core/usecases/archivar_documento.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select

from src.core.models import Documento, EstadoEntrevista
from src.storage.db import DocumentoRow, EstadoEntrevistaRow, session_scope


class DocumentoRepository:
    """Persistencia de documentos en SQLAlchemy."""

    def guardar(self, documento: Documento) -> None:
        """Inserta o actualiza un Documento."""
        documento.actualizado_en = datetime.now(UTC)
        payload = documento.model_dump_json()
        with session_scope() as s:
            row = s.get(DocumentoRow, str(documento.id))
            if row is None:
                s.add(
                    DocumentoRow(
                        id=str(documento.id),
                        user_id=documento.user_id,
                        tipo=documento.tipo,
                        estado=documento.estado,
                        nombre_modelo=documento.metadata_modelo.nombre_modelo,
                        payload_json=payload,
                        creado_en=documento.creado_en,
                        actualizado_en=documento.actualizado_en,
                        archivado=documento.archivado,
                        en_papelera=documento.en_papelera,
                        archivado_en=documento.archivado_en,
                    )
                )
            else:
                row.user_id = documento.user_id
                row.tipo = documento.tipo
                row.estado = documento.estado
                row.nombre_modelo = documento.metadata_modelo.nombre_modelo
                row.payload_json = payload
                row.actualizado_en = documento.actualizado_en
                row.archivado = documento.archivado
                row.en_papelera = documento.en_papelera
                row.archivado_en = documento.archivado_en

    def obtener(self, documento_id: UUID) -> Documento | None:
        """Devuelve el Documento o None si no existe."""
        with session_scope() as s:
            row = s.get(DocumentoRow, str(documento_id))
            if row is None:
                return None
            return Documento.model_validate_json(row.payload_json)

    def listar_por_usuario(
        self,
        user_id: str = "default",
        *,
        incluir_archivados: bool = False,
        solo_papelera: bool = False,
    ) -> list[Documento]:
        """Lista documentos de un usuario, ordenados por más reciente.

        Default: solo activos (no archivados, no en papelera). Útil para home.
        - `incluir_archivados=True`: incluye archivados, excluye papelera.
        - `solo_papelera=True`: SOLO los que están en papelera.
        """
        with session_scope() as s:
            stmt = (
                select(DocumentoRow)
                .where(DocumentoRow.user_id == user_id)
                .order_by(DocumentoRow.actualizado_en.desc())
            )
            if solo_papelera:
                stmt = stmt.where(DocumentoRow.en_papelera.is_(True))
            else:
                stmt = stmt.where(DocumentoRow.en_papelera.is_(False))
                if not incluir_archivados:
                    stmt = stmt.where(DocumentoRow.archivado.is_(False))
            rows = s.execute(stmt).scalars().all()
            return [Documento.model_validate_json(r.payload_json) for r in rows]

    def listar_papelera_global(self) -> list[Documento]:
        """Solo para admins: lista TODOS los documentos en papelera, todos los users."""
        with session_scope() as s:
            stmt = (
                select(DocumentoRow)
                .where(DocumentoRow.en_papelera.is_(True))
                .order_by(DocumentoRow.actualizado_en.desc())
            )
            rows = s.execute(stmt).scalars().all()
            return [Documento.model_validate_json(r.payload_json) for r in rows]

    def listar_papelera_expirada(self, dias_retencion: int = 30) -> list[Documento]:
        """Lista documentos en papelera con `archivado_en` antes del cutoff.

        Útil para el job de purge automática.
        """
        cutoff = datetime.now(UTC) - timedelta(days=dias_retencion)
        with session_scope() as s:
            stmt = select(DocumentoRow).where(
                DocumentoRow.en_papelera.is_(True),
                DocumentoRow.archivado_en.isnot(None),
                DocumentoRow.archivado_en < cutoff,
            )
            rows = s.execute(stmt).scalars().all()
            return [Documento.model_validate_json(r.payload_json) for r in rows]

    def borrar(self, documento_id: UUID) -> bool:
        """Borra el documento. Devuelve True si existía, False si no."""
        with session_scope() as s:
            row = s.get(DocumentoRow, str(documento_id))
            if row is None:
                return False
            s.delete(row)
            return True


def _id_compuesto(documento_id: str, seccion_id: str) -> str:
    return f"{documento_id}::{seccion_id}"


class EstadoEntrevistaRepository:
    """Persistencia de estados conversacionales por (documento, sección)."""

    def guardar(self, estado: EstadoEntrevista) -> None:
        estado.actualizada_en = datetime.now(UTC)
        payload = estado.model_dump_json()
        cid = _id_compuesto(estado.documento_id, estado.seccion_id)
        with session_scope() as s:
            row = s.get(EstadoEntrevistaRow, cid)
            if row is None:
                s.add(
                    EstadoEntrevistaRow(
                        id=cid,
                        documento_id=estado.documento_id,
                        seccion_id=estado.seccion_id,
                        cerrada=estado.cerrada,
                        payload_json=payload,
                        actualizada_en=estado.actualizada_en,
                    )
                )
            else:
                row.cerrada = estado.cerrada
                row.payload_json = payload
                row.actualizada_en = estado.actualizada_en

    def obtener(self, documento_id: str, seccion_id: str) -> EstadoEntrevista | None:
        cid = _id_compuesto(documento_id, seccion_id)
        with session_scope() as s:
            row = s.get(EstadoEntrevistaRow, cid)
            if row is None:
                return None
            return EstadoEntrevista.model_validate_json(row.payload_json)

    def borrar(self, documento_id: str, seccion_id: str) -> bool:
        cid = _id_compuesto(documento_id, seccion_id)
        with session_scope() as s:
            row = s.get(EstadoEntrevistaRow, cid)
            if row is None:
                return False
            s.delete(row)
            return True
