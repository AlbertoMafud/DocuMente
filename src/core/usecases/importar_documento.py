"""Use case: ImportarDocumento.

Orquesta el flujo completo de importar un .docx existente:
1. Guardar el archivo subido en `Storage`.
2. Parsearlo con `DocxReader`.
3. Persistir el `Documento` resultante con `DocumentoRepository`.
4. Analizar brechas con `GapAnalyzer`.
5. Devolver el `Documento` + lista de brechas para que la UI las muestre.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import IO

from src.core.models import Brecha, Documento
from src.core.usecases.gap_analyzer import GapAnalyzer
from src.docs.reader import DocxReader
from src.storage.repositories import DocumentoRepository
from src.storage.storage import Storage


@dataclass
class ResultadoImportacion:
    documento: Documento
    brechas: list[Brecha]
    file_id: str
    """ID interno del archivo .docx original guardado en Storage."""


class ImportarDocumento:
    """Use case que importa un .docx, lo persiste y devuelve sus brechas."""

    def __init__(
        self,
        storage: Storage,
        reader: DocxReader,
        repo: DocumentoRepository,
        analyzer: GapAnalyzer,
    ) -> None:
        self.storage = storage
        self.reader = reader
        self.repo = repo
        self.analyzer = analyzer

    def ejecutar(
        self,
        archivo: IO[bytes],
        nombre_original: str,
        user_id: str = "default",
    ) -> ResultadoImportacion:
        # 1. Guardar archivo en Storage
        file_id = self.storage.guardar_upload(archivo, nombre_original)

        # 2. Parsear con DocxReader
        ruta = self.storage.ruta_local(file_id)
        documento = self.reader.leer(ruta, user_id=user_id)

        # 3. Persistir
        self.repo.guardar(documento)

        # 4. Analizar brechas
        brechas = self.analyzer.analizar(documento)

        return ResultadoImportacion(
            documento=documento,
            brechas=brechas,
            file_id=file_id,
        )
