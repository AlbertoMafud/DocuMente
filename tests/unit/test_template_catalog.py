"""Tests del catálogo de secciones del template oficial."""

from __future__ import annotations

from src.core.template_catalog import TEMPLATE_MODEL_DEVELOPMENT, por_id


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
