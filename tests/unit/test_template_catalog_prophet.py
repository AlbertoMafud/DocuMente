from __future__ import annotations

from src.core.template_catalog_prophet import (
    TEMPLATE_PROPHET,
    construir_secciones_vacias_prophet,
    por_id_prophet,
)


def test_template_tiene_12_secciones() -> None:
    assert len(TEMPLATE_PROPHET) == 12


def test_ids_son_unicos() -> None:
    ids = [s.id for s in TEMPLATE_PROPHET]
    assert len(ids) == len(set(ids))


def test_tipo_contenido_valido() -> None:
    for s in TEMPLATE_PROPHET:
        assert s.tipo_contenido in {"campos", "tabla", "texto"}, (
            f"{s.id} tiene tipo inválido: {s.tipo_contenido}"
        )


def test_tablas_tienen_schema() -> None:
    for s in TEMPLATE_PROPHET:
        if s.tipo_contenido == "tabla":
            assert len(s.schema_tabla) > 0, f"{s.id}: tabla sin schema_tabla"


def test_secciones_obligatorias_correctas() -> None:
    obligatorias = {s.id for s in TEMPLATE_PROPHET if s.obligatoria}
    for esperada in (
        "identificacion",
        "corridas_runs",
        "variables_criticas",
        "matriz_conocimiento",
    ):
        assert esperada in obligatorias


def test_secciones_opcionales_correctas() -> None:
    opcionales = {s.id for s in TEMPLATE_PROPHET if not s.obligatoria}
    assert "componentes_librerias" in opcionales
    assert "limitaciones_riesgos" in opcionales


def test_por_id_prophet_encontrado() -> None:
    s = por_id_prophet("corridas_runs")
    assert s is not None and s.nombre == "Corridas (Runs)"


def test_por_id_prophet_inexistente() -> None:
    assert por_id_prophet("no_existe") is None


def test_construir_secciones_vacias_prophet() -> None:
    secciones = construir_secciones_vacias_prophet()
    assert len(secciones) == 12
    for s in secciones:
        assert s.completitud == "vacia"
        assert s.contenido is None
