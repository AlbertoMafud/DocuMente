"""Use case ExportarDocumento — genera el .docx final y registra audit event.

Orquesta:
1. Cargar Documento desde repo.
2. Si hay LLMClient inyectado, instanciar TableExtractor para llenar las
   tablas estructuradas (5.1, 5.2, 5.5, 6.5).
3. DocxWriter renderiza la plantilla maestra → bytes del .docx.
4. Registrar evento 'exportado' en audit_trail.
5. Devolver bytes + nombre de archivo sugerido para descarga.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from src.core.models import EventoAuditoria
from src.core.usecases.docx_writer import DocxWriter
from src.core.usecases.table_extractor import TableExtractor
from src.core.usecases.traductor import IDIOMAS_SOPORTADOS, Idioma, TraductorDocumento
from src.llm import LLMClient
from src.storage.repositories import DocumentoRepository


@dataclass(frozen=True)
class ResultadoExportacion:
    """Bytes del .docx generado + nombre de archivo sugerido."""

    contenido: bytes
    nombre_archivo: str


class ExportarDocumento:
    """Use case: renderizar plantilla con datos del documento y devolver bytes."""

    def __init__(
        self,
        doc_repo: DocumentoRepository,
        *,
        template_path: Path,
        llm: LLMClient | None = None,
    ) -> None:
        self.doc_repo = doc_repo
        self.template_path = template_path
        self.llm = llm

    def ejecutar(
        self,
        documento_id: UUID,
        *,
        actor: str,
        idioma_objetivo: Idioma = "es",
    ) -> ResultadoExportacion:
        if idioma_objetivo not in IDIOMAS_SOPORTADOS:
            raise ValueError(
                f"Idioma '{idioma_objetivo}' no soportado. Opciones: {IDIOMAS_SOPORTADOS}."
            )
        if not self.template_path.exists():
            raise FileNotFoundError(
                f"Plantilla maestra no encontrada en {self.template_path}. "
                "Verifica que existe el .docx con placeholders Jinja."
            )

        documento = self.doc_repo.obtener(documento_id)
        if documento is None:
            raise ValueError(f"Documento {documento_id} no encontrado.")

        # Si idioma destino != español, traducir contenido (mutación efímera
        # sobre la copia cargada de BD; no se persiste el doc traducido).
        if idioma_objetivo == "en":
            if self.llm is None:
                raise RuntimeError(
                    "Traducción al inglés requiere LLM configurado (ANTHROPIC_API_KEY en .env)."
                )
            TraductorDocumento(self.llm).traducir(documento, idioma_objetivo="en")

        extractor = TableExtractor(self.llm) if self.llm is not None else None
        writer = DocxWriter(table_extractor=extractor)
        blob = writer.generar(documento, self.template_path)
        nombre = _sugerir_nombre(documento.metadata_modelo.nombre_modelo, idioma=idioma_objetivo)

        # Recargar el doc original para registrar el audit event sin contaminar
        # la BD con el contenido traducido (la traducción solo vive en el .docx).
        original = self.doc_repo.obtener(documento_id)
        if original is not None:
            original.registrar_evento(
                EventoAuditoria(
                    actor=actor,
                    tipo="exportado",
                    descripcion=(
                        f"Documento exportado a .docx ({len(blob):,} bytes) "
                        f"como '{nombre}' [idioma: {idioma_objetivo}]."
                    ),
                    metadata={
                        "bytes": str(len(blob)),
                        "nombre_archivo": nombre,
                        "idioma": idioma_objetivo,
                    },
                )
            )
            # Conservar las métricas LLM (traducción + extracción tabular)
            # acumuladas en el doc mutado.
            original.metricas_uso = documento.metricas_uso
            self.doc_repo.guardar(original)

        return ResultadoExportacion(contenido=blob, nombre_archivo=nombre)


_INVALIDOS = re.compile(r'[<>:"/\\|?*]')


def _sugerir_nombre(nombre_modelo: str, *, idioma: Idioma = "es") -> str:
    """Genera nombre de archivo seguro: '<modelo>_<idioma>_<fecha>.docx'."""
    base = nombre_modelo.strip() if nombre_modelo and nombre_modelo.strip() else "documento"
    base = _INVALIDOS.sub("_", base).replace(" ", "_")[:60]
    fecha = datetime.now(UTC).astimezone().strftime("%Y%m%d_%H%M%S")
    sufijo_idioma = "_EN" if idioma == "en" else ""
    return f"{base}{sufijo_idioma}_{fecha}.docx"
