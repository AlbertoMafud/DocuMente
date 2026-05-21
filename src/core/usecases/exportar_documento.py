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
from src.core.usecases.crear_version import CrearVersion, ResultadoCrearVersion
from src.core.usecases.docx_writer import DocxWriter
from src.core.usecases.table_extractor import TableExtractor
from src.core.usecases.traductor import IDIOMAS_SOPORTADOS, Idioma, TraductorDocumento
from src.llm import LLMClient
from src.storage.repositories import DocumentoRepository, VersionRepository


@dataclass(frozen=True)
class ResultadoExportacion:
    """Bytes del .docx generado + nombre de archivo sugerido + metadata de versión."""

    contenido: bytes
    nombre_archivo: str
    version: ResultadoCrearVersion | None = None
    """Si se pidió `crear_version=True`, info de la versión creada (o reutilizada)."""


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
        crear_version: bool = False,
        comentario_version: str = "",
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

        # Modos que requieren LLM (cualquier traducción/normalización).
        modos_con_llm = {"en", "es_normalize", "en_normalize"}
        if idioma_objetivo in modos_con_llm:
            if self.llm is None:
                raise RuntimeError(
                    "Esta opción de idioma requiere LLM configurado (ANTHROPIC_API_KEY en .env)."
                )
            TraductorDocumento(self.llm).traducir(documento, idioma_objetivo=idioma_objetivo)

        # Idioma "físico" para el writer (string ES vs EN dentro del .docx).
        idioma_writer = "en" if idioma_objetivo in ("en", "en_normalize") else "es"

        extractor = TableExtractor(self.llm) if self.llm is not None else None
        writer = DocxWriter(table_extractor=extractor)
        blob = writer.generar(documento, self.template_path, idioma=idioma_writer)
        nombre = _sugerir_nombre(documento.metadata_modelo.nombre_modelo, idioma=idioma_writer)

        # Crear versión opt-in (C.2). Se hace ANTES de incrustar metadata para
        # que el hash sea sobre el estado del documento "limpio", no sobre uno
        # que ya incluye la version_numero en core_properties.
        resultado_version: ResultadoCrearVersion | None = None
        if crear_version:
            # Trabajamos sobre el documento ORIGINAL (no traducido) para que el
            # snapshot refleje el estado canónico, no la mutación efímera.
            original_para_version = self.doc_repo.obtener(documento_id)
            if original_para_version is not None:
                version_uc = CrearVersion(
                    doc_repo=self.doc_repo,
                    version_repo=VersionRepository(),
                )
                resultado_version = version_uc.ejecutar(
                    original_para_version,
                    comentario=comentario_version or f"Export DOCX ({idioma_objetivo})",
                    actor=actor,
                )

        # Incrustar metadata identificadora en core_properties del docx final.
        # Esto permite que ImportarDocumento reconozca el archivo como versión
        # de un documento existente al re-subirlo.
        blob = _incrustar_metadata_version(
            blob,
            documento_id=documento.id,
            version_numero=(
                resultado_version.version.numero if resultado_version is not None else None
            ),
            hash_contenido=(
                resultado_version.version.hash_contenido[:12]
                if resultado_version is not None
                else None
            ),
        )

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
                        f"como '{nombre}' [modo: {idioma_objetivo}]."
                    ),
                    metadata={
                        "bytes": str(len(blob)),
                        "nombre_archivo": nombre,
                        "modo_idioma": idioma_objetivo,
                        "idioma_escritura": idioma_writer,
                    },
                )
            )
            # Conservar las métricas LLM (traducción + extracción tabular)
            # acumuladas en el doc mutado.
            original.metricas_uso = documento.metricas_uso
            self.doc_repo.guardar(original)

        return ResultadoExportacion(
            contenido=blob,
            nombre_archivo=nombre,
            version=resultado_version,
        )


def _incrustar_metadata_version(
    blob: bytes,
    *,
    documento_id: UUID,
    version_numero: int | None,
    hash_contenido: str | None,
) -> bytes:
    """Incrusta `documento_id` + opcional `version_numero` + `hash` en core_properties.

    Usa `python-docx` para abrir el blob, escribir en core_properties.comments,
    keywords y category, y devolver los bytes actualizados. Esto sobrevive
    al transit por OneDrive / SharePoint / email — no se borra.

    Convención:
    - `category`: "DocuMente"
    - `comments`: "documento_id=<uuid>;version=<N>;hash=<12hex>" (CSV-style)
    - `keywords`: "DocuMente,v{N}" (legible humanamente en File Info de Word)
    """
    from io import BytesIO

    from docx import Document as DocxDocument

    buf_in = BytesIO(blob)
    doc = DocxDocument(buf_in)
    cp = doc.core_properties
    cp.category = "DocuMente"
    partes = [f"documento_id={documento_id}"]
    if version_numero is not None:
        partes.append(f"version={version_numero}")
    if hash_contenido is not None:
        partes.append(f"hash={hash_contenido}")
    cp.comments = ";".join(partes)
    if version_numero is not None:
        cp.keywords = f"DocuMente,v{version_numero}"
    else:
        cp.keywords = "DocuMente"
    buf_out = BytesIO()
    doc.save(buf_out)
    return buf_out.getvalue()


def leer_metadata_version(blob: bytes) -> dict[str, str]:
    """Parsea `core_properties.comments` de un .docx para extraer metadata DocuMente.

    Devuelve dict con keys: `documento_id`, `version` (opcional), `hash` (opcional).
    Si el .docx no tiene metadata DocuMente, devuelve dict vacío.
    """
    from io import BytesIO

    from docx import Document as DocxDocument

    try:
        doc = DocxDocument(BytesIO(blob))
    except Exception:
        return {}
    cp = doc.core_properties
    if (cp.category or "").strip() != "DocuMente":
        return {}
    comments = (cp.comments or "").strip()
    if not comments:
        return {}
    resultado: dict[str, str] = {}
    for parte in comments.split(";"):
        if "=" in parte:
            k, v = parte.split("=", 1)
            resultado[k.strip()] = v.strip()
    return resultado


_INVALIDOS = re.compile(r'[<>:"/\\|?*]')


def _sugerir_nombre(nombre_modelo: str, *, idioma: Idioma = "es") -> str:
    """Genera nombre de archivo seguro: '<modelo>_<idioma>_<fecha>.docx'."""
    base = nombre_modelo.strip() if nombre_modelo and nombre_modelo.strip() else "documento"
    base = _INVALIDOS.sub("_", base).replace(" ", "_")[:60]
    fecha = datetime.now(UTC).astimezone().strftime("%Y%m%d_%H%M%S")
    sufijo_idioma = "_EN" if idioma == "en" else ""
    return f"{base}{sufijo_idioma}_{fecha}.docx"
