"""Tests del catálogo de secciones del template oficial."""

from __future__ import annotations

from src.core.models import Seccion
from src.core.template_catalog import (
    TEMPLATE_MODEL_DEVELOPMENT,
    construir_secciones_vacias,
    por_id,
)


def test_catalogo_tiene_secciones() -> None:
    assert len(TEMPLATE_MODEL_DEVELOPMENT) >= 28


def test_catalogo_tiene_secciones_obligatorias() -> None:
    obligatorias = [s for s in TEMPLATE_MODEL_DEVELOPMENT if s.obligatoria]
    # Según TEMPLATE_MODEL_DEV.md hay >= 22 secciones obligatorias
    assert len(obligatorias) >= 22


def test_secciones_criticas_mrm_estan_en_catalogo() -> None:
    """Las secciones críticas para MRM (supuestos, limitaciones) deben existir."""
    ids = {s.id for s in TEMPLATE_MODEL_DEVELOPMENT}
    assert "4.4.assumptions" in ids
    assert "5.4.data_limitations" in ids
    assert "6.4.limitations" in ids
    assert "4.3.risk_drivers" in ids


def test_por_id_devuelve_seccion_correcta() -> None:
    sec = por_id("4.4.assumptions")
    assert sec is not None
    assert sec.nombre == "Key Assumptions"
    assert sec.obligatoria is True


def test_por_id_no_existente_devuelve_none() -> None:
    assert por_id("99.99.inexistente") is None


def test_aliases_incluyen_traducciones_smnyl() -> None:
    """Validamos que los aliases reconozcan headings en español que usa SMNYL."""
    sec_objetivo = next(
        (s for s in TEMPLATE_MODEL_DEVELOPMENT if "objetivo" in [a.lower() for a in s.aliases]),
        None,
    )
    assert sec_objetivo is not None, "Debería haber una sección con alias 'objetivo'"


def test_construir_secciones_vacias_devuelve_una_por_entrada_del_catalogo() -> None:
    secciones = construir_secciones_vacias()
    assert len(secciones) == len(TEMPLATE_MODEL_DEVELOPMENT)


def test_construir_secciones_vacias_devuelve_lista_de_secciones() -> None:
    secciones = construir_secciones_vacias()
    assert all(isinstance(s, Seccion) for s in secciones)


def test_construir_secciones_vacias_preserva_intencion_y_preguntas() -> None:
    secciones = construir_secciones_vacias()
    cat_por_id = {c.id: c for c in TEMPLATE_MODEL_DEVELOPMENT}
    for seccion in secciones:
        cat = cat_por_id[seccion.id]
        assert seccion.nombre == cat.nombre
        assert seccion.numero == cat.numero
        assert seccion.obligatoria == cat.obligatoria
        assert seccion.intencion == cat.intencion
        assert seccion.preguntas_guia == list(cat.preguntas_guia)


def test_construir_secciones_vacias_devuelve_secciones_vacias() -> None:
    secciones = construir_secciones_vacias()
    for seccion in secciones:
        assert seccion.contenido is None
        assert seccion.completitud == "vacia"
        assert seccion.motivo_omision is None


def test_construir_secciones_vacias_devuelve_lista_independiente() -> None:
    """Cada llamada devuelve secciones nuevas — no comparte estado."""
    a = construir_secciones_vacias()
    b = construir_secciones_vacias()
    a[0].contenido = "test"
    assert b[0].contenido is None
