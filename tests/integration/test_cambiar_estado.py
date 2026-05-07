"""Tests del use case CambiarEstadoDocumento (integración con repo real)."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from src.core.models import Documento, MetadataModelo, Seccion
from src.core.usecases.cambiar_estado import (
    CambiarEstadoDocumento,
    RegistrarSignoff,
    TransicionRechazada,
)
from src.storage.repositories import DocumentoRepository


@pytest.fixture(autouse=True)
def _db_temporal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Aísla cada test en su propia BD temporal."""
    db_path = tmp_path / f"test_{uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    import src.storage.db as db_module

    db_module._engine = None  # type: ignore[attr-defined]
    db_module._SessionLocal = None  # type: ignore[attr-defined]


def _documento_completo() -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="Modelo Test"),
        secciones=[
            Seccion(
                id=f"s.{i}",
                nombre=f"Sección {i}",
                numero=str(i),
                obligatoria=True,
                completitud="completa",
            )
            for i in range(3)
        ],
    )


def test_cambiar_estado_persiste_y_registra_audit() -> None:
    """draft → in_review con secciones completas: cambia estado y graba audit event."""
    repo = DocumentoRepository()
    doc = _documento_completo()
    repo.guardar(doc)

    uc = CambiarEstadoDocumento(repo)
    uc.ejecutar(doc.id, destino="in_review", actor="default")

    recargado = repo.obtener(doc.id)
    assert recargado is not None
    assert recargado.estado == "in_review"
    eventos = [e for e in recargado.audit_trail if e.tipo == "transicion_estado"]
    assert len(eventos) == 1
    assert eventos[0].metadata.get("origen") == "draft"
    assert eventos[0].metadata.get("destino") == "in_review"


def test_cambiar_estado_rechaza_transicion_invalida() -> None:
    """Si state machine bloquea, levanta TransicionRechazada con razones y NO persiste."""
    repo = DocumentoRepository()
    doc = Documento(
        secciones=[
            Seccion(
                id="s.1",
                nombre="S1",
                numero="1",
                obligatoria=True,
                completitud="vacia",
            )
        ]
    )
    repo.guardar(doc)

    uc = CambiarEstadoDocumento(repo)
    with pytest.raises(TransicionRechazada) as exc:
        uc.ejecutar(doc.id, destino="in_review", actor="default")

    assert exc.value.razones
    recargado = repo.obtener(doc.id)
    assert recargado is not None
    assert recargado.estado == "draft"


def test_cambiar_estado_documento_inexistente_levanta_error() -> None:
    """Si el documento no existe, levanta ValueError claro."""
    repo = DocumentoRepository()
    uc = CambiarEstadoDocumento(repo)

    with pytest.raises(ValueError):
        uc.ejecutar(uuid4(), destino="in_review", actor="default")


def test_registrar_signoff_reviewer_agrega_audit() -> None:
    """RegistrarSignoff('reviewer') agrega evento 'signoff_reviewer' al audit trail."""
    repo = DocumentoRepository()
    doc = _documento_completo()
    doc.estado = "in_review"
    repo.guardar(doc)

    uc = RegistrarSignoff(repo)
    uc.ejecutar(doc.id, rol="reviewer", actor="default")

    recargado = repo.obtener(doc.id)
    assert recargado is not None
    eventos = [e for e in recargado.audit_trail if e.tipo == "signoff_reviewer"]
    assert len(eventos) == 1


def test_registrar_signoff_fae_agrega_audit() -> None:
    """RegistrarSignoff('fae') agrega evento 'signoff_fae'."""
    repo = DocumentoRepository()
    doc = _documento_completo()
    doc.estado = "approved"
    repo.guardar(doc)

    uc = RegistrarSignoff(repo)
    uc.ejecutar(doc.id, rol="fae", actor="default")

    recargado = repo.obtener(doc.id)
    assert recargado is not None
    eventos = [e for e in recargado.audit_trail if e.tipo == "signoff_fae"]
    assert len(eventos) == 1


def test_flujo_completo_draft_a_published() -> None:
    """Flujo end-to-end: draft → in_review → signoff Reviewer → approved → signoff FAE → published."""
    repo = DocumentoRepository()
    doc = _documento_completo()
    repo.guardar(doc)

    cambiar = CambiarEstadoDocumento(repo)
    signoff = RegistrarSignoff(repo)

    cambiar.ejecutar(doc.id, destino="in_review", actor="default")
    signoff.ejecutar(doc.id, rol="reviewer", actor="default")
    cambiar.ejecutar(doc.id, destino="approved", actor="default")
    signoff.ejecutar(doc.id, rol="fae", actor="default")
    cambiar.ejecutar(doc.id, destino="published", actor="default")

    recargado = repo.obtener(doc.id)
    assert recargado is not None
    assert recargado.estado == "published"
