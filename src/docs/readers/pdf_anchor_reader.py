"""PdfAnchorReader — parsea un PDF como ancla estructural (alternativa a .docx).

A diferencia de `pdf_reader.leer_pdf` (que solo devuelve texto plano para
fuentes adicionales), este reader produce un `Documento` poblado con las
secciones del catálogo NYL detectadas en el PDF — mismo contrato que
`DocxReader`.

Estrategia (PDF carece de info de estilo nativo accesible vía pypdf):

1. Extraer texto plano del PDF.
2. Recorrer línea por línea. Considerar candidatas a heading aquellas que:
   - Empiezan con numeración tipo "4.4 ", "1.2.3 ", etc., O
   - Son cortas (<120 chars) y en mayúsculas o título-case, O
   - Coinciden literalmente con un nombre/alias del catálogo NYL.
3. Para cada candidata, intentar mapear al catálogo con la MISMA función
   `_coincide_con_catalogo` que usa `DocxReader`. Si match → sección actual
   cambia y se vuelca el buffer.
4. Texto entre headings = contenido de la sección.
5. Si NO se detectó ninguna sección del catálogo, el texto completo se
   guarda en `documento.fuentes_contexto` como fuente PDF para que
   `SugerenciasMultiFuente` lo procese.

No hace OCR. Si el PDF es escaneado (sin capa de texto), produce
documento vacío + advertencia. La UI muestra ese caso al usuario.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from src.core.models import Documento, EventoAuditoria, FuenteContexto, Seccion
from src.core.template_catalog import construir_secciones_vacias
from src.docs.reader import _coincide_con_catalogo, _evaluar_completitud
from src.docs.readers.pdf_reader import leer_pdf

_NUM_HEADING_RE = re.compile(r"^\s*\d+(?:\.\d+){0,3}\.?\s+\S")
_MAX_HEADING_LEN = 120


def _candidata_heading(linea: str) -> bool:
    """Filtro barato para descartar líneas que claramente NO son heading."""
    texto = linea.strip()
    if not texto:
        return False
    if len(texto) > _MAX_HEADING_LEN:
        return False
    # Empieza con número estilo "4.4 X" → muy probable heading
    if _NUM_HEADING_RE.match(texto):
        return True
    # Líneas cortas en mayúsculas (más de 60% letras mayúsculas entre letras)
    letras = [c for c in texto if c.isalpha()]
    if letras:
        ratio_mayus = sum(1 for c in letras if c.isupper()) / len(letras)
        if ratio_mayus >= 0.6 and len(texto) <= 80:
            return True
    # Líneas cortas en title case: cada palabra inicia con mayúscula
    palabras = [w for w in texto.split() if w]
    return 2 <= len(palabras) <= 10 and all(w[0].isupper() for w in palabras if w[0].isalpha())


class PdfAnchorReader:
    """Lector de PDF como ancla estructural — mismo contrato que DocxReader."""

    def leer(self, ruta: Path, user_id: str = "default") -> Documento:
        if not ruta.exists():
            raise FileNotFoundError(f"No existe el archivo: {ruta}")

        with ruta.open("rb") as f:
            texto_completo = leer_pdf(f)

        documento = Documento(
            user_id=user_id,
            archivo_origen=str(ruta),
            secciones=construir_secciones_vacias(),
        )

        # Caso PDF escaneado / sin texto extraíble
        if not texto_completo.strip():
            documento.registrar_evento(
                EventoAuditoria(
                    timestamp=datetime.now(UTC),
                    actor=user_id,
                    tipo="documento_importado",
                    descripcion=f"Importado desde {ruta.name} (PDF sin texto extraíble)",
                    metadata={"archivo": ruta.name, "advertencia": "pdf_sin_texto"},
                )
            )
            return documento

        secciones_detectadas = self._poblar_secciones_desde_texto(documento, texto_completo)

        # Si no se detectó ninguna sección NYL, guardar como fuente_contexto
        # para que SugerenciasMultiFuente intente desde texto plano.
        if secciones_detectadas == 0:
            documento.fuentes_contexto.append(
                FuenteContexto(
                    nombre_archivo=ruta.name,
                    tipo="pdf",
                    texto_extraido=texto_completo,
                )
            )

        # Re-evaluar completitud
        for s in documento.secciones:
            s.completitud = _evaluar_completitud(s.contenido or "")  # type: ignore[assignment]

        descripcion = (
            f"Importado desde {ruta.name} "
            f"({secciones_detectadas} sección(es) detectada(s) por heurística PDF)"
            if secciones_detectadas > 0
            else (
                f"Importado desde {ruta.name} "
                f"(sin estructura NYL detectada; texto cargado como fuente de contexto)"
            )
        )
        documento.registrar_evento(
            EventoAuditoria(
                timestamp=datetime.now(UTC),
                actor=user_id,
                tipo="documento_importado",
                descripcion=descripcion,
                metadata={
                    "archivo": ruta.name,
                    "secciones_detectadas": str(secciones_detectadas),
                },
            )
        )
        return documento

    def _poblar_secciones_desde_texto(self, documento: Documento, texto: str) -> int:
        """Recorre línea por línea, identifica headings y vuelca contenido.

        Devuelve la cantidad de secciones del catálogo que se mapearon.
        """
        seccion_actual: Seccion | None = None
        buffer: list[str] = []
        secciones_unicas: set[str] = set()

        def flush() -> None:
            if seccion_actual is None:
                return
            contenido = "\n".join(b for b in buffer if b.strip())
            if not contenido.strip():
                return
            existente = seccion_actual.contenido or ""
            seccion_actual.contenido = (
                f"{existente}\n{contenido}".strip() if existente else contenido
            )

        for linea in texto.splitlines():
            stripped = linea.strip()
            # Pypdf marca cada página con "--- Página N ---" en pdf_reader.py
            # — saltamos esos marcadores (no son contenido real).
            if stripped.startswith("--- Página ") and stripped.endswith("---"):
                continue
            if _candidata_heading(stripped):
                cat = _coincide_con_catalogo(stripped)
                if cat is not None:
                    flush()
                    buffer = []
                    seccion_actual = documento.seccion_por_id(cat.id)
                    if seccion_actual is not None:
                        secciones_unicas.add(seccion_actual.id)
                    continue
            if stripped:
                buffer.append(stripped)

        flush()
        return len(secciones_unicas)


def leer_pdf_bytes(contenido: bytes, nombre: str, user_id: str = "default") -> Documento:
    """Helper para tests: persiste bytes a temp file y delega al reader.

    `nombre` se usa para preservar la extensión en el path temporal (necesario
    para algunos pipelines que detectan tipo por extensión).
    """
    import contextlib
    import tempfile

    sufijo = Path(nombre).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=sufijo, delete=False) as tmp:
        tmp.write(contenido)
        tmp_path = Path(tmp.name)
    try:
        return PdfAnchorReader().leer(tmp_path, user_id=user_id)
    finally:
        with contextlib.suppress(OSError):
            tmp_path.unlink()
