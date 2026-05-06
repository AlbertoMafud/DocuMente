"""Tests del Drafter con LLMClient mockeado."""

from __future__ import annotations

from src.core.models import (
    Documento,
    EstadoEntrevista,
    MensajeEntrevista,
    MetadataModelo,
    Seccion,
)
from src.core.usecases.drafter import Drafter
from tests.unit.test_interview_engine import FakeLLM


def _setup() -> tuple[Documento, Seccion, EstadoEntrevista]:
    seccion = Seccion(
        id="4.4.assumptions",
        nombre="Key Assumptions",
        numero="4.4",
        obligatoria=True,
        intencion="Captura supuestos",
    )
    documento = Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="X", model_owner="O", fae="F"),
        secciones=[seccion],
    )
    estado = EstadoEntrevista(
        documento_id=str(documento.id),
        seccion_id=seccion.id,
        mensajes=[
            MensajeEntrevista(rol="assistant", contenido="¿Qué supuestos usas?"),
            MensajeEntrevista(
                rol="user", contenido="Mortalidad SOA 2017, lapses de la tabla 2019."
            ),
        ],
    )
    return documento, seccion, estado


def test_drafter_redacta_y_actualiza_seccion() -> None:
    fake = FakeLLM(
        [
            "## Supuestos clave\n\nSe utilizan los siguientes supuestos:\n"
            "- **Mortalidad**: SOA 2017\n- **Lapses**: tabla 2019\n"
        ]
    )
    drafter = Drafter(fake)
    documento, seccion, estado = _setup()

    texto, suficiente = drafter.redactar(documento, seccion, estado)

    assert suficiente is True
    assert "SOA 2017" in texto
    assert seccion.contenido == texto
    assert seccion.completitud == "completa"
    assert any(e.tipo == "seccion_editada" for e in documento.audit_trail)


def test_drafter_devuelve_insuficiente_cuando_material_es_pobre() -> None:
    fake = FakeLLM(["[BORRADOR INSUFICIENTE: faltan supuestos económicos]"])
    drafter = Drafter(fake)
    documento, seccion, estado = _setup()

    texto, suficiente = drafter.redactar(documento, seccion, estado)

    assert suficiente is False
    assert "INSUFICIENTE" in texto
    # Sección NO se actualiza si el borrador es insuficiente
    assert seccion.contenido is None
    assert seccion.completitud != "completa"


def test_drafter_sin_mensajes_devuelve_string_vacio() -> None:
    """Caso edge: estado vacío no debe llamar al LLM."""
    fake = FakeLLM([])
    drafter = Drafter(fake)
    documento, seccion, _ = _setup()
    estado_vacio = EstadoEntrevista(documento_id=str(documento.id), seccion_id=seccion.id)

    texto, suficiente = drafter.redactar(documento, seccion, estado_vacio)

    assert texto == ""
    assert suficiente is False
    assert len(fake.llamadas) == 0
