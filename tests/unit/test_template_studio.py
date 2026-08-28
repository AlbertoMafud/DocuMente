"""Tests de los use cases del Template Studio (ciclo de vida del template)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.models.template_dinamico import SeccionCatalogoDinamica
from src.core.usecases.template_studio import (
    ActualizarSeccionesTemplate,
    BorrarTemplateBorrador,
    CorrerLintTemplate,
    CrearNuevaVersionTemplate,
    CrearTemplateBorrador,
    PublicarTemplate,
    RetirarTemplate,
    StudioError,
)
from src.storage.repositories import TemplateDinamicoRepository


@pytest.fixture
def repo(monkeypatch, tmp_path: Path):
    db_file = tmp_path / "test_studio.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    import src.storage.db as db_mod

    db_mod._engine = None
    db_mod._SessionLocal = None
    yield TemplateDinamicoRepository()
    db_mod._engine = None
    db_mod._SessionLocal = None


def _secciones_sanas() -> list[SeccionCatalogoDinamica]:
    """Catálogo que pasa el lint sin errores ni advertencias."""
    return [
        SeccionCatalogoDinamica(
            id="1.objetivo",
            numero="1",
            nombre="Objetivo",
            obligatoria=True,
            intencion="Qué logra el procedimiento y qué necesidad del negocio atiende.",
            aliases=["objetivo", "propósito"],
            preguntas_guia=["¿Qué problema resuelve este procedimiento?"],
        ),
        SeccionCatalogoDinamica(
            id="2.alcance",
            numero="2",
            nombre="Alcance",
            obligatoria=False,
            intencion="Qué áreas y sistemas cubre el procedimiento y cuáles quedan fuera.",
            aliases=["alcance", "scope"],
            preguntas_guia=["¿Qué queda explícitamente fuera?"],
        ),
    ]


def _crear(repo: TemplateDinamicoRepository, **kw):
    uc = CrearTemplateBorrador(repo=repo)
    params = {
        "nombre": "Ficha de Procedimiento Operativo",
        "secciones": _secciones_sanas(),
    }
    params.update(kw)
    return uc.ejecutar(**params)


def _publicar_listo(repo: TemplateDinamicoRepository):
    t = _crear(repo)
    CorrerLintTemplate(repo=repo).ejecutar(t.id)
    return PublicarTemplate(repo=repo).ejecutar(t.id)


# --- Crear ---


def test_crear_genera_slug_desde_nombre(repo) -> None:
    t = _crear(repo)
    assert t.slug == "ficha_de_procedimiento_operativo"
    assert t.estado == "borrador"
    assert t.version == 1


def test_crear_slugifica_acentos_y_enies(repo) -> None:
    t = _crear(repo, nombre="Diseño de Métricas Año 1")
    assert t.slug == "diseno_de_metricas_ano_1"


def test_crear_registra_eventos_de_auditoria(repo) -> None:
    t = _crear(repo, archivo_origen="plantilla.docx")
    tipos = [e.tipo for e in t.audit_trail]
    assert "template_creado" in tipos
    assert "template_extraido" in tipos
    assert "catalogo_propuesto_llm" in tipos


def test_crear_rechaza_nombre_vacio(repo) -> None:
    with pytest.raises(StudioError):
        _crear(repo, nombre="   ")


def test_crear_rechaza_slug_reservado_de_template_congelado(repo) -> None:
    with pytest.raises(StudioError, match="reservado"):
        _crear(repo, slug="prophet")
    with pytest.raises(StudioError, match="reservado"):
        _crear(repo, slug="model_development")


def test_crear_rechaza_slug_malformado(repo) -> None:
    with pytest.raises(StudioError, match="Slug inválido"):
        _crear(repo, slug="Con Espacios")


# --- Actualizar secciones ---


def test_actualizar_secciones_invalida_lint_previo(repo) -> None:
    t = _crear(repo)
    CorrerLintTemplate(repo=repo).ejecutar(t.id)
    assert repo.obtener(t.id).resultado_lint is not None  # type: ignore[union-attr]

    nuevas = _secciones_sanas()[:1]
    actualizado = ActualizarSeccionesTemplate(repo=repo).ejecutar(t.id, nuevas)
    assert len(actualizado.secciones) == 1
    assert actualizado.resultado_lint is None
    assert "seccion_catalogo_editada" in [e.tipo for e in actualizado.audit_trail]


def test_no_se_edita_un_template_publicado(repo) -> None:
    t = _publicar_listo(repo)
    with pytest.raises(StudioError, match="nueva versión"):
        ActualizarSeccionesTemplate(repo=repo).ejecutar(t.id, _secciones_sanas())


# --- Lint ---


def test_lint_persiste_resultado_y_evento(repo) -> None:
    t = _crear(repo)
    resultado = CorrerLintTemplate(repo=repo).ejecutar(t.id)
    assert resultado.resultado_lint is not None
    assert resultado.resultado_lint.aprobado is True
    assert "lint_ejecutado" in [e.tipo for e in resultado.audit_trail]


# --- Publicar ---


def test_publicar_exige_lint_corrido(repo) -> None:
    t = _crear(repo)
    with pytest.raises(StudioError, match="lint"):
        PublicarTemplate(repo=repo).ejecutar(t.id)


def test_publicar_bloqueado_por_errores_de_lint(repo) -> None:
    malas = [
        SeccionCatalogoDinamica(
            id="1.x", numero="1", nombre="Sin intención", obligatoria=True, aliases=["x"]
        )
    ]
    t = _crear(repo, secciones=malas)
    CorrerLintTemplate(repo=repo).ejecutar(t.id)
    with pytest.raises(StudioError, match="error"):
        PublicarTemplate(repo=repo).ejecutar(t.id)


def test_publicar_exige_aceptar_advertencias(repo) -> None:
    # Sin aliases → advertencia L9 (no bloqueante pero requiere aceptación).
    con_advertencia = [
        SeccionCatalogoDinamica(
            id="1.objetivo",
            numero="1",
            nombre="Objetivo",
            obligatoria=True,
            intencion="Qué logra el procedimiento y para quién existe.",
            preguntas_guia=["¿Qué problema resuelve?"],
        ),
        SeccionCatalogoDinamica(
            id="2.alcance",
            numero="2",
            nombre="Alcance",
            obligatoria=False,
            intencion="Qué cubre y qué queda fuera del procedimiento.",
        ),
    ]
    t = _crear(repo, secciones=con_advertencia)
    CorrerLintTemplate(repo=repo).ejecutar(t.id)
    with pytest.raises(StudioError, match="advertencia"):
        PublicarTemplate(repo=repo).ejecutar(t.id)

    publicado = PublicarTemplate(repo=repo).ejecutar(t.id, aceptar_advertencias=True)
    assert publicado.estado == "publicado"
    assert "advertencias_aceptadas" in [e.tipo for e in publicado.audit_trail]


def test_publicar_ok_registra_evento(repo) -> None:
    t = _publicar_listo(repo)
    assert t.estado == "publicado"
    assert "template_publicado" in [e.tipo for e in t.audit_trail]


def test_publicar_retira_la_version_anterior_del_mismo_slug(repo) -> None:
    v1 = _publicar_listo(repo)
    v2 = CrearNuevaVersionTemplate(repo=repo).ejecutar(v1.id)
    CorrerLintTemplate(repo=repo).ejecutar(v2.id)
    PublicarTemplate(repo=repo).ejecutar(v2.id)

    v1_releido = repo.obtener(v1.id)
    assert v1_releido is not None
    assert v1_releido.estado == "retirado"
    publicado = repo.obtener_publicado_por_slug(v1.slug)
    assert publicado is not None
    assert publicado.version == 2


# --- Versionar / retirar / borrar ---


def test_nueva_version_copia_secciones_sin_compartir_estado(repo) -> None:
    v1 = _publicar_listo(repo)
    v2 = CrearNuevaVersionTemplate(repo=repo).ejecutar(v1.id)
    assert v2.version == 2
    assert v2.estado == "borrador"
    assert v2.slug == v1.slug
    v2.secciones[0].nombre = "Cambiado"
    assert repo.obtener(v1.id).secciones[0].nombre == "Objetivo"  # type: ignore[union-attr]


def test_no_se_versiona_un_borrador(repo) -> None:
    t = _crear(repo)
    with pytest.raises(StudioError, match="publicado o retirado"):
        CrearNuevaVersionTemplate(repo=repo).ejecutar(t.id)


def test_retirar_solo_desde_publicado(repo) -> None:
    t = _crear(repo)
    with pytest.raises(StudioError):
        RetirarTemplate(repo=repo).ejecutar(t.id)

    publicado = _publicar_listo(repo)
    retirado = RetirarTemplate(repo=repo).ejecutar(publicado.id)
    assert retirado.estado == "retirado"


def test_borrar_solo_borradores(repo) -> None:
    t = _crear(repo)
    BorrarTemplateBorrador(repo=repo).ejecutar(t.id)
    assert repo.obtener(t.id) is None

    publicado = _publicar_listo(repo)
    with pytest.raises(StudioError, match="borradores"):
        BorrarTemplateBorrador(repo=repo).ejecutar(publicado.id)


# --- Integración con el registro ---


def test_template_publicado_es_resoluble_por_el_registro(repo) -> None:
    from src.core.template_registry import resolver_template

    t = _publicar_listo(repo)
    spec = resolver_template(t.slug)
    assert spec.origen == "dinamico"
    assert len(spec.catalogo) == 2


def test_template_retirado_deja_de_resolverse(repo) -> None:
    from src.core.template_registry import TemplateDesconocidoError, resolver_template

    t = _publicar_listo(repo)
    RetirarTemplate(repo=repo).ejecutar(t.id)
    with pytest.raises(TemplateDesconocidoError):
        resolver_template(t.slug)
