"""Use case: ImportarDocumento.

Orquesta el flujo completo de importar un .docx existente:
1. Guardar el archivo subido en `Storage`.
2. Parsearlo con `DocxReader`.
3. Persistir el `Documento` resultante con `DocumentoRepository`.
4. (Opcional) Procesar fuentes adicionales (PDF/XLSX/TXT/DOCX) y generar
   sugerencias automáticas para las secciones vacías vía LLM.
5. Analizar brechas con `GapAnalyzer`.
6. Devolver el `Documento` + lista de brechas + conteos + advertencias.

Los errores en extracción de fuentes o en sugerencias LLM se acumulan
en `ResultadoImportacion.advertencias` — nunca se suprimen silenciosamente,
para que la UI pueda mostrarlos al usuario.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import IO

from src.core.models import Brecha, Documento, FuenteContexto
from src.core.usecases.gap_analyzer import GapAnalyzer
from src.core.usecases.sugerencias_multifuente import (
    ResultadoSugerencias,
    SugerenciasMultiFuente,
)
from src.docs.reader import DocxReader
from src.docs.readers import extraer_texto
from src.docs.readers.anchor_reader import AnchorReader
from src.llm import LLMClient
from src.storage.repositories import DocumentoRepository
from src.storage.storage import Storage

logger = logging.getLogger(__name__)


@dataclass
class ResultadoImportacion:
    documento: Documento
    brechas: list[Brecha]
    file_id: str
    """ID interno del archivo .docx original guardado en Storage."""
    fuentes_procesadas: int = 0
    """Cantidad de fuentes adicionales que se procesaron correctamente."""
    secciones_pre_pobladas: int = 0
    """Secciones vacías que se rellenaron con borrador automático multi-fuente."""
    fuentes_descartadas: list[str] = field(default_factory=list)
    """Nombres de fuentes que fallaron al extraer texto."""
    sugerencias: ResultadoSugerencias | None = None
    """Detalle del paso multi-fuente; None si no se intentó."""
    llm_disponible: bool = True
    advertencias: list[str] = field(default_factory=list)


class ImportarDocumento:
    """Use case que importa un .docx, lo persiste y devuelve sus brechas."""

    def __init__(
        self,
        storage: Storage,
        reader: DocxReader | AnchorReader,
        repo: DocumentoRepository,
        analyzer: GapAnalyzer,
        llm: LLMClient | None = None,
    ) -> None:
        self.storage = storage
        # Acepta DocxReader legacy (tests existentes) o AnchorReader (multi-formato).
        # Si reciben DocxReader puro, ancla solo soporta .docx (comportamiento previo).
        self.reader = reader
        self.repo = repo
        self.analyzer = analyzer
        self.llm = llm

    def ejecutar(
        self,
        archivo: IO[bytes],
        nombre_original: str,
        user_id: str = "default",
        *,
        fuentes_adicionales: list[tuple[IO[bytes], str]] | None = None,
    ) -> ResultadoImportacion:
        # 1. Guardar archivo en Storage
        file_id = self.storage.guardar_upload(archivo, nombre_original)

        # 2. Parsear ancla (DOCX o PDF según extensión, si reader soporta)
        ruta = self.storage.ruta_local(file_id)
        documento = self.reader.leer(ruta, user_id=user_id)

        # 3. Procesar fuentes adicionales si las hay
        fuentes_procesadas = 0
        fuentes_descartadas: list[str] = []
        advertencias: list[str] = []
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
                    fuentes_procesadas += 1
                else:
                    fuentes_descartadas.append(nombre)

        # 4. Persistir antes de las sugerencias para no perder estado si fallan
        self.repo.guardar(documento)

        # 5. Generar sugerencias multi-fuente si hay LLM + fuentes
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

        # 6. Analizar brechas
        brechas = self.analyzer.analizar(documento)

        secciones_pre_pobladas = sugerencias.secciones_pobladas if sugerencias else 0

        return ResultadoImportacion(
            documento=documento,
            brechas=brechas,
            file_id=file_id,
            fuentes_procesadas=fuentes_procesadas,
            secciones_pre_pobladas=secciones_pre_pobladas,
            fuentes_descartadas=fuentes_descartadas,
            sugerencias=sugerencias,
            llm_disponible=llm_disponible,
            advertencias=advertencias,
        )
