"""Tests del catálogo de cadenas localizadas ES/EN."""

from __future__ import annotations

from src.core.usecases.strings_localizados import (
    MOTIVOS_PREDEFINIDOS_ES,
    STRINGS_UI,
    t,
    traducir_motivo_predefinido,
)


def test_t_devuelve_traduccion_es() -> None:
    assert t("seccion_omitida_prefijo", "es") == "Sección omitida — "


def test_t_devuelve_traduccion_en() -> None:
    assert t("seccion_omitida_prefijo", "en") == "Section omitted — "


def test_t_clave_inexistente_devuelve_marcador_visible() -> None:
    """Una clave que no existe devuelve `<missing:key>` para detectar en QA."""
    assert t("clave_que_no_existe", "es") == "<missing:clave_que_no_existe>"
    assert t("clave_que_no_existe", "en") == "<missing:clave_que_no_existe>"


def test_todas_las_claves_tienen_ambos_idiomas() -> None:
    """Garantía estructural: ninguna clave puede tener solo ES o solo EN."""
    for clave, traducciones in STRINGS_UI.items():
        assert "es" in traducciones, f"Clave '{clave}' sin traducción ES"
        assert "en" in traducciones, f"Clave '{clave}' sin traducción EN"
        assert traducciones["es"].strip(), f"Clave '{clave}' ES vacía"
        assert traducciones["en"].strip(), f"Clave '{clave}' EN vacía"


def test_motivos_predefinidos_listan_los_4_motivos_es() -> None:
    """La lista debe contener los 4 motivos predefinidos en español."""
    assert "No aplica al modelo" in MOTIVOS_PREDEFINIDOS_ES
    assert "Información no disponible" in MOTIVOS_PREDEFINIDOS_ES
    assert "Pendiente para versión futura" in MOTIVOS_PREDEFINIDOS_ES
    assert "Otro (especificar)" in MOTIVOS_PREDEFINIDOS_ES
    assert len(MOTIVOS_PREDEFINIDOS_ES) == 4


def test_traducir_motivo_predefinido_swap_directo_es_a_en() -> None:
    """Motivo predefinido en ES → traducción directa al EN."""
    assert traducir_motivo_predefinido("No aplica al modelo", "en") == "Not applicable to the model"
    assert (
        traducir_motivo_predefinido("Información no disponible", "en")
        == "Information not available"
    )


def test_traducir_motivo_predefinido_es_a_es_devuelve_mismo() -> None:
    assert traducir_motivo_predefinido("No aplica al modelo", "es") == "No aplica al modelo"


def test_traducir_motivo_predefinido_no_predefinido_devuelve_none() -> None:
    """Motivo libre no coincide con ningún predefinido → None."""
    assert traducir_motivo_predefinido("Texto libre del usuario", "en") is None


def test_motivos_de_omitir_seccion_coinciden_con_predefinidos() -> None:
    """Los MOTIVOS_OMISION del use case deben coincidir con los predefinidos
    del catálogo localizado (un solo punto de verdad)."""
    from src.core.usecases.omitir_seccion import MOTIVOS_OMISION

    assert tuple(MOTIVOS_OMISION) == MOTIVOS_PREDEFINIDOS_ES


def test_apendice_en_singular_en_es_y_appendix_en_en() -> None:
    assert t("apendice_singular", "es") == "Apéndice"
    assert t("apendice_singular", "en") == "Appendix"
