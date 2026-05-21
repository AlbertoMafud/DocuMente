"""Use case ArchivarDocumento — gestión de visibilidad y papelera.

Tres acciones soportadas (todas registran evento de audit + persisten):

- `archivar(doc_id, actor)`: marca el doc como archivado. Sigue siendo
  recuperable desde la pestaña "Archivados" del home.
- `desarchivar(doc_id, actor)`: revierte el archivado.
- `enviar_a_papelera(doc_id, actor, razon)`: marca el doc para purga a 30 días.
  Recuperable desde la pestaña "Papelera" mientras no expire.
- `restaurar_de_papelera(doc_id, actor)`: revierte papelera.
- `eliminar_permanente(doc_id, actor, *, es_admin)`: borra de la BD. Requiere
  `es_admin=True`. Quien no es admin recibe `PermissionError`.

El use case NO valida quién es admin — eso vive en la capa de auth (Fase A.1).
Acá solo se respeta el flag que viene del caller.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from src.core.models import Documento, EventoAuditoria
from src.storage.repositories import DocumentoRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadoVisibilidad:
    """Resultado de cualquier acción de visibilidad."""

    documento_id: UUID
    visibilidad_anterior: str
    visibilidad_nueva: str
    accion: str
    """`archivado` / `desarchivado` / `enviado_a_papelera` / `restaurado_de_papelera` / `eliminado_permanente`."""


class ArchivarDocumento:
    """Use case con todas las mutaciones de visibilidad."""

    def __init__(self, repo: DocumentoRepository) -> None:
        self.repo = repo

    def archivar(self, doc_id: UUID, actor: str, razon: str = "") -> ResultadoVisibilidad:
        doc = self._cargar_o_fallar(doc_id)
        if doc.archivado:
            return ResultadoVisibilidad(
                documento_id=doc_id,
                visibilidad_anterior=doc.visibilidad,
                visibilidad_nueva=doc.visibilidad,
                accion="archivado",
            )
        anterior = doc.visibilidad
        doc.archivado = True
        doc.archivado_en = datetime.now(UTC)
        doc.registrar_evento(
            EventoAuditoria(
                actor=actor,
                tipo="archivado",
                descripcion=f"Documento archivado por {actor}.",
                metadata={"razon": razon} if razon else {},
            )
        )
        self.repo.guardar(doc)
        return ResultadoVisibilidad(
            documento_id=doc_id,
            visibilidad_anterior=anterior,
            visibilidad_nueva=doc.visibilidad,
            accion="archivado",
        )

    def desarchivar(self, doc_id: UUID, actor: str) -> ResultadoVisibilidad:
        doc = self._cargar_o_fallar(doc_id)
        if not doc.archivado:
            return ResultadoVisibilidad(
                documento_id=doc_id,
                visibilidad_anterior=doc.visibilidad,
                visibilidad_nueva=doc.visibilidad,
                accion="desarchivado",
            )
        anterior = doc.visibilidad
        doc.archivado = False
        doc.archivado_en = datetime.now(UTC)
        doc.registrar_evento(
            EventoAuditoria(
                actor=actor,
                tipo="desarchivado",
                descripcion=f"Documento desarchivado por {actor}.",
            )
        )
        self.repo.guardar(doc)
        return ResultadoVisibilidad(
            documento_id=doc_id,
            visibilidad_anterior=anterior,
            visibilidad_nueva=doc.visibilidad,
            accion="desarchivado",
        )

    def enviar_a_papelera(self, doc_id: UUID, actor: str, razon: str = "") -> ResultadoVisibilidad:
        doc = self._cargar_o_fallar(doc_id)
        if doc.en_papelera:
            return ResultadoVisibilidad(
                documento_id=doc_id,
                visibilidad_anterior=doc.visibilidad,
                visibilidad_nueva=doc.visibilidad,
                accion="enviado_a_papelera",
            )
        anterior = doc.visibilidad
        doc.en_papelera = True
        doc.archivado_en = datetime.now(UTC)
        doc.registrar_evento(
            EventoAuditoria(
                actor=actor,
                tipo="enviado_a_papelera",
                descripcion=f"Documento movido a papelera por {actor}. Se purgará en 30 días si no se restaura.",
                metadata={"razon": razon} if razon else {},
            )
        )
        self.repo.guardar(doc)
        return ResultadoVisibilidad(
            documento_id=doc_id,
            visibilidad_anterior=anterior,
            visibilidad_nueva=doc.visibilidad,
            accion="enviado_a_papelera",
        )

    def restaurar_de_papelera(self, doc_id: UUID, actor: str) -> ResultadoVisibilidad:
        doc = self._cargar_o_fallar(doc_id)
        if not doc.en_papelera:
            return ResultadoVisibilidad(
                documento_id=doc_id,
                visibilidad_anterior=doc.visibilidad,
                visibilidad_nueva=doc.visibilidad,
                accion="restaurado_de_papelera",
            )
        anterior = doc.visibilidad
        doc.en_papelera = False
        doc.archivado_en = datetime.now(UTC)
        doc.registrar_evento(
            EventoAuditoria(
                actor=actor,
                tipo="restaurado_de_papelera",
                descripcion=f"Documento restaurado desde papelera por {actor}.",
            )
        )
        self.repo.guardar(doc)
        return ResultadoVisibilidad(
            documento_id=doc_id,
            visibilidad_anterior=anterior,
            visibilidad_nueva=doc.visibilidad,
            accion="restaurado_de_papelera",
        )

    def eliminar_permanente(
        self,
        doc_id: UUID,
        actor: str,
        *,
        es_admin: bool,
        razon: str = "",
    ) -> ResultadoVisibilidad:
        """Borra de la BD. SOLO accesible para admins.

        Levanta `PermissionError` si `es_admin=False`. El caller (UI o use case
        superior) es responsable de propagar el flag correcto desde la auth.
        """
        if not es_admin:
            raise PermissionError(
                "Solo un usuario admin puede eliminar permanentemente un documento."
            )
        doc = self._cargar_o_fallar(doc_id)
        anterior = doc.visibilidad
        # Registramos el evento ANTES de borrar — queda en logs estructurados
        # vía logger. La BD pierde el audit_trail al borrarse, intencionalmente.
        logger.info(
            "Eliminación permanente: doc_id=%s actor=%s anterior=%s razon=%r",
            doc_id,
            actor,
            anterior,
            razon,
        )
        self.repo.borrar(doc_id)
        return ResultadoVisibilidad(
            documento_id=doc_id,
            visibilidad_anterior=anterior,
            visibilidad_nueva="eliminado",
            accion="eliminado_permanente",
        )

    def _cargar_o_fallar(self, doc_id: UUID) -> Documento:
        doc = self.repo.obtener(doc_id)
        if doc is None:
            raise ValueError(f"Documento {doc_id} no encontrado.")
        return doc


def purgar_papelera_expirada(
    repo: DocumentoRepository,
    *,
    dias_retencion: int = 30,
    actor: str = "system",
) -> int:
    """Job idempotente que elimina documentos con `en_papelera=True` cuyo
    `archivado_en` esté antes de `now - dias_retencion`.

    Devuelve la cantidad de documentos purgados. Pensado para ejecutarse al
    boot de la app o en un cron.
    """
    expirados = repo.listar_papelera_expirada(dias_retencion=dias_retencion)
    if not expirados:
        return 0
    eliminados = 0
    for doc in expirados:
        logger.info(
            "Purgando documento automáticamente: doc_id=%s archivado_en=%s",
            doc.id,
            doc.archivado_en,
        )
        if repo.borrar(doc.id):
            eliminados += 1
    return eliminados
