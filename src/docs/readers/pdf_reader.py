"""Lector de PDF — extrae texto + opcionalmente imágenes embebidas.

Por default solo extrae texto plano de todas las páginas vía `pypdf`. Si se
pasa un `VisionDescriber`, también extrae imágenes embebidas, las describe
con Claude Vision (Haiku 4.5) y las intercala en el texto resultante para
que el LLM downstream las "vea" semánticamente.
"""

from __future__ import annotations

import logging
from typing import IO

from pypdf import PdfReader

from src.llm.vision_describer import VisionDescriber

logger = logging.getLogger(__name__)


def leer_pdf(
    archivo: IO[bytes],
    *,
    vision_describer: VisionDescriber | None = None,
) -> str:
    """Devuelve el texto plano concatenado de todas las páginas del PDF.

    Tolerante a PDFs escaneados (devuelve string vacío si no hay capa de texto).
    No hace OCR. Si el PDF tiene contraseña, levanta excepción de pypdf.

    Si `vision_describer` se pasa, también extrae imágenes embebidas y las
    intercala como `[Imagen N (página X): <descripción>]` después del texto
    de la página correspondiente. Si la descripción falla para una imagen
    en particular, se reporta como placeholder pero el resto del flujo
    continúa.
    """
    archivo.seek(0)
    reader = PdfReader(archivo)
    fragmentos: list[str] = []
    contador_imagenes = 0

    for i, pagina in enumerate(reader.pages, start=1):
        # Texto de la página
        try:
            texto = pagina.extract_text() or ""
        except Exception:
            texto = ""
        if texto.strip():
            fragmentos.append(f"--- Página {i} ---\n{texto.strip()}")

        # Imágenes embebidas (solo si tenemos describer)
        if vision_describer is None:
            continue
        try:
            imagenes_pagina = list(pagina.images)
        except Exception as exc:
            logger.debug("No se pudieron enumerar imágenes en página %d: %s", i, exc)
            imagenes_pagina = []

        for img in imagenes_pagina:
            try:
                imagen_bytes = img.data
                # pypdf no siempre expone media_type; inferimos de la extensión
                nombre = getattr(img, "name", "")
                media_type = _inferir_media_type(nombre)
            except Exception as exc:
                logger.debug("Imagen ilegible en página %d: %s", i, exc)
                continue

            if not imagen_bytes:
                continue

            contador_imagenes += 1
            desc = vision_describer.describir(imagen_bytes, media_type=media_type)
            fragmentos.append(f"[Imagen {contador_imagenes} (página {i}): {desc.descripcion}]")

    return "\n\n".join(fragmentos)


def _inferir_media_type(nombre_o_path: str) -> str:
    """Mapeo simple extensión → MIME type. Default a image/png."""
    nlower = nombre_o_path.lower()
    if nlower.endswith(".jpg") or nlower.endswith(".jpeg"):
        return "image/jpeg"
    if nlower.endswith(".gif"):
        return "image/gif"
    if nlower.endswith(".webp"):
        return "image/webp"
    return "image/png"
