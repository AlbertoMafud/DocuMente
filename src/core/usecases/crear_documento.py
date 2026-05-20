"""Use case: CrearDocumentoEnBlanco.

Crea un Documento esqueleto con las 28 secciones del template oficial NYL
todas vacías, metadata mínima, audit event 'documento_creado' y lo persiste.

Es el punto de entrada del flujo "desde cero" — paralelo a ImportarDocumento.

También acepta fuentes adicionales opcionales para que el flujo "desde cero"
también pueda pre-poblar secciones con borradores automáticos a partir de
material existente del usuario. Los problemas en la extracción de fuentes
o en la generación LLM se propagan al `ResultadoCrearDocumento` para que la
UI los muestre — nunca se suprimen silenciosamente.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import IO

from src.core.models import Documento, EventoAuditoria, FuenteContexto
from src.core.models.documento import MetadataModelo
from src.core.template_catalog import construir_secciones_vacias
from src.core.usecases.sugerencias_multifuente import (
    ResultadoSugerencias,
    SugerenciasMultiFuente,
)
from src.docs.readers import extraer_texto
from src.llm import LLMClient
from src.storage.repositories import DocumentoRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadoCrearDocumento:
    """Resultado del flujo de creación desde cero.

    Attributes:
        documento: el documento creado y persistido.
        fuentes_extraidas: cantidad de fuentes adicionales cargadas como contexto.
        fuentes_descartadas: lista de nombres de archivos que fallaron al extraer texto.
        sugerencias: resultado del paso SugerenciasMultiFuente (puede ser None si
            no se intentó — LLM ausente o sin fuentes).
        llm_disponible: True si el cliente LLM se pudo construir.
        advertencias: lista de mensajes para mostrar al usuario en la UI.
    """

    documento: Documento
    fuentes_extraidas: int = 0
    fuentes_descartadas: list[str] = field(default_factory=list)
    sugerencias: ResultadoSugerencias | None = None
    llm_disponible: bool = True
    advertencias: list[str] = field(default_factory=list)

    @property
    def secciones_prellenadas(self) -> int:
        return self.sugerencias.secciones_pobladas if self.sugerencias else 0


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
    ) -> ResultadoCrearDocumento:
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

        advertencias: list[str] = []
        fuentes_descartadas: list[str] = []
        if fuentes_adicionales:
            for archivo_fuente, nombre in fuentes_adicionales:
                try:
                    tipo, texto = extraer_texto(archivo_fuente, nombre)
                except Exception as exc:
                    logger.warning(
                        "No se pudo extraer texto de fuente '%s': %s",
                        nombre,
                        exc,
                        exc_info=True,
                    )
                    fuentes_descartadas.append(nombre)
                    continue
                if texto.strip():
                    documento.fuentes_contexto.append(
                        FuenteContexto(
                            nombre_archivo=nombre,
                            tipo=tipo,
                            texto_extraido=texto,
                        )
                    )
                else:
                    fuentes_descartadas.append(nombre)

        self.repo.guardar(documento)

        sugerencias: ResultadoSugerencias | None = None
        llm_disponible = self.llm is not None
        if not llm_disponible and documento.fuentes_contexto:
            advertencias.append(
                "Cargaste fuentes pero el asistente de IA no está disponible — "
                "se guardaron como contexto, pero no se generaron borradores automáticos."
            )

        if self.llm is not None and documento.fuentes_contexto:
            sugerencias = SugerenciasMultiFuente(self.llm).ejecutar(documento)
            if sugerencias.secciones_pobladas > 0:
                self.repo.guardar(documento)
            if sugerencias.hubo_errores:
                advertencias.append(
                    f"Algunas secciones no se pudieron prellenar "
                    f"({len(sugerencias.errores)} error(es) al llamar al LLM)."
                )

        if fuentes_descartadas:
            advertencias.append(f"No se pudo leer texto útil de: {', '.join(fuentes_descartadas)}.")

        return ResultadoCrearDocumento(
            documento=documento,
            fuentes_extraidas=len(documento.fuentes_contexto),
            fuentes_descartadas=fuentes_descartadas,
            sugerencias=sugerencias,
            llm_disponible=llm_disponible,
            advertencias=advertencias,
        )
