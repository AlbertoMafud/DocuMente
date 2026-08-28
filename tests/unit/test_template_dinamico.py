"""Tests del modelo TemplateDinamico + repositorio (Template Studio S-A)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.models import EventoAuditoria
from src.core.models.template_dinamico import (
    HallazgoLint,
    ResultadoLint,
    SeccionCatalogoDinamica,
    TemplateDinamico,
)
from src.storage.repositories import TemplateDinamicoRepository


@pytest.fixture
def repo_aislado(monkeypatch, tmp_path: Path):
    db_file = tmp_path / "test_templates.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    import src.storage.db as db_mod

    db_mod._engine = None
    db_mod._SessionLocal = None
    yield TemplateDinamicoRepository()
    db_mod._engine = None
    db_mod._SessionLocal = None


def _template(slug: str = "ficha_euc", estado: str = "borrador") -> TemplateDinamico:
    return TemplateDinamico(
        slug=slug,
        nombre="Ficha de EUC",
        estado=estado,  # type: ignore[arg-type]
        secciones=[
            SeccionCatalogoDinamica(
                id="1.identificacion",
                numero="1",
                nombre="Identificación",
                intencion="Datos básicos del EUC.",
                tipo_contenido="campos",
            )
        ],
    )


# --- Modelo ---


def test_defaults_del_modelo() -> None:
    t = _template()
    assert t.estado == "borrador"
    assert t.version == 1
    assert t.resultado_lint is None
    assert t.audit_trail == []


def test_registrar_evento_actualiza_timestamp() -> None:
    t = _template()
    antes = t.actualizado_en
    t.registrar_evento(
        EventoAuditoria(actor="default", tipo="template_creado", descripcion="Creado en Studio")
    )
    assert len(t.audit_trail) == 1
    assert t.actualizado_en >= antes


def test_seccion_por_id() -> None:
    t = _template()
    assert t.seccion_por_id("1.identificacion") is not None
    assert t.seccion_por_id("no_existe") is None


def test_estado_invalido_rechazado() -> None:
    with pytest.raises(ValueError):
        TemplateDinamico(slug="x", nombre="X", estado="publicandose")  # type: ignore[arg-type]


def test_resultado_lint_aprobado_solo_sin_errores() -> None:
    solo_advertencias = ResultadoLint(
        hallazgos=[HallazgoLint(codigo="L9", severidad="advertencia", mensaje="Sin aliases")]
    )
    con_error = ResultadoLint(
        hallazgos=[HallazgoLint(codigo="L3", severidad="error", mensaje="Intención vacía")]
    )
    assert solo_advertencias.aprobado is True
    assert len(solo_advertencias.advertencias) == 1
    assert con_error.aprobado is False
    assert len(con_error.errores) == 1


def test_roundtrip_json_preserva_todo() -> None:
    t = _template()
    t.resultado_lint = ResultadoLint(
        hallazgos=[HallazgoLint(codigo="L7", severidad="advertencia", mensaje="Intención corta")]
    )
    t.registrar_evento(
        EventoAuditoria(actor="default", tipo="lint_ejecutado", descripcion="Lint corrido")
    )
    reconstruido = TemplateDinamico.model_validate_json(t.model_dump_json())
    assert reconstruido.slug == t.slug
    assert reconstruido.resultado_lint is not None
    assert reconstruido.resultado_lint.hallazgos[0].codigo == "L7"
    assert reconstruido.audit_trail[0].tipo == "lint_ejecutado"


# --- Repositorio ---


def test_guardar_y_obtener_roundtrip(repo_aislado: TemplateDinamicoRepository) -> None:
    t = _template()
    repo_aislado.guardar(t)
    leido = repo_aislado.obtener(t.id)
    assert leido is not None
    assert leido.slug == "ficha_euc"
    assert leido.secciones[0].tipo_contenido == "campos"


def test_guardar_dos_veces_actualiza(repo_aislado: TemplateDinamicoRepository) -> None:
    t = _template()
    repo_aislado.guardar(t)
    t.nombre = "Ficha de EUC v2"
    t.estado = "publicado"
    repo_aislado.guardar(t)
    leido = repo_aislado.obtener(t.id)
    assert leido is not None
    assert leido.nombre == "Ficha de EUC v2"
    assert len(repo_aislado.listar()) == 1


def test_listar_filtra_por_estado(repo_aislado: TemplateDinamicoRepository) -> None:
    repo_aislado.guardar(_template(slug="a", estado="borrador"))
    repo_aislado.guardar(_template(slug="b", estado="publicado"))
    assert len(repo_aislado.listar()) == 2
    assert [t.slug for t in repo_aislado.listar(estado="publicado")] == ["b"]


def test_listar_filtra_por_creador(repo_aislado: TemplateDinamicoRepository) -> None:
    t = _template(slug="mio")
    t.creado_por = "alberto"
    repo_aislado.guardar(t)
    repo_aislado.guardar(_template(slug="ajeno"))
    assert [x.slug for x in repo_aislado.listar(creado_por="alberto")] == ["mio"]


def test_obtener_publicado_por_slug(repo_aislado: TemplateDinamicoRepository) -> None:
    repo_aislado.guardar(_template(slug="ficha_euc", estado="publicado"))
    repo_aislado.guardar(_template(slug="ficha_euc", estado="retirado"))
    encontrado = repo_aislado.obtener_publicado_por_slug("ficha_euc")
    assert encontrado is not None
    assert encontrado.estado == "publicado"
    assert repo_aislado.obtener_publicado_por_slug("no_existe") is None


def test_borrar(repo_aislado: TemplateDinamicoRepository) -> None:
    t = _template()
    repo_aislado.guardar(t)
    assert repo_aislado.borrar(t.id) is True
    assert repo_aislado.obtener(t.id) is None
    assert repo_aislado.borrar(t.id) is False
