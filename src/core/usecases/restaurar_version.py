"""Use case RestaurarVersion — sobrescribe el documento activo con un snapshot.

Antes de sobrescribir, crea automáticamente un snapshot del estado actual
con comentario "Pre-restore from vN" para que el usuario NO pierda
trabajo no versionado. Después carga el snapshot JSON de la versión
seleccionada como el nuevo estado activo y registra evento
`version_restaurada` en el audit_trail del documento.

Idempotencia: si el documento actual ya es idéntico al snapshot vN
(mismo contenido material), el snapshot pre-restore se omite (vía
idempotencia natural de CrearVersion) y la "restauración" es no-op a
nivel datos — pero igual se registra evento de audit.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from src.core.models import Documento, EventoAuditoria, Version
from src.core.usecases.crear_version import CrearVersion
from src.storage.repositories import DocumentoRepository, VersionRepository

logger = logging.getLogger(__name__)


class VersionNoEncontrada(ValueError):
    """Se intentó restaurar una versión que no existe para ese documento."""


@dataclass(frozen=True)
class ResultadoRestaurar:
    """Resultado de la restauración."""

    documento: Documento
    """Estado del documento DESPUÉS de restaurar (contenido de la versión)."""

    version_restaurada: Version
    """La versión que se cargó como estado activo."""

    snapshot_pre_restore: Version | None
    """La versión auto-creada antes de sobrescribir (None si era idempotente)."""


class RestaurarVersion:
    """Use case: vuelve el documento activo al contenido de una versión N."""

    def __init__(
        self,
        doc_repo: DocumentoRepository,
        version_repo: VersionRepository,
    ) -> None:
        self.doc_repo = doc_repo
        self.version_repo = version_repo

    def ejecutar(
        self,
        documento_id: UUID,
        numero_version: int,
        *,
        actor: str = "default",
    ) -> ResultadoRestaurar:
        documento_actual = self.doc_repo.obtener(documento_id)
        if documento_actual is None:
            raise ValueError(f"Documento {documento_id} no encontrado.")

        version_destino = self.version_repo.por_doc_y_numero(documento_id, numero_version)
        if version_destino is None:
            raise VersionNoEncontrada(f"El documento no tiene una versión v{numero_version}.")

        # 1. Snapshot automático del estado actual ANTES de sobrescribir
        crear_uc = CrearVersion(doc_repo=self.doc_repo, version_repo=self.version_repo)
        resultado_pre = crear_uc.ejecutar(
            documento_actual,
            comentario=f"Pre-restore from v{numero_version}",
            actor=actor,
        )
        snapshot_pre = None if resultado_pre.es_duplicado else resultado_pre.version

        # 2. Hidratar el documento desde el snapshot_json de la versión destino
        documento_restaurado = Documento.model_validate_json(version_destino.snapshot_json)

        # Conservar el audit_trail acumulado del documento actual + sumar el evento
        # de restauración. Hidratar desde el snapshot trae el audit_trail viejo,
        # que NO queremos perder de la historia.
        documento_restaurado.audit_trail = list(documento_actual.audit_trail)
        documento_restaurado.registrar_evento(
            EventoAuditoria(
                actor=actor,
                tipo="version_restaurada",
                descripcion=(
                    f"Documento restaurado al contenido de v{numero_version}"
                    + (
                        f" — comentario original: {version_destino.comentario}"
                        if version_destino.comentario
                        else ""
                    )
                ),
                metadata={
                    "version_origen_numero": str(numero_version),
                    "version_origen_id": str(version_destino.id),
                    "snapshot_pre_restore_id": (str(snapshot_pre.id) if snapshot_pre else ""),
                },
            )
        )

        self.doc_repo.guardar(documento_restaurado)

        return ResultadoRestaurar(
            documento=documento_restaurado,
            version_restaurada=version_destino,
            snapshot_pre_restore=snapshot_pre,
        )


__all__ = ["RestaurarVersion", "ResultadoRestaurar", "VersionNoEncontrada"]
