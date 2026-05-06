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
from src.docs.tabla_reader import TablaLeida, leer_tabla
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
    "AdjuntarTablaApendice",
    "ResultadoAdjuntar",
    "es_seccion_data_heavy",
]
