"""Use case: AdjuntarTablaApendice.

Cuando el usuario sube un .xlsx o .csv en la pantalla de entrevista de una
sección data-heavy, este use case:
1. Guarda el archivo en `Storage`.
2. Lee la tabla con `tabla_reader`.
3. Construye un `Apendice` con la tabla en markdown.
4. Agrega el apéndice al `Documento` y persiste.
5. Inyecta una `system_note` en el `EstadoEntrevista` actual para que Claude
   sepa que el apéndice se cargó y lo referencie en su redacción.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import IO

from src.core.models import (
    Apendice,
    Documento,
    EventoAuditoria,
    Seccion,
)
from src.docs.tabla_reader import TablaLeida, leer_tabla, leer_tabla_todas
from src.storage.repositories import (
    DocumentoRepository,
    EstadoEntrevistaRepository,
)
from src.storage.storage import Storage


@dataclass
class ResultadoAdjuntar:
    apendice: Apendice
    tabla: TablaLeida


# Secciones donde la subida de tablas tiene sentido.
SECCIONES_DATA_HEAVY: frozenset[str] = frozenset(
    {
        "4.4.assumptions",
        "5.1.raw_data",
        "5.2.upstream",
        "5.3.1.aggregations",
        "5.3.2.segmentations",
        "5.3.3.averages_proxies",
    }
)


def es_seccion_data_heavy(seccion_id: str) -> bool:
    return seccion_id in SECCIONES_DATA_HEAVY


class AdjuntarTablaApendice:
    """Adjunta una tabla (Excel/CSV) como apéndice de la sección actual."""

    def __init__(
        self,
        storage: Storage,
        doc_repo: DocumentoRepository,
        estado_repo: EstadoEntrevistaRepository,
    ) -> None:
        self.storage = storage
        self.doc_repo = doc_repo
        self.estado_repo = estado_repo

    def ejecutar_multihoja(
        self,
        documento: Documento,
        seccion: Seccion,
        archivo: IO[bytes],
        nombre_original: str,
        titulo_base: str,
    ) -> list[ResultadoAdjuntar]:
        """Crea N apéndices (uno por hoja) para Excel multihoja, 1 para CSV o Excel mono-hoja.

        Cada apéndice se titula `"{titulo_base} — {nombre_hoja}"` para diferenciarlos.
        Si hay una sola tabla (CSV, o Excel con 1 hoja con datos), el título queda
        igual a `titulo_base` (sin sufijo) para preservar UX simple.
        """
        # 1. Guardar archivo una sola vez (todas las hojas comparten archivo origen).
        file_id = self.storage.guardar_upload(archivo, nombre_original)
        ruta_local = self.storage.ruta_local(file_id)

        # 2. Leer todas las hojas
        tablas = leer_tabla_todas(Path(str(ruta_local)))
        if not tablas:
            raise ValueError(
                f"No se detectaron hojas con datos en '{nombre_original}'. "
                "Verifica que el archivo no esté vacío."
            )

        resultados: list[ResultadoAdjuntar] = []
        usar_sufijo = len(tablas) > 1
        for tabla in tablas:
            if usar_sufijo and tabla.nombre_hoja:
                titulo = f"{titulo_base} — {tabla.nombre_hoja}"
            else:
                titulo = titulo_base or f"Tabla de {seccion.nombre}"

            contenido = (
                f"**Archivo origen:** `{tabla.nombre_archivo}`"
                + (f" · Hoja: `{tabla.nombre_hoja}`" if tabla.nombre_hoja else "")
                + f"\n\n**Dimensiones:** {tabla.n_filas} filas × {tabla.n_columnas} columnas\n\n"
                + tabla.tabla_completa_md
            )
            apendice = Apendice(
                seccion_origen_id=seccion.id,
                titulo=titulo,
                tipo="tabla",
                contenido_md=contenido,
                archivo_id_storage=file_id,
                nombre_archivo_original=nombre_original,
            )
            documento.apendices.append(apendice)
            documento.registrar_evento(
                EventoAuditoria(
                    actor=documento.user_id,
                    tipo="seccion_editada",
                    descripcion=(
                        f"Apéndice agregado: '{apendice.titulo}' "
                        f"({tabla.n_filas}×{tabla.n_columnas}) "
                        f"vinculado a {seccion.numero} {seccion.nombre}."
                    ),
                    seccion_id=seccion.id,
                    metadata={"apendice_id": str(apendice.id)},
                )
            )
            resultados.append(ResultadoAdjuntar(apendice=apendice, tabla=tabla))

        self.doc_repo.guardar(documento)

        # Inyectar nota en la entrevista activa con resumen agregado
        estado = self.estado_repo.obtener(str(documento.id), seccion.id)
        if estado is not None and resultados:
            if len(resultados) == 1:
                tabla = resultados[0].tabla
                ap = resultados[0].apendice
                nota = (
                    f"El usuario adjuntó una tabla como apéndice: "
                    f"'{ap.titulo}' ({tabla.n_filas} filas, {tabla.n_columnas} cols). "
                    f"Resumen estructural:\n{tabla.resumen_estadistico}\n\n"
                    f"Primeras 5 filas:\n{tabla.primeras_filas_md}\n\n"
                    "En tu redacción y preguntas siguientes, refiérete a esta tabla "
                    f"como '(ver Apéndice: {ap.titulo})'. NO repliques toda la tabla "
                    "en la sección principal — vive en el apéndice."
                )
            else:
                lineas = [
                    f"El usuario adjuntó un Excel con {len(resultados)} hojas. "
                    "Cada hoja se guardó como apéndice independiente:"
                ]
                for r in resultados:
                    lineas.append(
                        f"- '{r.apendice.titulo}' ({r.tabla.n_filas}×{r.tabla.n_columnas})"
                    )
                lineas.append(
                    "\nEn tu redacción referencia cada apéndice por su título; "
                    "NO repliques las tablas en la sección principal."
                )
                nota = "\n".join(lineas)
            estado.agregar("system_note", nota)
            self.estado_repo.guardar(estado)

        return resultados

    def ejecutar(
        self,
        documento: Documento,
        seccion: Seccion,
        archivo: IO[bytes],
        nombre_original: str,
        titulo: str,
    ) -> ResultadoAdjuntar:
        # 1. Guardar archivo
        file_id = self.storage.guardar_upload(archivo, nombre_original)
        ruta_local = self.storage.ruta_local(file_id)

        # 2. Leer tabla
        tabla = leer_tabla(Path(str(ruta_local)))

        # 3. Construir apéndice
        contenido = (
            f"**Archivo origen:** `{tabla.nombre_archivo}`"
            + (f" · Hoja: `{tabla.nombre_hoja}`" if tabla.nombre_hoja else "")
            + f"\n\n**Dimensiones:** {tabla.n_filas} filas × {tabla.n_columnas} columnas\n\n"
            + tabla.tabla_completa_md
        )
        apendice = Apendice(
            seccion_origen_id=seccion.id,
            titulo=titulo or f"Tabla de {seccion.nombre}",
            tipo="tabla",
            contenido_md=contenido,
            archivo_id_storage=file_id,
            nombre_archivo_original=nombre_original,
        )

        # 4. Agregar al documento + audit
        documento.apendices.append(apendice)
        documento.registrar_evento(
            EventoAuditoria(
                actor=documento.user_id,
                tipo="seccion_editada",
                descripcion=(
                    f"Apéndice agregado: '{apendice.titulo}' "
                    f"({tabla.n_filas}×{tabla.n_columnas}) "
                    f"vinculado a {seccion.numero} {seccion.nombre}."
                ),
                seccion_id=seccion.id,
                metadata={"apendice_id": str(apendice.id)},
            )
        )
        self.doc_repo.guardar(documento)

        # 5. Inyectar system_note en la entrevista activa (si existe)
        estado = self.estado_repo.obtener(str(documento.id), seccion.id)
        if estado is not None:
            nota = (
                f"El usuario adjuntó una tabla como apéndice: "
                f"'{apendice.titulo}' ({tabla.n_filas} filas, {tabla.n_columnas} cols). "
                f"Resumen estructural:\n{tabla.resumen_estadistico}\n\n"
                f"Primeras 5 filas:\n{tabla.primeras_filas_md}\n\n"
                "En tu redacción y preguntas siguientes, refiérete a esta tabla "
                f"como '(ver Apéndice: {apendice.titulo})'. NO repliques toda la tabla "
                "en la sección principal — vive en el apéndice."
            )
            estado.agregar("system_note", nota)
            self.estado_repo.guardar(estado)

        return ResultadoAdjuntar(apendice=apendice, tabla=tabla)


__all__ = [
    "SECCIONES_DATA_HEAVY",
    "AdjuntarFormulaApendice",
    "AdjuntarPdfApendice",
    "AdjuntarTablaApendice",
    "ResultadoAdjuntar",
    "ResultadoAdjuntarFormula",
    "ResultadoAdjuntarPdf",
    "es_seccion_data_heavy",
]


@dataclass
class ResultadoAdjuntarPdf:
    """Resultado de adjuntar un PDF como apéndice."""

    apendice: Apendice
    n_paginas: int


@dataclass
class ResultadoAdjuntarFormula:
    """Resultado de adjuntar una fórmula LaTeX como apéndice."""

    apendice: Apendice
    latex_source: str


class AdjuntarPdfApendice:
    """Adjunta un .pdf como apéndice (cada página se renderiza al exportar)."""

    def __init__(
        self,
        storage: Storage,
        doc_repo: DocumentoRepository,
        estado_repo: EstadoEntrevistaRepository,
    ) -> None:
        self.storage = storage
        self.doc_repo = doc_repo
        self.estado_repo = estado_repo

    def ejecutar(
        self,
        documento: Documento,
        seccion: Seccion,
        archivo: IO[bytes],
        nombre_original: str,
        titulo: str,
    ) -> ResultadoAdjuntarPdf:
        from src.docs.readers.pdf_apendice_reader import contar_paginas_pdf

        file_id = self.storage.guardar_upload(archivo, nombre_original)
        ruta_local = self.storage.ruta_local(file_id)

        try:
            with Path(str(ruta_local)).open("rb") as f:
                n_paginas = contar_paginas_pdf(f)
        except Exception as exc:
            raise ValueError(
                f"No se pudo leer el PDF '{nombre_original}': {exc.__class__.__name__}"
            ) from exc

        if n_paginas == 0:
            raise ValueError(f"El PDF '{nombre_original}' no tiene páginas.")

        apendice = Apendice(
            seccion_origen_id=seccion.id,
            titulo=titulo or f"PDF de {seccion.nombre}",
            tipo="pdf",
            contenido_md="",  # vacío — el render vive en archivo_id_storage
            archivo_id_storage=file_id,
            nombre_archivo_original=nombre_original,
        )
        documento.apendices.append(apendice)
        documento.registrar_evento(
            EventoAuditoria(
                actor=documento.user_id,
                tipo="seccion_editada",
                descripcion=(
                    f"Apéndice PDF agregado: '{apendice.titulo}' ({n_paginas} página(s)) "
                    f"vinculado a {seccion.numero} {seccion.nombre}."
                ),
                seccion_id=seccion.id,
                metadata={"apendice_id": str(apendice.id), "n_paginas": str(n_paginas)},
            )
        )
        self.doc_repo.guardar(documento)

        estado = self.estado_repo.obtener(str(documento.id), seccion.id)
        if estado is not None:
            nota = (
                f"El usuario adjuntó un PDF como apéndice: '{apendice.titulo}' "
                f"({n_paginas} página(s)). El contenido visual del PDF se embeberá "
                f"en el .docx final. En tu redacción de la sección principal, "
                f"refiérete a él como '(ver Apéndice: {apendice.titulo})'."
            )
            estado.agregar("system_note", nota)
            self.estado_repo.guardar(estado)

        return ResultadoAdjuntarPdf(apendice=apendice, n_paginas=n_paginas)


class AdjuntarFormulaApendice:
    """Adjunta una fórmula LaTeX como apéndice (se renderea al exportar)."""

    def __init__(
        self,
        doc_repo: DocumentoRepository,
        estado_repo: EstadoEntrevistaRepository,
    ) -> None:
        self.doc_repo = doc_repo
        self.estado_repo = estado_repo

    def ejecutar(
        self,
        documento: Documento,
        seccion: Seccion,
        latex_source: str,
        titulo: str,
    ) -> ResultadoAdjuntarFormula:
        # Validar render previo — si el LaTeX no parsea, fallamos rápido.
        from src.docs.formulas.latex_to_image import (
            LatexRenderError,
            renderizar_latex_a_png,
        )

        limpio = (latex_source or "").strip()
        if not limpio:
            raise ValueError("El source LaTeX no puede estar vacío.")

        try:
            renderizar_latex_a_png(limpio)
        except LatexRenderError as exc:
            raise ValueError(f"LaTeX no válido: {exc}") from exc

        apendice = Apendice(
            seccion_origen_id=seccion.id,
            titulo=titulo or f"Fórmula de {seccion.nombre}",
            tipo="formula",
            contenido_md="",
            latex_source=limpio,
            nombre_archivo_original="",
        )
        documento.apendices.append(apendice)
        documento.registrar_evento(
            EventoAuditoria(
                actor=documento.user_id,
                tipo="seccion_editada",
                descripcion=(
                    f"Apéndice fórmula agregado: '{apendice.titulo}' "
                    f"vinculado a {seccion.numero} {seccion.nombre}."
                ),
                seccion_id=seccion.id,
                metadata={"apendice_id": str(apendice.id), "latex_chars": str(len(limpio))},
            )
        )
        self.doc_repo.guardar(documento)

        estado = self.estado_repo.obtener(str(documento.id), seccion.id)
        if estado is not None:
            estado.agregar(
                "system_note",
                f"El usuario adjuntó una fórmula matemática como apéndice: "
                f"'{apendice.titulo}'. Refiérete a ella desde la prosa como "
                f"'(ver Apéndice: {apendice.titulo})'.",
            )
            self.estado_repo.guardar(estado)

        return ResultadoAdjuntarFormula(apendice=apendice, latex_source=limpio)
