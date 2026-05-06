"""Métricas de uso del LLM acumuladas por Documento.

Captura tokens consumidos y costo estimado en USD a través de toda la vida
del documento. Permite mostrar al usuario "Costo de generación: $X USD"
y validar que el prompt caching está funcionando (cache_hit_rate > 50%).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LlamadaLLM(BaseModel):
    """Una llamada individual al LLM, registrada para auditoría y costo."""

    model_config = ConfigDict(frozen=True)

    modelo: str
    """ID del modelo usado, ej. 'claude-opus-4-7'."""
    tarea: str
    """Tarea: 'chat' | 'drafting' | 'extraction'."""
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    costo_usd: float = 0.0


class MetricasUso(BaseModel):
    """Métricas acumuladas de uso del LLM por documento."""

    model_config = ConfigDict(str_strip_whitespace=True)

    llamadas: list[LlamadaLLM] = Field(default_factory=list)

    @property
    def total_input_tokens(self) -> int:
        return sum(ll.input_tokens for ll in self.llamadas)

    @property
    def total_output_tokens(self) -> int:
        return sum(ll.output_tokens for ll in self.llamadas)

    @property
    def total_cache_read_tokens(self) -> int:
        return sum(ll.cache_read_tokens for ll in self.llamadas)

    @property
    def total_cache_creation_tokens(self) -> int:
        return sum(ll.cache_creation_tokens for ll in self.llamadas)

    @property
    def costo_total_usd(self) -> float:
        return sum(ll.costo_usd for ll in self.llamadas)

    @property
    def cache_hit_rate(self) -> float:
        """Fracción de tokens de input servidos desde cache (0.0 - 1.0).

        Si es < 0.5 después de varias llamadas, hay un silent invalidator.
        """
        total_input_equiv = (
            self.total_input_tokens
            + self.total_cache_read_tokens
            + self.total_cache_creation_tokens
        )
        if total_input_equiv == 0:
            return 0.0
        return self.total_cache_read_tokens / total_input_equiv

    def agregar(self, llamada: LlamadaLLM) -> None:
        self.llamadas.append(llamada)
