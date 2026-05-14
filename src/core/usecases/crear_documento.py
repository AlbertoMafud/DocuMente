"""Use case: CrearDocumentoEnBlanco.

Crea un Documento esqueleto con las 28 secciones del template oficial NYL
todas vacías, metadata mínima, audit event 'documento_creado' y lo persiste.

Es el punto de entrada del flujo "desde cero" — paralelo a ImportarDocumento.

También acepta fuentes adicionales opcionales para que el flujo "desde cero"
también pueda pre-poblar secciones con borradores automáticos a partir de
material existente del usuario.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import IO

from src.core.models import Documento, EventoAuditoria, FuenteContexto
from src.core.models.documento import MetadataModelo
from src.core.template_catalog import construir_secciones_vacias
from src.core.usecases.sugerencias_multifuente import SugerenciasMultiFuente
from src.docs.readers import extraer_texto
from src.llm import LLMClient
from src.storage.repositories import DocumentoRepository


@dataclass
class CrearDocumentoEnBlanco:
    """Use case que crea un documento esqueleto y lo persiste."""

    repo: DocumentoRepository
    llm: LLMClient | None = None

    def ejecutar(
        self,
        nombre_modelo: str,
        model_id: str,
        user_id: str = "default",
        *,
        fuentes_adicionales: list[tuple[IO[bytes], str]] | None = None,
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

        if fuentes_adicionales:
            for archivo_fuente, nombre in fuentes_adicionales:
                try:
                    tipo, texto = extraer_texto(archivo_fuente, nombre)
                except (ValueError, Exception):
                    continue
                if texto.strip():
                    documento.fuentes_contexto.append(
                        FuenteContexto(
                            nombre_archivo=nombre,
                            tipo=tipo,
                            texto_extraido=texto,
                        )
                    )

        self.repo.guardar(documento)

        if self.llm is not None and documento.fuentes_contexto:
            rellenadas = SugerenciasMultiFuente(self.llm).ejecutar(documento)
            if rellenadas > 0:
                self.repo.guardar(documento)

        return documento
