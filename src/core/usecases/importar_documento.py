"""Use case: ImportarDocumento.

Orquesta el flujo completo de importar un .docx existente:
1. Guardar el archivo subido en `Storage`.
2. Parsearlo con `DocxReader`.
3. Persistir el `Documento` resultante con `DocumentoRepository`.
4. (Opcional) Procesar fuentes adicionales (PDF/XLSX/TXT/DOCX) y generar
   sugerencias automáticas para las secciones vacías vía LLM.
5. Analizar brechas con `GapAnalyzer`.
6. Devolver el `Documento` + lista de brechas para que la UI las muestre.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import IO

from src.core.models import Brecha, Documento, FuenteContexto
from src.core.usecases.gap_analyzer import GapAnalyzer
from src.core.usecases.sugerencias_multifuente import SugerenciasMultiFuente
from src.docs.reader import DocxReader
from src.docs.readers import extraer_texto
from src.llm import LLMClient
from src.storage.repositories import DocumentoRepository
from src.storage.storage import Storage


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


class ImportarDocumento:
    """Use case que importa un .docx, lo persiste y devuelve sus brechas."""

    def __init__(
        self,
        storage: Storage,
        reader: DocxReader,
        repo: DocumentoRepository,
        analyzer: GapAnalyzer,
        llm: LLMClient | None = None,
    ) -> None:
        self.storage = storage
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

        # 2. Parsear con DocxReader (ancla estructural)
        ruta = self.storage.ruta_local(file_id)
        documento = self.reader.leer(ruta, user_id=user_id)

        # 3. Procesar fuentes adicionales si las hay
        fuentes_procesadas = 0
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
                    fuentes_procesadas += 1

        # 4. Persistir antes de las sugerencias para no perder estado si fallan
        self.repo.guardar(documento)

        # 5. Generar sugerencias multi-fuente si hay LLM + fuentes
        secciones_pre_pobladas = 0
        if self.llm is not None and documento.fuentes_contexto:
            sugerencias = SugerenciasMultiFuente(self.llm)
            secciones_pre_pobladas = sugerencias.ejecutar(documento)
            if secciones_pre_pobladas > 0:
                self.repo.guardar(documento)

        # 6. Analizar brechas
        brechas = self.analyzer.analizar(documento)

        return ResultadoImportacion(
            documento=documento,
            brechas=brechas,
            file_id=file_id,
            fuentes_procesadas=fuentes_procesadas,
            secciones_pre_pobladas=secciones_pre_pobladas,
        )
