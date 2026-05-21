"""VisionDescriber — describe imágenes embebidas en documentos cargados.

Diseñado para capturar valor semántico de screenshots y diagramas en docs
de Prophet/MRM, donde el texto solo no es suficiente para entender el
contexto. Usa Claude Haiku 4.5 multimodal a través del `LLMClient`
existente, con cache local persistente por SHA-256 del binario.

Decisiones:

1. **Cache infinito por hash**: las imágenes son inmutables — si dos
   documentos contienen exactamente el mismo screenshot, su descripción
   solo se paga una vez en la vida del proyecto.
2. **Persistencia local**: `data/vision_cache.json`. Cuando migremos a
   EC2 + Postgres podemos mover a una tabla.
3. **Degradación silenciosa**: si el LLM no está disponible (no API key,
   error de red, cuota), devuelve un placeholder y loggea warning. El
   pipeline de extracción nunca se aborta por una imagen.
4. **Modelo Haiku, no Sonnet/Opus**: el caso de uso es "describir en 3-4
   frases qué se ve" — no requiere razonamiento profundo. Haiku 4.5
   multimodal cuesta ~$1 input + $5 output por 1M tokens.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path

from anthropic.types import TextBlockParam

from src.llm.client import LLMClient

logger = logging.getLogger(__name__)

_PROMPT_DESCRIPCION = (
    "Describe brevemente qué muestra esta imagen, en el contexto de "
    "documentación de un modelo, proceso o procedimiento institucional. "
    "Si es un screenshot de software (ej. Prophet, Excel, SQL, alguna app), "
    "identifica la herramienta y los elementos visibles relevantes. "
    "Si es un flowchart, diagrama o gráfico, describe la estructura y "
    "qué representa. Si es una tabla de datos, indica las columnas y el "
    "tipo de información. Máximo 4 frases, en español, factuales — no "
    "interpretes ni hagas suposiciones sobre el negocio."
)

_SYSTEM_BLOCKS: list[TextBlockParam] = [
    {
        "type": "text",
        "text": (
            "Eres un asistente experto en documentación institucional. "
            "Tu tarea es describir imágenes embebidas en documentos para "
            "que un humano que NO vea la imagen pueda entender qué contiene."
        ),
    }
]


@dataclass(frozen=True)
class DescripcionImagen:
    """Resultado de describir una imagen."""

    sha256: str
    descripcion: str
    desde_cache: bool
    """True si la descripción vino del cache local."""


class VisionDescriber:
    """Describe imágenes embebidas en PDFs/DOCX usando Claude vision.

    Uso:
        describer = VisionDescriber(llm_client)
        desc = describer.describir(image_bytes, "image/png")
        print(desc.descripcion)
    """

    def __init__(
        self,
        llm: LLMClient,
        *,
        cache_path: Path | None = None,
    ) -> None:
        self._llm = llm
        self._cache_path = cache_path or (
            Path(__file__).resolve().parent.parent.parent / "data" / "vision_cache.json"
        )
        self._cache: dict[str, str] = {}
        self._cache_lock = threading.Lock()
        self._cargar_cache()

    def _cargar_cache(self) -> None:
        if self._cache_path.exists():
            try:
                with self._cache_path.open("r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(
                    "No se pudo leer vision_cache (%s): %s. Se inicia vacío.",
                    self._cache_path,
                    exc,
                )
                self._cache = {}

    def _persistir_cache(self) -> None:
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self._cache_path.open("w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            logger.warning("No se pudo persistir vision_cache: %s", exc)

    def describir(
        self,
        imagen_bytes: bytes,
        media_type: str = "image/png",
    ) -> DescripcionImagen:
        """Devuelve una descripción de la imagen.

        Si la imagen ya fue descrita antes (mismo hash sha256), devuelve
        el cache sin llamar al LLM.

        Args:
            imagen_bytes: contenido binario de la imagen (PNG, JPEG, GIF, WebP).
            media_type: MIME type. Acepta image/png, image/jpeg, image/gif, image/webp.
        """
        sha = hashlib.sha256(imagen_bytes).hexdigest()

        with self._cache_lock:
            if sha in self._cache:
                return DescripcionImagen(
                    sha256=sha,
                    descripcion=self._cache[sha],
                    desde_cache=True,
                )

        try:
            descripcion = self._llamar_llm(imagen_bytes, media_type)
        except Exception as exc:
            logger.warning(
                "VisionDescriber falló para sha=%s: %s. Devolviendo placeholder.",
                sha[:8],
                exc,
                exc_info=True,
            )
            return DescripcionImagen(
                sha256=sha,
                descripcion="[imagen no descrita: vision describer no disponible]",
                desde_cache=False,
            )

        with self._cache_lock:
            self._cache[sha] = descripcion
            self._persistir_cache()

        return DescripcionImagen(sha256=sha, descripcion=descripcion, desde_cache=False)

    def _llamar_llm(self, imagen_bytes: bytes, media_type: str) -> str:
        """Llama al LLM con la imagen + el prompt de descripción."""
        b64 = base64.b64encode(imagen_bytes).decode("ascii")
        # MessageParam con content blocks mixtos (image + text).
        # Cast por compatibilidad con TypedDict de anthropic.
        messages: list = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": _PROMPT_DESCRIPCION},
                ],
            }
        ]

        respuesta = self._llm.chat(
            tarea="vision",
            system_blocks=_SYSTEM_BLOCKS,
            messages=messages,
            max_tokens=400,
        )
        return respuesta.text.strip()


__all__ = ["DescripcionImagen", "VisionDescriber"]
