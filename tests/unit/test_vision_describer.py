"""Tests unitarios para VisionDescriber — cache, degradación, llamadas LLM."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.llm.client import LLMResponse
from src.llm.vision_describer import VisionDescriber


def _llm_fake_response(texto: str) -> LLMResponse:
    return LLMResponse(
        text=texto,
        modelo_usado="claude-haiku-4-5",
        input_tokens=100,
        output_tokens=20,
        cache_read_tokens=0,
        cache_creation_tokens=0,
    )


def test_describe_primera_vez_llama_al_llm_y_guarda_en_cache(tmp_path: Path) -> None:
    llm = MagicMock()
    llm.chat.return_value = _llm_fake_response("Screenshot de Prophet mostrando DCF Browser.")

    describer = VisionDescriber(llm=llm, cache_path=tmp_path / "cache.json")

    desc = describer.describir(b"\x89PNG\r\n\x1a\n" + b"fake-png-bytes")

    assert "Prophet" in desc.descripcion
    assert desc.desde_cache is False
    llm.chat.assert_called_once()

    # cache file persistido
    assert (tmp_path / "cache.json").exists()
    cache_data = json.loads((tmp_path / "cache.json").read_text(encoding="utf-8"))
    assert desc.sha256 in cache_data


def test_describe_segunda_vez_misma_imagen_usa_cache(tmp_path: Path) -> None:
    llm = MagicMock()
    llm.chat.return_value = _llm_fake_response("Screenshot original")

    describer = VisionDescriber(llm=llm, cache_path=tmp_path / "cache.json")

    img_bytes = b"\x89PNG-bytes-misma-imagen"
    primera = describer.describir(img_bytes)
    segunda = describer.describir(img_bytes)

    assert primera.descripcion == segunda.descripcion
    assert primera.sha256 == segunda.sha256
    assert primera.desde_cache is False
    assert segunda.desde_cache is True
    # LLM solo se llamó una vez
    assert llm.chat.call_count == 1


def test_describe_imagenes_distintas_genera_descripciones_distintas(
    tmp_path: Path,
) -> None:
    llm = MagicMock()
    llm.chat.side_effect = [
        _llm_fake_response("Descripción de la imagen A"),
        _llm_fake_response("Descripción de la imagen B"),
    ]

    describer = VisionDescriber(llm=llm, cache_path=tmp_path / "cache.json")

    desc_a = describer.describir(b"imagen-a-bytes")
    desc_b = describer.describir(b"imagen-b-bytes")

    assert desc_a.sha256 != desc_b.sha256
    assert desc_a.descripcion != desc_b.descripcion
    assert llm.chat.call_count == 2


def test_describe_si_llm_falla_devuelve_placeholder_sin_crashear(
    tmp_path: Path,
) -> None:
    llm = MagicMock()
    llm.chat.side_effect = RuntimeError("API no disponible (red caída)")

    describer = VisionDescriber(llm=llm, cache_path=tmp_path / "cache.json")
    desc = describer.describir(b"imagen-cualquier-bytes")

    assert "no descrita" in desc.descripcion.lower()
    assert desc.desde_cache is False
    # El fallo NO se cachea — la próxima vez vuelve a intentar
    cache_path = tmp_path / "cache.json"
    if cache_path.exists():
        cache_data = json.loads(cache_path.read_text(encoding="utf-8"))
        assert desc.sha256 not in cache_data


def test_cache_persistido_se_lee_al_instanciar(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.json"
    sha_precargado = "a" * 64
    cache_path.write_text(
        json.dumps({sha_precargado: "Descripción precargada desde JSON"}),
        encoding="utf-8",
    )

    llm = MagicMock()
    describer = VisionDescriber(llm=llm, cache_path=cache_path)

    # Si la imagen tiene ese sha exacto (hardcodeamos para test), debe devolver cache.
    # Simulamos con un input que produzca ese hash es imposible — pero podemos
    # verificar que el cache se cargó inspeccionando el atributo interno.
    assert describer._cache == {sha_precargado: "Descripción precargada desde JSON"}
    llm.chat.assert_not_called()


def test_media_type_pasa_al_llm_correctamente(tmp_path: Path) -> None:
    llm = MagicMock()
    llm.chat.return_value = _llm_fake_response("descripcion")

    describer = VisionDescriber(llm=llm, cache_path=tmp_path / "cache.json")
    describer.describir(b"jpeg-bytes", media_type="image/jpeg")

    _args, kwargs = llm.chat.call_args
    messages = kwargs["messages"]
    image_block = messages[0]["content"][0]
    assert image_block["type"] == "image"
    assert image_block["source"]["media_type"] == "image/jpeg"


@pytest.mark.parametrize(
    "tarea_esperada",
    ["vision"],
)
def test_describer_usa_tier_vision(tmp_path: Path, tarea_esperada: str) -> None:
    llm = MagicMock()
    llm.chat.return_value = _llm_fake_response("ok")

    describer = VisionDescriber(llm=llm, cache_path=tmp_path / "cache.json")
    describer.describir(b"imagen")

    _args, kwargs = llm.chat.call_args
    assert kwargs["tarea"] == tarea_esperada
