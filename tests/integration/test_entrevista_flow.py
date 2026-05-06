"""Tests de integración del flujo end-to-end de entrevista.

Mockeamos el LLMClient pero ejercitamos use cases + repos + persistencia real.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from src.core.models import Documento, MetadataModelo, Seccion
from src.core.usecases import (
    Drafter,
    IniciarEntrevista,
    InterviewEngine,
    ResponderPregunta,
)
from src.storage.repositories import (
    DocumentoRepository,
    EstadoEntrevistaRepository,
)
from tests.unit.test_interview_engine import FakeLLM


@pytest.fixture(autouse=True)
def _db_temporal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Aísla cada test en su propia BD temporal."""
    db_path = tmp_path / f"test_{uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    # Reset del singleton de db.py para que use la nueva URL
    import src.storage.db as db_module

    db_module._engine = None  # type: ignore[attr-defined]
    db_module._SessionLocal = None  # type: ignore[attr-defined]


def _documento_seed() -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(
            nombre_modelo="Modelo de Prueba",
            model_owner="Owner",
            fae="FAE",
            intended_use="testing",
        ),
        secciones=[
            Seccion(
                id="4.4.assumptions",
                nombre="Key Assumptions",
                numero="4.4",
                obligatoria=True,
                intencion="Capturar supuestos",
            ),
        ],
    )


def test_flujo_completo_entrevista_cierra_y_genera_borrador() -> None:
    fake = FakeLLM(
        [
            "¿Qué tabla de mortalidad usa el modelo?",  # primera pregunta (engine.iniciar)
            "SECCION_COMPLETA\nResumen capturado.",  # responde y cierra
            "## Supuestos\n- Mortalidad SOA 2017",  # drafter.redactar
        ]
    )
    engine = InterviewEngine(fake)
    drafter = Drafter(fake)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()

    # Seed: persistir documento
    doc = _documento_seed()
    doc_repo.guardar(doc)

    iniciar = IniciarEntrevista(engine, doc_repo, estado_repo)
    responder = ResponderPregunta(engine, drafter, doc_repo, estado_repo)

    turno1 = iniciar.ejecutar(doc.id, "4.4.assumptions")
    assert "tabla de mortalidad" in turno1.respuesta_claude.lower()
    assert turno1.seccion_cerrada is False

    turno2 = responder.ejecutar(doc.id, "4.4.assumptions", "SOA 2017 base.")
    assert turno2.seccion_cerrada is True
    assert turno2.borrador is not None
    assert "SOA 2017" in turno2.borrador

    # Verificar persistencia
    doc_recuperado = doc_repo.obtener(doc.id)
    assert doc_recuperado is not None
    sec = doc_recuperado.seccion_por_id("4.4.assumptions")
    assert sec is not None
    assert sec.completitud == "completa"
    assert "SOA 2017" in (sec.contenido or "")


def test_iniciar_entrevista_dos_veces_retoma_estado() -> None:
    """Si la entrevista ya empezó, IniciarEntrevista la retoma sin llamar al LLM."""
    fake = FakeLLM(["primera pregunta"])
    engine = InterviewEngine(fake)
    Drafter(fake)  # construido para verificar que se importa, no usado aquí
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()

    doc = _documento_seed()
    doc_repo.guardar(doc)
    iniciar = IniciarEntrevista(engine, doc_repo, estado_repo)

    turno1 = iniciar.ejecutar(doc.id, "4.4.assumptions")
    n_llamadas_iniciales = len(fake.llamadas)

    # Segunda llamada a iniciar — debe retomar, NO debe llamar al LLM
    turno2 = iniciar.ejecutar(doc.id, "4.4.assumptions")
    assert len(fake.llamadas) == n_llamadas_iniciales
    assert turno2.respuesta_claude == turno1.respuesta_claude


def test_responder_sin_iniciar_levanta_error() -> None:
    fake = FakeLLM([])
    engine = InterviewEngine(fake)
    drafter = Drafter(fake)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()

    doc = _documento_seed()
    doc_repo.guardar(doc)

    responder = ResponderPregunta(engine, drafter, doc_repo, estado_repo)
    with pytest.raises(ValueError, match="No hay entrevista activa"):
        responder.ejecutar(doc.id, "4.4.assumptions", "respuesta")


def test_drafter_insuficiente_reabre_entrevista() -> None:
    """Si el Drafter dice INSUFICIENTE, la sección NO se cierra."""
    fake = FakeLLM(
        [
            "primera pregunta",  # iniciar
            "SECCION_COMPLETA\nresumen",  # claude cierra prematuramente
            "[BORRADOR INSUFICIENTE: falta detalle]",  # drafter rechaza
        ]
    )
    engine = InterviewEngine(fake)
    drafter = Drafter(fake)
    doc_repo = DocumentoRepository()
    estado_repo = EstadoEntrevistaRepository()

    doc = _documento_seed()
    doc_repo.guardar(doc)
    iniciar = IniciarEntrevista(engine, doc_repo, estado_repo)
    responder = ResponderPregunta(engine, drafter, doc_repo, estado_repo)

    iniciar.ejecutar(doc.id, "4.4.assumptions")
    turno = responder.ejecutar(doc.id, "4.4.assumptions", "respuesta corta")

    # cerrada=False porque borrador fue insuficiente → reabrió
    assert turno.seccion_cerrada is False
    assert turno.borrador is None
    estado = estado_repo.obtener(str(doc.id), "4.4.assumptions")
    assert estado is not None
    assert estado.cerrada is False  # reabierta
