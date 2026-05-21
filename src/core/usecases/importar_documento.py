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
from src.core.usecases.structure_realigner import (
    ResultadoRealign,
    StructureRealigner,
)
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
    realign: ResultadoRealign | None = None
    """Detalle de StructureRealigner; None si no se intentó (cobertura ya alta o sin LLM)."""
    llm_disponible: bool = True
    advertencias: list[str] = field(default_factory=list)
    documento_id_previo: str | None = None
    """Si el .docx ancla viene de un export previo de DocuMente, el `documento_id`
    original. La UI puede usarlo para preguntar al usuario si quiere crear v{N+1}
    del documento existente o tratarlo como documento nuevo. (Fase C.2)"""
    version_previa: int | None = None
    """Número de versión que tenía el .docx según su core_properties (C.2)."""


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
        describir_imagenes: bool = False,
    ) -> ResultadoImportacion:
        # 1. Guardar archivo en Storage
        # Leemos primero los bytes para poder inspeccionar metadata sin
        # consumir el stream para el storage.
        archivo.seek(0)
        bytes_ancla = archivo.read()
        archivo.seek(0)
        file_id = self.storage.guardar_upload(archivo, nombre_original)

        # 1.b. Detección de versión previa via core_properties (C.2)
        documento_id_previo: str | None = None
        version_previa: int | None = None
        if nombre_original.lower().endswith(".docx"):
            from src.core.usecases.exportar_documento import leer_metadata_version

            try:
                meta = leer_metadata_version(bytes_ancla)
                if meta:
                    documento_id_previo = meta.get("documento_id")
                    if "version" in meta:
                        try:
                            version_previa = int(meta["version"])
                        except ValueError:
                            version_previa = None
            except Exception as exc:
                logger.warning("No se pudo leer metadata de versión: %s", exc)

        # 2. Parsear ancla (DOCX o PDF según extensión, si reader soporta)
        ruta = self.storage.ruta_local(file_id)
        documento = self.reader.leer(ruta, user_id=user_id)

        # 3. Procesar fuentes adicionales si las hay
        fuentes_procesadas = 0
        fuentes_descartadas: list[str] = []
        advertencias: list[str] = []
        vision_describer = None
        if describir_imagenes and self.llm is not None:
            from src.llm.vision_describer import VisionDescriber

            vision_describer = VisionDescriber(self.llm)

        if fuentes_adicionales:
            for archivo_fuente, nombre in fuentes_adicionales:
                try:
                    tipo, texto = extraer_texto(
                        archivo_fuente,
                        nombre,
                        vision_describer=vision_describer,
                    )
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

        # 4. Si la cobertura del catálogo es baja, intentar reestructuración LLM.
        # El reader detecta secciones por heading-matching estricto; si el ancla
        # NO sigue la nomenclatura NYL, casi nada se mapea. El realigner toma
        # el texto crudo y remapea fragmentos verbatim a las secciones del catálogo.
        realign: ResultadoRealign | None = None
        if self.llm is not None:
            texto_crudo = self._extraer_texto_crudo(documento, ruta)
            if texto_crudo:
                realign = StructureRealigner(self.llm).ejecutar(documento, texto_crudo)
                if realign.hubo_errores:
                    advertencias.append(
                        "Reestructuración del ancla con IA falló — el documento "
                        "queda con las secciones que el reader sí detectó."
                    )

        # 5. Persistir antes de las sugerencias para no perder estado si fallan
        self.repo.guardar(documento)

        # 6. Generar sugerencias multi-fuente si hay LLM + fuentes
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

        # 7. Analizar brechas
        brechas = self.analyzer.analizar(documento)

        secciones_pre_pobladas = sugerencias.secciones_pobladas if sugerencias else 0

        if documento_id_previo:
            advertencias.append(
                f"Este .docx fue exportado previamente desde DocuMente "
                f"(documento_id={documento_id_previo}, "
                f"versión={version_previa if version_previa is not None else '?'}). "
                f"Si quieres crear una nueva versión del documento existente en lugar "
                f"de un documento independiente, ve al dashboard del documento original."
            )

        return ResultadoImportacion(
            documento=documento,
            brechas=brechas,
            file_id=file_id,
            fuentes_procesadas=fuentes_procesadas,
            secciones_pre_pobladas=secciones_pre_pobladas,
            fuentes_descartadas=fuentes_descartadas,
            sugerencias=sugerencias,
            realign=realign,
            llm_disponible=llm_disponible,
            advertencias=advertencias,
            documento_id_previo=documento_id_previo,
            version_previa=version_previa,
        )

    def _extraer_texto_crudo(self, documento: Documento, ruta) -> str:  # type: ignore[no-untyped-def]
        """Devuelve el texto plano del ancla para alimentar el StructureRealigner.

        Para PDFs, el `PdfAnchorReader` ya guarda el texto en `fuentes_contexto`
        cuando no detectó estructura — reusamos esa fuente.
        Para .docx (o PDFs que sí detectaron secciones pero pocas), reconstruimos
        concatenando el contenido detectado + el del ancla original.
        """
        # Caso PDF amorfo: ya hay texto en fuentes_contexto
        for fc in documento.fuentes_contexto:
            if fc.tipo == "pdf" and ruta.name == fc.nombre_archivo and fc.texto_extraido.strip():
                return fc.texto_extraido

        # Caso DOCX o PDF con algo de estructura: extraer del archivo
        try:
            from io import BytesIO

            with ruta.open("rb") as f:
                _tipo, texto = extraer_texto(BytesIO(f.read()), ruta.name)
            return texto
        except Exception as exc:  # pragma: no cover (defensa)
            logger.warning(
                "No se pudo extraer texto crudo del ancla '%s' para realign: %s",
                ruta.name,
                exc,
                exc_info=True,
            )
            return ""
