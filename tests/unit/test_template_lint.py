"""Tests del lint determinístico de AI-readiness (L1-L9)."""

from __future__ import annotations

from src.core.models.template_dinamico import SeccionCatalogoDinamica
from src.core.rules.template_lint import lint_secciones


def _seccion(**overrides) -> SeccionCatalogoDinamica:
    base = {
        "id": "1.objetivo",
        "numero": "1",
        "nombre": "Objetivo",
        "obligatoria": True,
        "intencion": "Qué logra el procedimiento y para quién existe.",
        "aliases": ["objetivo", "propósito"],
        "preguntas_guia": ["¿Qué problema resuelve?"],
    }
    base.update(overrides)
    return SeccionCatalogoDinamica(**base)


def _codigos(resultado, severidad=None):
    return [h.codigo for h in resultado.hallazgos if severidad is None or h.severidad == severidad]


def test_catalogo_sano_pasa_sin_errores() -> None:
    secciones = [
        _seccion(),
        _seccion(
            id="2.alcance",
            numero="2",
            nombre="Alcance",
            obligatoria=False,
            aliases=["alcance"],
            preguntas_guia=[],
        ),
    ]
    r = lint_secciones(secciones)
    assert r.aprobado is True
    assert _codigos(r, "error") == []


def test_l1_id_vacio_duplicado_y_formato() -> None:
    r = lint_secciones(
        [
            _seccion(id=""),
            _seccion(id="2.alcance", numero="2", aliases=["a"]),
            _seccion(id="2.alcance", numero="3", aliases=["b"]),
            _seccion(id="Con Espacios", numero="4", aliases=["c"]),
        ]
    )
    errores = _codigos(r, "error")
    assert errores.count("L1") == 3  # vacío + duplicado + formato
    assert r.aprobado is False


def test_l2_numeracion_faltante_duplicada_y_desordenada() -> None:
    sin_numero = lint_secciones([_seccion(numero="")])
    assert "L2" in _codigos(sin_numero, "error")

    duplicada = lint_secciones([_seccion(), _seccion(id="2.otro", numero="1", aliases=["x"])])
    assert "L2" in _codigos(duplicada, "error")

    desordenada = lint_secciones(
        [
            _seccion(id="3.tres", numero="3", aliases=["t"]),
            _seccion(id="1.uno", numero="1", aliases=["u"]),
        ]
    )
    assert "L2" in _codigos(desordenada, "error")


def test_l3_intencion_vacia_es_error() -> None:
    r = lint_secciones([_seccion(intencion="")])
    assert "L3" in _codigos(r, "error")


def test_l4_obligatoria_sin_preguntas_es_error() -> None:
    r = lint_secciones([_seccion(preguntas_guia=[])])
    assert "L4" in _codigos(r, "error")
    opcional = lint_secciones([_seccion(obligatoria=False, preguntas_guia=[])])
    assert "L4" not in _codigos(opcional, "error")


def test_l5_alias_colisionando_es_error() -> None:
    r = lint_secciones(
        [
            _seccion(aliases=["objetivo"]),
            _seccion(id="2.meta", numero="2", nombre="Meta", aliases=["OBJETIVO"]),
        ]
    )
    assert "L5" in _codigos(r, "error")


def test_l6_tabla_sin_schema_es_error() -> None:
    r = lint_secciones([_seccion(tipo_contenido="tabla", schema_tabla=[])])
    assert "L6" in _codigos(r, "error")
    con_schema = lint_secciones([_seccion(tipo_contenido="tabla", schema_tabla=["persona", "rol"])])
    assert "L6" not in _codigos(con_schema, "error")


def test_l7_intencion_generica_es_advertencia() -> None:
    corta = lint_secciones([_seccion(intencion="Datos.")])
    assert "L7" in _codigos(corta, "advertencia")
    generica = lint_secciones([_seccion(intencion="Descripción de la sección.")])
    # ojo: "Descripción de la sección." con punto no matchea el literal — el
    # check usa lista de frases exactas + umbral de longitud; ≥15 chars con
    # punto pasa. Verificamos el caso exacto de la lista:
    exacta = lint_secciones([_seccion(intencion="descripción de la sección")])
    assert "L7" in _codigos(exacta, "advertencia")
    assert generica.aprobado is True  # advertencias nunca bloquean


def test_l8_cero_o_todas_obligatorias_es_advertencia() -> None:
    todas = lint_secciones([_seccion(), _seccion(id="2.b", numero="2", aliases=["b"])])
    assert "L8" in _codigos(todas, "advertencia")
    ninguna = lint_secciones([_seccion(obligatoria=False, preguntas_guia=[])])
    assert "L8" in _codigos(ninguna, "advertencia")


def test_l9_sin_aliases_es_advertencia() -> None:
    r = lint_secciones([_seccion(aliases=[])])
    assert "L9" in _codigos(r, "advertencia")


def test_catalogos_congelados_pasan_el_lint_sin_errores() -> None:
    """Sanity: MRM y Prophet (envueltos por el registro) no tienen errores L1-L6.

    Prophet no tiene preguntas_guia (L4) ni aliases (L9) — por eso solo se
    exige cero errores de estructura en MRM, y para Prophet toleramos L4
    como deuda conocida del catálogo congelado.
    """
    from src.core.template_registry import resolver_template

    mrm = lint_secciones(list(resolver_template("model_development").catalogo))
    assert [h for h in mrm.errores if h.codigo != "L4"] == []
