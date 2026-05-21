"""LLMClient: interfaz + implementación con Anthropic SDK (estrategia tiered).

Diseñado con tres premisas:

1. **Interfaz `LLMClient` como Protocol** — la lógica de negocio depende de la
   interfaz, no de Anthropic. Migrar a Bedrock o a otro proveedor implica
   implementar la interfaz, no reescribir use cases.
2. **Prompt caching agresivo** — el contexto fijo (template oficial NYL +
   extracto MRM + lineamientos de marca + tono) son ~12K tokens que se
   repiten en cada llamada de la sesión. Cachearlos ahorra ~90% de costo y
   tiempo después de la primera llamada.
3. **Estrategia tiered de modelos** — cada tarea usa el modelo apropiado:
   - `chat` (entrevista) → Sonnet 4.6 (excelente conversacional, ~3× más barato que Opus)
   - `drafting` (borrador final) → Opus 4.7 (calidad institucional)
   - `extraction` (extracción de hechos) → Haiku 4.5 (rapidísimo, baratísimo)
   - `vision` (describir imágenes embebidas) → Haiku 4.5 multimodal
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

import anthropic
from anthropic.types import MessageParam, TextBlockParam

from src.config import get_settings

Tarea = Literal["chat", "drafting", "extraction", "vision"]


# Mapeo default de tarea → modelo. Override-able vía Settings.
_MODELO_POR_TAREA_DEFAULT: dict[Tarea, str] = {
    "chat": "claude-sonnet-4-6",
    "drafting": "claude-opus-4-7",
    "extraction": "claude-haiku-4-5",
    "vision": "claude-haiku-4-5",
}


@dataclass(frozen=True)
class LLMResponse:
    """Respuesta del LLM en formato neutral al proveedor."""

    text: str
    """Texto generado por el modelo."""

    modelo_usado: str
    """ID del modelo que produjo la respuesta. Necesario para calcular costo."""

    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    """Tokens leídos de la cache (≈10% del costo de input)."""
    cache_creation_tokens: int
    """Tokens escritos a la cache (≈125% del costo de input, primera vez)."""

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_creation_tokens
        )


class LLMClient(Protocol):
    """Interfaz neutral al proveedor de LLM.

    Implementaciones disponibles:
    - `AnthropicClient`: usa Anthropic SDK directo con estrategia tiered.
    - `BedrockClient` (post-MVP): mismo modelo Claude vía AWS Bedrock.

    Ofrece tanto interfaz síncrona (`chat`) como asíncrona (`chat_async`).
    Los use cases legacy usan síncrona; flujos que necesitan paralelizar
    múltiples llamadas (SugerenciasMultiFuente, streaming) usan async.
    """

    def chat(
        self,
        *,
        tarea: Tarea,
        system_blocks: list[TextBlockParam],
        messages: list[MessageParam],
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Manda un turno al LLM (sincrónico) y devuelve la respuesta.

        Args:
            tarea: tipo de trabajo, mapea internamente al modelo apropiado.
            system_blocks: bloques de system prompt. Marcar bloques estables con
                `cache_control={"type": "ephemeral"}` para cachear el prefijo.
            messages: historia de la conversación (turnos user/assistant).
            max_tokens: techo de tokens en la respuesta.
        """
        ...

    async def chat_async(
        self,
        *,
        tarea: Tarea,
        system_blocks: list[TextBlockParam],
        messages: list[MessageParam],
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Versión async de `chat` — permite `asyncio.gather` para paralelizar
        múltiples llamadas. Misma semántica + mismos kwargs que `chat`.
        """
        ...


class AnthropicClient:
    """Implementación de `LLMClient` con Anthropic SDK + estrategia tiered.

    El modelo a usar se decide por `tarea` en cada llamada (no se fija al
    instanciar). Esto permite a un solo cliente servir entrevista, drafting
    y extracción sin reconfiguración.
    """

    def __init__(self, modelos_override: dict[Tarea, str] | None = None) -> None:
        """Construye el cliente.

        Args:
            modelos_override: si se pasa, sobreescribe el mapeo default
                tarea→modelo. Útil para tests o para forzar todo a Opus.
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY no está configurada. Agrégala a .env "
                "(ver .env.example) antes de usar el LLMClient."
            )
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        # AsyncAnthropic comparte la API key + el pool de conexiones — usar
        # ambos clientes en el mismo proceso es seguro. Existe desde
        # anthropic SDK ≥0.50.
        self._async_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._modelos: dict[Tarea, str] = {
            **_MODELO_POR_TAREA_DEFAULT,
            **(modelos_override or {}),
        }

    def modelo_para(self, tarea: Tarea) -> str:
        """Devuelve el ID del modelo que se usará para una tarea."""
        return self._modelos[tarea]

    def _construir_kwargs(
        self,
        *,
        tarea: Tarea,
        system_blocks: list[TextBlockParam],
        messages: list[MessageParam],
        max_tokens: int,
    ) -> tuple[str, dict[str, Any]]:
        """Devuelve `(modelo_id, kwargs)` listos para `messages.create(**kwargs)`.

        Compartido entre `chat` (sync) y `chat_async` para no duplicar la
        lógica de tier + thinking + effort.
        """
        modelo = self._modelos[tarea]
        kwargs: dict[str, Any] = {
            "model": modelo,
            "max_tokens": max_tokens,
            "system": system_blocks,
            "messages": messages,
        }

        # Adaptive thinking + effort según tarea.
        if tarea == "drafting":
            kwargs["thinking"] = {"type": "adaptive"}
            kwargs["output_config"] = {"effort": "high"}
        elif tarea == "chat":
            kwargs["thinking"] = {"type": "adaptive"}
            kwargs["output_config"] = {"effort": "medium"}
        else:  # extraction y vision
            # Haiku 4.5 NO soporta `effort` ni adaptive thinking confiablemente.
            kwargs["thinking"] = {"type": "disabled"}

        return modelo, kwargs

    @staticmethod
    def _parsear_respuesta(response: Any, modelo: str) -> LLMResponse:
        """Convierte la respuesta cruda del SDK en `LLMResponse` neutral."""
        text = "".join(
            block.text  # type: ignore[union-attr]
            for block in response.content
            if block.type == "text"
        )
        usage = response.usage
        return LLMResponse(
            text=text,
            modelo_usado=modelo,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        )

    def chat(
        self,
        *,
        tarea: Tarea,
        system_blocks: list[TextBlockParam],
        messages: list[MessageParam],
        max_tokens: int = 4096,
    ) -> LLMResponse:
        modelo, kwargs = self._construir_kwargs(
            tarea=tarea,
            system_blocks=system_blocks,
            messages=messages,
            max_tokens=max_tokens,
        )
        response = self._client.messages.create(**kwargs)
        return self._parsear_respuesta(response, modelo)

    async def chat_async(
        self,
        *,
        tarea: Tarea,
        system_blocks: list[TextBlockParam],
        messages: list[MessageParam],
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Async equivalente de `chat`. Apto para `asyncio.gather` con N tareas
        en paralelo. Usa el mismo modelo, mismo kwargs, mismo parser.

        Atención: el SDK AsyncAnthropic respeta los rate limits del tier de la
        cuenta. Si paralelizamos demasiadas llamadas, el SDK devuelve 429.
        Mitigación recomendada en el caller: `asyncio.Semaphore(5)` o similar.
        """
        modelo, kwargs = self._construir_kwargs(
            tarea=tarea,
            system_blocks=system_blocks,
            messages=messages,
            max_tokens=max_tokens,
        )
        response = await self._async_client.messages.create(**kwargs)
        return self._parsear_respuesta(response, modelo)
