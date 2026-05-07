"""Tests de los modelos de dominio Pydantic."""

from __future__ import annotations

from src.core.models import (
    Brecha,
    Documento,
    EventoAuditoria,
    MetadataModelo,
    Seccion,
)


def test_documento_default_user_id_is_default() -> None:
    """user_id default es 'default' (preparado para multi-user post-MVP)."""
    doc = Documento()
    assert doc.user_id == "default"


def test_documento_estado_inicial_draft() -> None:
    doc = Documento()
    assert doc.estado == "draft"


def test_documento_completitud_sin_secciones_es_cero() -> None:
    doc = Documento()
    assert doc.porcentaje_completitud == 0.0


def test_documento_completitud_correcta() -> None:
    secciones = [
        Seccion(id="a", nombre="A", numero="1", obligatoria=True, completitud="completa"),
        Seccion(id="b", nombre="B", numero="2", obligatoria=True, completitud="vacia"),
        Seccion(id="c", nombre="C", numero="3", obligatoria=False, completitud="completa"),
    ]
    doc = Documento(secciones=secciones)
    # Solo cuentan las obligatorias: 1 de 2 completas → 0.5
    assert doc.porcentaje_completitud == 0.5


def test_seccion_tiene_contenido() -> None:
    s_vacia = Seccion(id="x", nombre="X", numero="1", obligatoria=True)
    s_con = Seccion(id="y", nombre="Y", numero="2", obligatoria=True, contenido="hola mundo")
    assert s_vacia.tiene_contenido is False
    assert s_con.tiene_contenido is True


def test_brecha_es_inmutable() -> None:
    b = Brecha(seccion_id="x", tipo="seccion_vacia", severidad="alta", mensaje="m")
    try:
        b.mensaje = "otro"  # type: ignore[misc]
    except Exception:
        return  # esperado
    raise AssertionError("Brecha debería ser inmutable")


def test_evento_auditoria_es_inmutable() -> None:
    e = EventoAuditoria(actor="default", tipo="documento_creado", descripcion="x")
    try:
        e.descripcion = "y"  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("EventoAuditoria debería ser inmutable")


def test_documento_registrar_evento_actualiza_audit_trail() -> None:
    doc = Documento()
    assert len(doc.audit_trail) == 0
    evento = EventoAuditoria(actor="default", tipo="documento_creado", descripcion="test")
    doc.registrar_evento(evento)
    assert len(doc.audit_trail) == 1


def test_seccion_por_id_devuelve_correcta() -> None:
    secciones = [
        Seccion(id="a.1", nombre="A", numero="1", obligatoria=True),
        Seccion(id="b.2", nombre="B", numero="2", obligatoria=False),
    ]
    doc = Documento(secciones=secciones)
    assert doc.seccion_por_id("a.1") is not None
    assert doc.seccion_por_id("a.1").nombre == "A"  # type: ignore[union-attr]
    assert doc.seccion_por_id("inexistente") is None


def test_metadata_modelo_default_vacio() -> None:
    m = MetadataModelo()
    assert m.nombre_modelo == ""
    assert m.model_developers == []
    assert m.inherent_risk_tier is None


def test_seccion_puede_marcarse_como_omitida() -> None:
    """Una sección puede tener completitud='omitida' con motivo asociado."""
    s = Seccion(
        id="x",
        nombre="X",
        numero="1",
        obligatoria=True,
        completitud="omitida",
        motivo_omision="No aplica al modelo",
    )
    assert s.completitud == "omitida"
    assert s.motivo_omision == "No aplica al modelo"


def test_seccion_motivo_omision_default_none() -> None:
    """motivo_omision es opcional y default None (backward-compatible)."""
    s = Seccion(id="x", nombre="X", numero="1", obligatoria=True)
    assert s.motivo_omision is None


def test_formato_estado_documento_acepta_seccion_omitida() -> None:
    """Regresión: formato_estado_documento no debe romper con secciones omitidas.

    Bug histórico: el dict de marcadores en interview.py no incluía 'omitida'
    y reventaba con KeyError al iniciar entrevista en docs con omitidas.
    """
    from src.llm.prompts.interview import formato_estado_documento

    secciones = [
        Seccion(id="a", nombre="A", numero="1", obligatoria=True, completitud="completa"),
        Seccion(
            id="b",
            nombre="B",
            numero="2",
            obligatoria=True,
            completitud="omitida",
            motivo_omision="No aplica",
        ),
        Seccion(id="c", nombre="C", numero="3", obligatoria=True, completitud="vacia"),
        Seccion(id="d", nombre="D", numero="4", obligatoria=True, completitud="parcial"),
    ]
    doc = Documento(secciones=secciones)
    salida = formato_estado_documento(doc)

    assert "1 A" in salida
    assert "2 B" in salida


def test_documento_porcentaje_resuelto_cuenta_omitidas() -> None:
    """porcentaje_resuelto cuenta secciones obligatorias completas + omitidas."""
    secciones = [
        Seccion(id="a", nombre="A", numero="1", obligatoria=True, completitud="completa"),
        Seccion(id="b", nombre="B", numero="2", obligatoria=True, completitud="omitida"),
        Seccion(id="c", nombre="C", numero="3", obligatoria=True, completitud="vacia"),
        Seccion(id="d", nombre="D", numero="4", obligatoria=True, completitud="parcial"),
    ]
    doc = Documento(secciones=secciones)
    # 1 completa + 1 omitida = 2 resueltas de 4 obligatorias = 0.5
    assert doc.porcentaje_resuelto == 0.5
    # porcentaje_completitud sigue contando solo completas (1/4 = 0.25)
    assert doc.porcentaje_completitud == 0.25
