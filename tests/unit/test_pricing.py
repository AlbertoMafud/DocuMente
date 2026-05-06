"""Tests de pricing.py — cálculo de costo de llamadas LLM."""

from __future__ import annotations

import pytest

from src.llm.pricing import construir_llamada, costo_usd


def test_costo_opus_input_only() -> None:
    # 1M tokens de input a $5/MTok = $5
    assert costo_usd("claude-opus-4-7", 1_000_000, 0, 0, 0) == pytest.approx(5.0)


def test_costo_opus_full() -> None:
    # 100K input + 10K output + 50K cache_read + 0 cache_write
    # = 100K * 5 + 10K * 25 + 50K * 0.5 = 500 + 250 + 25 = 775 USD por millón
    # = 0.775 USD por las cantidades dadas
    c = costo_usd("claude-opus-4-7", 100_000, 10_000, 50_000, 0)
    assert c == pytest.approx(0.775)


def test_costo_sonnet_es_menor_que_opus() -> None:
    args = (100_000, 10_000, 0, 0)
    sonnet = costo_usd("claude-sonnet-4-6", *args)
    opus = costo_usd("claude-opus-4-7", *args)
    assert sonnet < opus
    # Sonnet input es $3 vs Opus $5 → ratio aprox 0.6
    assert sonnet / opus < 0.65


def test_costo_haiku_es_minimo() -> None:
    args = (100_000, 10_000, 0, 0)
    haiku = costo_usd("claude-haiku-4-5", *args)
    sonnet = costo_usd("claude-sonnet-4-6", *args)
    assert haiku < sonnet


def test_costo_modelo_desconocido_devuelve_cero() -> None:
    """No debe romper la app si llega un modelo no reconocido."""
    assert costo_usd("modelo-inexistente", 1000, 1000, 0, 0) == 0.0


def test_construir_llamada_calcula_costo() -> None:
    ll = construir_llamada(
        modelo="claude-haiku-4-5",
        tarea="extraction",
        input_tokens=10_000,
        output_tokens=500,
        cache_read_tokens=0,
        cache_creation_tokens=0,
    )
    assert ll.modelo == "claude-haiku-4-5"
    assert ll.tarea == "extraction"
    # 10K * $1/MTok + 500 * $5/MTok = 0.01 + 0.0025 = 0.0125
    assert ll.costo_usd == pytest.approx(0.0125)
