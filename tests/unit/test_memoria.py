"""Tests del modelo MemoriaModelo."""

from __future__ import annotations

from src.core.models import MemoriaModelo


def test_memoria_vacia_no_renderiza_para_prompt() -> None:
    m = MemoriaModelo()
    assert m.esta_vacia is True
    assert m.renderizar_para_prompt() == ""


def test_memoria_con_hechos_se_renderiza() -> None:
    m = MemoriaModelo(plataforma="Prophet", frecuencia_corridas="mensual")
    rendered = m.renderizar_para_prompt()
    assert "Prophet" in rendered
    assert "mensual" in rendered
    assert "no preguntes por estos" in rendered.lower()


def test_actualizar_desde_dict_merge_aditivo() -> None:
    m = MemoriaModelo(plataforma="Prophet")
    cambios = m.actualizar_desde_dict(
        {
            "lenguaje_codigo": "R",
            "rutas_principales": ["/data/inputs/"],
            "plataforma": "GGY Axis",  # NO debe sobrescribir Prophet
        },
        fuente="extraccion:test",
    )
    assert cambios is True
    assert m.plataforma == "Prophet", "No debe sobrescribir hechos existentes"
    assert m.lenguaje_codigo == "R"
    assert "/data/inputs/" in m.rutas_principales


def test_actualizar_desde_dict_no_duplica_listas() -> None:
    m = MemoriaModelo(rutas_principales=["/a/", "/b/"])
    cambios = m.actualizar_desde_dict({"rutas_principales": ["/a/", "/c/"]}, fuente="test")
    assert cambios is True
    assert m.rutas_principales == ["/a/", "/b/", "/c/"]


def test_actualizar_dict_vacio_no_marca_cambios() -> None:
    m = MemoriaModelo(plataforma="Prophet")
    cambios = m.actualizar_desde_dict({}, fuente="test")
    assert cambios is False
