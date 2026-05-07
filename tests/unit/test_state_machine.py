"""Tests del DocumentStateMachine.

Reglas oficiales en `docs/MRM_REQUIREMENTS.md` §10 y §12. La state machine
es la fuente única que decide si una transición de estado es permitida.
"""

from __future__ import annotations

from src.core.models import Documento, EventoAuditoria, Seccion
from src.core.rules.state_machine import DocumentStateMachine


def _doc_con_secciones(completas: int, total: int) -> Documento:
    """Helper: documento con N secciones obligatorias, M de ellas completas."""
    secciones = []
    for i in range(total):
        secciones.append(
            Seccion(
                id=f"s.{i}",
                nombre=f"Sección {i}",
                numero=str(i),
                obligatoria=True,
                completitud="completa" if i < completas else "vacia",
            )
        )
    return Documento(secciones=secciones)


def test_draft_a_in_review_bloqueada_si_secciones_incompletas() -> None:
    """No se puede pasar a 'in_review' si faltan secciones obligatorias."""
    doc = _doc_con_secciones(completas=2, total=5)
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "in_review")

    assert resultado.permitida is False
    assert any("sin resolver" in r.lower() for r in resultado.razones)


def test_draft_a_in_review_permitida_si_100_porciento_completo() -> None:
    """Con todas las secciones obligatorias completas, draft → in_review se permite."""
    doc = _doc_con_secciones(completas=5, total=5)
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "in_review")

    assert resultado.permitida is True
    assert resultado.razones == []


def test_transicion_a_mismo_estado_bloqueada() -> None:
    """No tiene sentido transicionar a sí mismo (ej. draft → draft)."""
    doc = _doc_con_secciones(completas=5, total=5)
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "draft")

    assert resultado.permitida is False
    assert any("mismo estado" in r.lower() for r in resultado.razones)


def test_transicion_no_listada_bloqueada() -> None:
    """draft → approved (saltándose in_review) no es transición válida."""
    doc = _doc_con_secciones(completas=5, total=5)
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "approved")

    assert resultado.permitida is False
    assert any("no permitida" in r.lower() for r in resultado.razones)


def test_in_review_a_draft_siempre_permitida() -> None:
    """Rechazo de revisión: in_review → draft es siempre válida (sin condiciones)."""
    doc = _doc_con_secciones(completas=5, total=5)
    doc.estado = "in_review"
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "draft")

    assert resultado.permitida is True


def test_in_review_a_approved_bloqueada_sin_signoff_reviewer() -> None:
    """Sin sign-off del Reviewer en audit_trail, no se puede aprobar."""
    doc = _doc_con_secciones(completas=5, total=5)
    doc.estado = "in_review"
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "approved")

    assert resultado.permitida is False
    assert any("reviewer" in r.lower() for r in resultado.razones)


def test_in_review_a_approved_permitida_con_signoff_reviewer() -> None:
    """Con audit event 'signoff_reviewer', in_review → approved se permite."""
    doc = _doc_con_secciones(completas=5, total=5)
    doc.estado = "in_review"
    doc.registrar_evento(
        EventoAuditoria(
            actor="default",
            tipo="signoff_reviewer",
            descripcion="Sign-off del Reviewer registrado.",
        )
    )
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "approved")

    assert resultado.permitida is True


def test_approved_a_in_review_siempre_permitida() -> None:
    """Retracción: approved → in_review es siempre válida."""
    doc = _doc_con_secciones(completas=5, total=5)
    doc.estado = "approved"
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "in_review")

    assert resultado.permitida is True


def test_approved_a_published_bloqueada_sin_signoff_fae() -> None:
    """Sin sign-off del FAE, no se publica."""
    doc = _doc_con_secciones(completas=5, total=5)
    doc.estado = "approved"
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "published")

    assert resultado.permitida is False
    assert any("fae" in r.lower() for r in resultado.razones)


def test_approved_a_published_permitida_con_signoff_fae() -> None:
    """Con sign-off del FAE en audit, approved → published se permite."""
    doc = _doc_con_secciones(completas=5, total=5)
    doc.estado = "approved"
    doc.registrar_evento(
        EventoAuditoria(
            actor="default",
            tipo="signoff_fae",
            descripcion="Sign-off del FAE registrado.",
        )
    )
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "published")

    assert resultado.permitida is True


def test_published_a_retired_permitida() -> None:
    """published → retired es válida (modelo retirado)."""
    doc = _doc_con_secciones(completas=5, total=5)
    doc.estado = "published"
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "retired")

    assert resultado.permitida is True


def test_retired_es_inmutable() -> None:
    """Una vez retirado, no se puede transicionar a ningún otro estado."""
    doc = _doc_con_secciones(completas=5, total=5)
    doc.estado = "retired"
    sm = DocumentStateMachine()

    for destino in ("draft", "in_review", "approved", "published"):
        resultado = sm.validar_transicion(doc, destino)  # type: ignore[arg-type]
        assert resultado.permitida is False, f"retired → {destino} no debería permitirse"
        assert any("retirado" in r.lower() or "inmutable" in r.lower() for r in resultado.razones)


def test_draft_a_in_review_permitida_si_secciones_omitidas() -> None:
    """Secciones omitidas cuentan como resueltas para transición a in_review."""
    secciones = [
        Seccion(id="a", nombre="A", numero="1", obligatoria=True, completitud="completa"),
        Seccion(
            id="b",
            nombre="B",
            numero="2",
            obligatoria=True,
            completitud="omitida",
            motivo_omision="No aplica al modelo",
        ),
        Seccion(id="c", nombre="C", numero="3", obligatoria=True, completitud="completa"),
    ]
    doc = Documento(secciones=secciones)
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "in_review")

    assert resultado.permitida is True


def test_draft_a_in_review_bloqueada_si_hay_seccion_parcial() -> None:
    """Una sección 'parcial' bloquea la transición (no es ni completa ni omitida)."""
    secciones = [
        Seccion(id="a", nombre="A", numero="1", obligatoria=True, completitud="completa"),
        Seccion(id="b", nombre="B", numero="2", obligatoria=True, completitud="parcial"),
    ]
    doc = Documento(secciones=secciones)
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "in_review")

    assert resultado.permitida is False
    assert any("sin resolver" in r.lower() or "completar" in r.lower() for r in resultado.razones)


def test_published_a_approved_no_permitida() -> None:
    """No se puede 'des-publicar' un documento (solo retirar)."""
    doc = _doc_con_secciones(completas=5, total=5)
    doc.estado = "published"
    sm = DocumentStateMachine()

    resultado = sm.validar_transicion(doc, "approved")

    assert resultado.permitida is False
