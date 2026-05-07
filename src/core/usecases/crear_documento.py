"""Use case: CrearDocumentoEnBlanco.

Crea un Documento esqueleto con las 32 secciones del template oficial NYL
todas vacías, metadata mínima, audit event 'documento_creado' y lo persiste.

Es el punto de entrada del flujo "desde cero" — paralelo a ImportarDocumento.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from src.core.models import Documento, EventoAuditoria
from src.core.models.documento import MetadataModelo
from src.core.template_catalog import construir_secciones_vacias
from src.storage.repositories import DocumentoRepository


@dataclass
class CrearDocumentoEnBlanco:
    """Use case que crea un documento esqueleto y lo persiste."""

    repo: DocumentoRepository

    def ejecutar(
        self,
        nombre_modelo: str,
        model_id: str,
        user_id: str = "default",
    ) -> Documento:
        nombre_clean = nombre_modelo.strip()
        model_id_clean = model_id.strip()
        if not nombre_clean:
            raise ValueError("nombre_modelo no puede estar vacío.")
        if not model_id_clean:
            raise ValueError("model_id no puede estar vacío.")

        documento = Documento(
            user_id=user_id,
            metadata_modelo=MetadataModelo(
                nombre_modelo=nombre_clean,
                model_id=model_id_clean,
            ),
            secciones=construir_secciones_vacias(),
        )
        documento.registrar_evento(
            EventoAuditoria(
                timestamp=datetime.now(UTC),
                actor=user_id,
                tipo="documento_creado",
                descripcion=f"Documento creado desde cero: {nombre_clean}",
                metadata={"model_id": model_id_clean},
            )
        )
        self.repo.guardar(documento)
        return documento
