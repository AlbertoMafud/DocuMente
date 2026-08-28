"""Tests del registro de templates (Template Studio S-A).

Cubren: envoltura de los catálogos congelados (MRM, Prophet) sin tocarlos,
resolución de dinámicos publicados desde BD, error para tipos desconocidos,
y construcción de secciones vacías desde cualquier spec.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.models.template_dinamico import (
    SeccionCatalogoDinamica,
    TemplateDinamico,
)
from src.core.template_catalog import TEMPLATE_MODEL_DEVELOPMENT
from src.core.template_catalog_prophet import TEMPLATE_PROPHET
from src.core.template_registry import (
    TemplateDesconocidoError,
    construir_secciones_desde_spec,
    listar_templates,
    resolver_template,
)
from src.storage.repositories import TemplateDinamicoRepository


@pytest.fixture
def bd_aislada(monkeypatch, tmp_path: Path):
    """BD SQLite efímera para los tests que tocan dinámicos."""
    db_file = tmp_path / "test_registry.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    import src.storage.db as db_mod

    db_mod._engine = None
    db_mod._SessionLocal = None
    yield
    db_mod._engine = None
    db_mod._SessionLocal = None


def _template_dinamico(slug: str = "procedimiento_operativo", estado: str = "publicado"):
    return TemplateDinamico(
        slug=slug,
        nombre="Ficha de Procedimiento Operativo",
        estado=estado,  # type: ignore[arg-type]
        secciones=[
            SeccionCatalogoDinamica(
                id="1.objetivo",
                numero="1",
                nombre="Objetivo",
                obligatoria=True,
                intencion="Qué logra el procedimiento y para quién.",
                preguntas_guia=["¿Qué problema resuelve este procedimiento?"],
            ),
            SeccionCatalogoDinamica(
                id="2.responsables",
                numero="2",
                nombre="Responsables",
                obligatoria=True,
                intencion="Quién ejecuta, valida y aprueba.",
                tipo_contenido="tabla",
                schema_tabla=["persona", "rol"],
            ),
        ],
    )


# --- Templates de código (sin BD) ---


def test_resolver_mrm_envuelve_las_28_secciones() -> None:
    spec = resolver_template("model_development")
    assert spec.origen == "codigo"
    assert spec.writer == "mrm"
    assert len(spec.catalogo) == len(TEMPLATE_MODEL_DEVELOPMENT) == 28


def test_resolver_mrm_preserva_campos_ai_ready() -> None:
    spec = resolver_template("model_development")
    original = TEMPLATE_MODEL_DEVELOPMENT[0]
    envuelta = spec.catalogo[0]
    assert envuelta.id == original.id
    assert envuelta.intencion == original.intencion
    assert envuelta.aliases == list(original.aliases)
    assert envuelta.preguntas_guia == list(original.preguntas_guia)
    assert envuelta.tipo_contenido == "texto"


def test_resolver_prophet_preserva_tipo_contenido_y_schema() -> None:
    spec = resolver_template("prophet")
    assert spec.writer == "prophet"
    assert len(spec.catalogo) == len(TEMPLATE_PROPHET) == 12
    corridas = next(s for s in spec.catalogo if s.id == "corridas_runs")
    assert corridas.tipo_contenido == "tabla"
    assert "corrida_precedente" in corridas.schema_tabla


def test_los_catalogos_congelados_no_se_mutan() -> None:
    """Resolver dos veces no comparte estado mutable con los congelados."""
    spec1 = resolver_template("model_development")
    spec1.catalogo[0].aliases.append("hackeado")
    spec2 = resolver_template("model_development")
    assert "hackeado" not in spec2.catalogo[0].aliases
    assert "hackeado" not in TEMPLATE_MODEL_DEVELOPMENT[0].aliases


def test_construir_secciones_desde_spec_mrm_equivale_al_builder_legacy() -> None:
    from src.core.template_catalog import construir_secciones_vacias

    via_registro = construir_secciones_desde_spec(resolver_template("model_development"))
    via_legacy = construir_secciones_vacias()
    assert [s.id for s in via_registro] == [s.id for s in via_legacy]
    assert [s.preguntas_guia for s in via_registro] == [s.preguntas_guia for s in via_legacy]


# --- Dinámicos (con BD) ---


def test_resolver_dinamico_publicado(bd_aislada) -> None:
    TemplateDinamicoRepository().guardar(_template_dinamico())
    spec = resolver_template("procedimiento_operativo")
    assert spec.origen == "dinamico"
    assert spec.writer == "generico"
    assert spec.ruta_plantilla_word is None
    assert len(spec.catalogo) == 2


def test_resolver_dinamico_no_publicado_falla(bd_aislada) -> None:
    TemplateDinamicoRepository().guardar(_template_dinamico(estado="borrador"))
    with pytest.raises(TemplateDesconocidoError):
        resolver_template("procedimiento_operativo")


def test_resolver_tipo_desconocido_falla(bd_aislada) -> None:
    with pytest.raises(TemplateDesconocidoError):
        resolver_template("no_existe")


def test_listar_incluye_codigos_y_dinamicos_publicados(bd_aislada) -> None:
    repo = TemplateDinamicoRepository()
    repo.guardar(_template_dinamico())
    repo.guardar(_template_dinamico(slug="otro_borrador", estado="borrador"))
    ids = [t.id for t in listar_templates()]
    assert "model_development" in ids
    assert "prophet" in ids
    assert "procedimiento_operativo" in ids
    assert "otro_borrador" not in ids


def test_construir_secciones_desde_spec_dinamico(bd_aislada) -> None:
    TemplateDinamicoRepository().guardar(_template_dinamico())
    secciones = construir_secciones_desde_spec(resolver_template("procedimiento_operativo"))
    assert [s.id for s in secciones] == ["1.objetivo", "2.responsables"]
    assert secciones[0].preguntas_guia == ["¿Qué problema resuelve este procedimiento?"]
    assert all(s.completitud == "vacia" for s in secciones)
