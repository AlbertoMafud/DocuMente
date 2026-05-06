"""Tarifas oficiales de Anthropic por modelo y cálculo de costo de llamadas.

Fuente: https://www.anthropic.com/pricing y `shared/models.md` del skill claude-api.
Precios en USD por millón de tokens.

Mantenimiento: cuando Anthropic actualice precios, ajustar aquí.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.core.models import LlamadaLLM


@dataclass(frozen=True)
class TarifaModelo:
    """Tarifas en USD por millón de tokens."""

    input_per_mtok: float
    output_per_mtok: float
    cache_read_per_mtok: float
    """Cache read es ~10% del input estándar."""
    cache_write_per_mtok: float
    """Cache write (5min TTL) es ~125% del input estándar."""


# Tarifas vigentes (cacheadas: 2026-04-15, ver shared/models.md)
TARIFAS: dict[str, TarifaModelo] = {
    "claude-opus-4-7": TarifaModelo(
        input_per_mtok=5.00,
        output_per_mtok=25.00,
        cache_read_per_mtok=0.50,
        cache_write_per_mtok=6.25,
    ),
    "claude-opus-4-6": TarifaModelo(
        input_per_mtok=5.00,
        output_per_mtok=25.00,
        cache_read_per_mtok=0.50,
        cache_write_per_mtok=6.25,
    ),
    "claude-sonnet-4-6": TarifaModelo(
        input_per_mtok=3.00,
        output_per_mtok=15.00,
        cache_read_per_mtok=0.30,
        cache_write_per_mtok=3.75,
    ),
    "claude-haiku-4-5": TarifaModelo(
        input_per_mtok=1.00,
        output_per_mtok=5.00,
        cache_read_per_mtok=0.10,
        cache_write_per_mtok=1.25,
    ),
}


def costo_usd(
    modelo: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
    cache_creation_tokens: int,
) -> float:
    """Calcula el costo en USD de una llamada al LLM."""
    tarifa = TARIFAS.get(modelo)
    if tarifa is None:
        # Modelo desconocido: log silencioso, costo 0. Evita romper la app.
        return 0.0
    return (
        input_tokens * tarifa.input_per_mtok
        + output_tokens * tarifa.output_per_mtok
        + cache_read_tokens * tarifa.cache_read_per_mtok
        + cache_creation_tokens * tarifa.cache_write_per_mtok
    ) / 1_000_000


def construir_llamada(
    modelo: str,
    tarea: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
    cache_creation_tokens: int,
) -> LlamadaLLM:
    """Construye un `LlamadaLLM` con el costo ya calculado."""
    return LlamadaLLM(
        modelo=modelo,
        tarea=tarea,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_creation_tokens=cache_creation_tokens,
        costo_usd=costo_usd(
            modelo=modelo,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_creation_tokens=cache_creation_tokens,
        ),
    )
