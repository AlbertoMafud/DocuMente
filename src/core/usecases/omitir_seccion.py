"""Use case OmitirSeccion — marca una sección como deliberadamente omitida.

Una sección omitida queda explícitamente justificada con motivo capturado del
usuario y registrada en el audit_trail. Para la state machine, una sección
omitida cuenta como "resuelta" (ya no bloquea la transición a in_review).

Diseño: omitir es una decisión documentada del usuario, no un olvido. Por eso
exigimos motivo no vacío y lo persistimos tanto en la sección como en el
audit event para auditabilidad.
"""

from __future__ import annotations

from typing import Final
from uuid import UUID

from src.core.models import EventoAuditoria
from src.storage.repositories import DocumentoRepository

MOTIVOS_OMISION: Final[list[str]] = [
    "No aplica al modelo",
    "Información no disponible",
    "Pendiente para versión futura",
    "Otro (especificar)",
]


class OmitirSeccion:
    """Use case: marcar una sección como omitida con motivo justificado."""

    def __init__(self, doc_repo: DocumentoRepository) -> None:
        self.doc_repo = doc_repo

    def ejecutar(
        self,
        documento_id: UUID,
        *,
        seccion_id: str,
        motivo: str,
        actor: str,
    ) -> None:
        if not motivo or not motivo.strip():
            raise ValueError(
                "El motivo de omisión no puede estar vacío. "
                "Una sección omitida requiere justificación documentada."
            )

        documento = self.doc_repo.obtener(documento_id)
        if documento is None:
            raise ValueError(f"Documento {documento_id} no encontrado.")

        seccion = documento.seccion_por_id(seccion_id)
        if seccion is None:
            raise ValueError(f"Sección '{seccion_id}' no existe en el documento.")

        seccion.completitud = "omitida"
        seccion.motivo_omision = motivo.strip()

        documento.registrar_evento(
            EventoAuditoria(
                actor=actor,
                tipo="seccion_omitida",
                descripcion=(
                    f"Sección '{seccion.numero} {seccion.nombre}' marcada como "
                    f"omitida. Motivo: {motivo.strip()}"
                ),
                seccion_id=seccion_id,
                metadata={"motivo": motivo.strip()},
            )
        )

        self.doc_repo.guardar(documento)
