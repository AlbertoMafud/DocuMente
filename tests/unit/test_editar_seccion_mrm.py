"""Tests del editor inline MRM (B.4) — persistencia + completitud + audit.

El editor inline usa Streamlit's st.session_state y rerun. Probamos la
lógica de persistencia y reglas de completitud — NO el flujo Streamlit
completo (eso requiere streamlit testing framework).
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from src.core.models import Documento, Seccion
from src.core.models.documento import MetadataModelo
from src.storage.repositories import DocumentoRepository


@pytest.fixture(autouse=True)
def _db_temporal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / f"test_{uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    import src.storage.db as db_module

    db_module._engine = None  # type: ignore[attr-defined]
    db_module._SessionLocal = None  # type: ignore[attr-defined]


def _doc_con_seccion_vacia() -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="Test"),
        secciones=[
            Seccion(
                id="4.4.assumptions",
                nombre="Key Assumptions",
                numero="4.4",
                obligatoria=True,
                completitud="vacia",
                intencion="Supuestos clave del modelo",
            )
        ],
    )


def test_editar_inline_persiste_contenido_y_actualiza_completitud_completa() -> None:
    """Texto largo (>200 chars) → completitud='completa'."""
    repo = DocumentoRepository()
    doc = _doc_con_seccion_vacia()
    repo.guardar(doc)

    # Simular guardado del editor: muta directo + persiste (lo mismo que hace
    # el botón "Guardar cambios" en editar_seccion_mrm.py)
    seccion = doc.seccion_por_id("4.4.assumptions")
    assert seccion is not None
    contenido = "supuesto " * 50  # ~450 chars
    seccion.contenido = contenido.strip()
    seccion.completitud = "completa"
    from datetime import UTC, datetime

    from src.core.models import EventoAuditoria

    doc.registrar_evento(
        EventoAuditoria(
            timestamp=datetime.now(UTC),
            actor=doc.user_id,
            tipo="seccion_editada",
            descripcion="Sección '4.4 Key Assumptions' editada inline desde vista previa.",
            seccion_id="4.4.assumptions",
        )
    )
    repo.guardar(doc)

    recuperado = repo.obtener(doc.id)
    assert recuperado is not None
    s = recuperado.seccion_por_id("4.4.assumptions")
    assert s is not None
    assert s.contenido is not None and s.contenido.startswith("supuesto")
    assert s.completitud == "completa"
    eventos = [e for e in recuperado.audit_trail if e.tipo == "seccion_editada"]
    assert len(eventos) == 1
    assert "inline desde vista previa" in eventos[0].descripcion


def test_editar_inline_contenido_corto_resulta_en_completitud_parcial() -> None:
    """Contenido <200 chars → completitud='parcial'."""
    repo = DocumentoRepository()
    doc = _doc_con_seccion_vacia()
    repo.guardar(doc)

    seccion = doc.seccion_por_id("4.4.assumptions")
    assert seccion is not None
    seccion.contenido = "supuesto corto"
    # Simulación: replicar la regla de completitud del editor
    n_chars = len(seccion.contenido.strip())
    if n_chars == 0:
        seccion.completitud = "vacia"
    elif n_chars < 200:
        seccion.completitud = "parcial"
    else:
        seccion.completitud = "completa"
    repo.guardar(doc)

    recuperado = repo.obtener(doc.id)
    assert recuperado is not None
    s = recuperado.seccion_por_id("4.4.assumptions")
    assert s is not None
    assert s.completitud == "parcial"


def test_editar_inline_borrar_contenido_resulta_en_completitud_vacia() -> None:
    """Limpiar todo el textarea → completitud='vacia'."""
    repo = DocumentoRepository()
    doc = Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="Test"),
        secciones=[
            Seccion(
                id="4.4.assumptions",
                nombre="Key Assumptions",
                numero="4.4",
                obligatoria=True,
                contenido="contenido previo",
                completitud="completa",
            )
        ],
    )
    repo.guardar(doc)

    seccion = doc.seccion_por_id("4.4.assumptions")
    assert seccion is not None
    # Borrar contenido
    contenido_limpio = ""
    seccion.contenido = contenido_limpio if contenido_limpio else None
    if not contenido_limpio:
        seccion.completitud = "vacia"
    repo.guardar(doc)

    recuperado = repo.obtener(doc.id)
    assert recuperado is not None
    s = recuperado.seccion_por_id("4.4.assumptions")
    assert s is not None
    assert s.contenido is None
    assert s.completitud == "vacia"


def test_editor_existe_como_modulo_importable() -> None:
    """Sanity: el módulo se importa sin errores (validación de imports)."""
    from src.ui.pages import editar_seccion_mrm

    assert hasattr(editar_seccion_mrm, "render")
    assert callable(editar_seccion_mrm.render)
