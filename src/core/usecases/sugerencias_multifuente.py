"""Use case SugerenciasMultiFuente — pre-popula secciones vacías con borradores
generados a partir del texto extraído de fuentes adicionales.

Política:
- Solo opera sobre secciones con `completitud == "vacia"`. No pisa contenido
  existente (parcial, completa, omitida).
- Marca el contenido sugerido con prefijo `[Borrador automático — revisar]`
  y `completitud = "parcial"` para que la UI muestre el badge claramente.
- Cita las fuentes consultadas al final del borrador.
- Tolerante a errores LLM: si una sección falla, sigue con las demás y
  registra el error en el resultado (no se suprime silenciosamente).

Paralelización (S17):
- `ejecutar_async()` procesa las secciones en paralelo con un Semaphore
  configurable (default 5). Esto reduce el tiempo wall-clock de ~10 min a
  ~1-2 min para documentos con ~10-15 secciones a sugerir.
- `ejecutar()` (sincrónico) se mantiene como wrapper que llama
  `asyncio.run(self.ejecutar_async(...))`. Los use cases legacy no necesitan
  cambiar.
- Acepta callback `on_progress(seccion_idx, total)` para emitir eventos al
  endpoint streaming (S17.B). Default no-op para que tests + callers viejos
  no se enteren.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from anthropic.types import MessageParam, TextBlockParam

from src.core.models import Documento, FuenteContexto, Seccion
from src.core.usecases.strings_localizados import Idioma, t
from src.llm import LLMClient
from src.llm.pricing import construir_llamada
from src.llm.prompts.sugerencias_multifuente import (
    SUGERENCIAS_MULTIFUENTE_SYSTEM,
    construir_prompt_seccion,
)

logger = logging.getLogger(__name__)

# Concurrencia default. Conservador: el tier de Anthropic suele permitir
# 50+ RPM en producción; 5 paralelas evita rate limits incluso en tier free.
_CONCURRENCIA_DEFAULT = 5

# Tipo del callback de progreso. Async para que el caller pueda awaitar
# operaciones de IO (ej. emitir SSE) sin bloquear el gather principal.
ProgressCallback = Callable[["EventoProgreso"], Awaitable[None]]


@dataclass(frozen=True)
class EventoProgreso:
    """Evento emitido cuando una sección termina de procesarse.

    Lo consume el endpoint streaming para emitir SSE. En callers viejos
    no se usa (callback default es no-op).
    """

    seccion_id: str
    seccion_nombre: str
    seccion_numero: str
    completadas: int
    """Conteo acumulado de secciones terminadas (incluye errores)."""
    total: int
    """Total de secciones que se intentaron procesar."""
    estado: str
    """`'poblada'` si se llenó, `'sin_info'` si LLM dijo que no había info,
    `'error'` si la llamada falló."""
    error: str | None = None


@dataclass(frozen=True)
class ResultadoSugerencias:
    """Resultado de aplicar sugerencias multi-fuente sobre un documento.

    Attributes:
        secciones_pobladas: cantidad de secciones que se llenaron con borrador.
        secciones_intentadas: cantidad de secciones vacías que se intentaron.
        errores: lista de mensajes legibles si alguna sección falló por LLM.
        fuentes_usadas: cantidad de fuentes con texto extraído utilizadas.
    """

    secciones_pobladas: int = 0
    secciones_intentadas: int = 0
    errores: list[str] = field(default_factory=list)
    fuentes_usadas: int = 0

    @property
    def hubo_errores(self) -> bool:
        return bool(self.errores)


async def _noop_progress(_evento: EventoProgreso) -> None:
    """Callback default que no hace nada."""
    return None


class SugerenciasMultiFuente:
    """Use case: extrae sugerencias de fuentes adicionales y pre-popula secciones.

    Ofrece dos APIs:
    - `ejecutar(...)`: sincrónico, mismo contrato de siempre. Internamente
      llama `asyncio.run(ejecutar_async(...))`.
    - `ejecutar_async(..., on_progress=...)`: asíncrono, permite callback de
      progreso. Útil para endpoint SSE.
    """

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def ejecutar(
        self,
        documento: Documento,
        fuentes: list[FuenteContexto] | None = None,
        *,
        idioma: Idioma = "es",
        max_secciones: int = 28,
        concurrencia: int = _CONCURRENCIA_DEFAULT,
    ) -> ResultadoSugerencias:
        """Wrapper sincrónico de `ejecutar_async`. Mantiene contrato legacy."""
        return asyncio.run(
            self.ejecutar_async(
                documento,
                fuentes,
                idioma=idioma,
                max_secciones=max_secciones,
                concurrencia=concurrencia,
            )
        )

    async def ejecutar_async(
        self,
        documento: Documento,
        fuentes: list[FuenteContexto] | None = None,
        *,
        idioma: Idioma = "es",
        max_secciones: int = 28,
        concurrencia: int = _CONCURRENCIA_DEFAULT,
        on_progress: ProgressCallback | None = None,
    ) -> ResultadoSugerencias:
        """Genera sugerencias para secciones vacías, en paralelo.

        Args:
            documento: documento donde escribir las sugerencias (in-place).
            fuentes: lista de FuenteContexto. Si None, usa `documento.fuentes_contexto`.
            idioma: idioma del prefijo "[Borrador automático — revisar]".
            max_secciones: límite duro de secciones a sugerir (control de costo).
            concurrencia: número máximo de llamadas LLM simultáneas (Semaphore).
            on_progress: callback opcional invocado al terminar cada sección.

        Returns:
            ResultadoSugerencias con conteos y errores agregados durante la corrida.
        """
        fuentes_efectivas = fuentes if fuentes is not None else documento.fuentes_contexto
        if not fuentes_efectivas:
            return ResultadoSugerencias()

        fuentes_payload: list[tuple[str, str]] = [
            (f.nombre_archivo, f.texto_extraido)
            for f in fuentes_efectivas
            if f.texto_extraido.strip()
        ]
        if not fuentes_payload:
            return ResultadoSugerencias()

        prefijo_borrador = t("borrador_automatico_revisar", idioma)
        secciones_a_procesar: list[Seccion] = [
            s for s in documento.secciones if s.completitud == "vacia"
        ][:max_secciones]
        total = len(secciones_a_procesar)
        if total == 0:
            return ResultadoSugerencias(
                fuentes_usadas=len(fuentes_payload),
            )

        callback = on_progress or _noop_progress
        semaforo = asyncio.Semaphore(concurrencia)
        completadas_lock = asyncio.Lock()
        completadas = 0
        pobladas = 0
        errores: list[str] = []

        async def procesar_una(seccion: Seccion) -> None:
            nonlocal completadas, pobladas

            async with semaforo:
                estado: str = "sin_info"
                error_msg: str | None = None
                try:
                    draft = await self._sugerir_para_seccion_async(
                        documento,
                        seccion_nombre=seccion.nombre,
                        seccion_descripcion=seccion.intencion or seccion.nombre,
                        fuentes=fuentes_payload,
                    )
                    if draft and "[Sin información en fuentes adjuntas]" not in draft:
                        # Edición in-place del documento — Python no necesita lock
                        # porque cada coroutine toca una sección distinta del dict.
                        seccion.contenido = f"{prefijo_borrador}\n\n{draft.strip()}"
                        seccion.completitud = "parcial"
                        estado = "poblada"
                except Exception as exc:
                    msg = (
                        f"Sección {seccion.id}: falló la sugerencia LLM ({exc.__class__.__name__})"
                    )
                    logger.warning(msg, exc_info=True)
                    estado = "error"
                    error_msg = msg

            # Fuera del semáforo: actualizar contadores + emitir progreso.
            # El lock evita race conditions en los contadores.
            async with completadas_lock:
                completadas += 1
                if estado == "poblada":
                    pobladas += 1
                if error_msg:
                    errores.append(error_msg)
                idx_actual = completadas

            await callback(
                EventoProgreso(
                    seccion_id=seccion.id,
                    seccion_nombre=seccion.nombre,
                    seccion_numero=seccion.numero,
                    completadas=idx_actual,
                    total=total,
                    estado=estado,
                    error=error_msg,
                )
            )

        # Lanzar todas las coroutines con gather. El semáforo limita la
        # concurrencia real a N llamadas simultáneas.
        await asyncio.gather(
            *(procesar_una(s) for s in secciones_a_procesar),
            return_exceptions=False,
        )

        return ResultadoSugerencias(
            secciones_pobladas=pobladas,
            secciones_intentadas=total,
            errores=errores,
            fuentes_usadas=len(fuentes_payload),
        )

    async def _sugerir_para_seccion_async(
        self,
        documento: Documento,
        *,
        seccion_nombre: str,
        seccion_descripcion: str,
        fuentes: list[tuple[str, str]],
    ) -> str:
        """Llamada LLM asíncrona para una sola sección.

        Mantenemos `_sugerir_para_seccion` síncrono por compatibilidad con
        tests viejos que pueden mockearlo directamente; esta versión async
        existe para el flujo paralelizado.
        """
        system_blocks: list[TextBlockParam] = [
            {"type": "text", "text": SUGERENCIAS_MULTIFUENTE_SYSTEM}
        ]
        user_msg = construir_prompt_seccion(
            seccion_nombre=seccion_nombre,
            seccion_descripcion=seccion_descripcion,
            fuentes=fuentes,
        )
        messages: list[MessageParam] = [{"role": "user", "content": user_msg}]

        respuesta = await self.llm.chat_async(
            tarea="chat",
            system_blocks=system_blocks,
            messages=messages,
            max_tokens=2048,
        )
        # Edición in-place de métricas — Python list/dict son thread-safe
        # bajo GIL y bajo asyncio mono-thread; está OK sin lock.
        documento.metricas_uso.agregar(
            construir_llamada(
                modelo=respuesta.modelo_usado,
                tarea="chat",
                input_tokens=respuesta.input_tokens,
                output_tokens=respuesta.output_tokens,
                cache_read_tokens=respuesta.cache_read_tokens,
                cache_creation_tokens=respuesta.cache_creation_tokens,
            )
        )
        return respuesta.text.strip()

    def _sugerir_para_seccion(
        self,
        documento: Documento,
        *,
        seccion_nombre: str,
        seccion_descripcion: str,
        fuentes: list[tuple[str, str]],
    ) -> str:
        """Versión síncrona — preservada para compatibilidad con tests viejos.

        Delega a la versión async via asyncio.run. NO se usa en el flujo
        principal (que ahora es full async); está aquí para que mocks
        existentes sigan funcionando.
        """
        return asyncio.run(
            self._sugerir_para_seccion_async(
                documento,
                seccion_nombre=seccion_nombre,
                seccion_descripcion=seccion_descripcion,
                fuentes=fuentes,
            )
        )
