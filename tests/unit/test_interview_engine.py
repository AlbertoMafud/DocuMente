"""Tests del InterviewEngine con LLMClient mockeado."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from anthropic.types import MessageParam, TextBlockParam

from src.core.models import Documento, MetadataModelo, Seccion
from src.core.usecases.interview_engine import InterviewEngine
from src.llm import LLMResponse


class FakeLLM:
    """Mock determinista del LLMClient para tests."""

    def __init__(self, respuestas: list[str]) -> None:
        self._respuestas: Iterator[str] = iter(respuestas)
        self.llamadas: list[tuple[str, list[TextBlockParam], list[MessageParam]]] = []

    def chat(
        self,
        *,
        tarea: str,
        system_blocks: list[TextBlockParam],
        messages: list[MessageParam],
        max_tokens: int = 4096,
    ) -> LLMResponse:
        self.llamadas.append((tarea, system_blocks, messages))
        try:
            text = next(self._respuestas)
        except StopIteration:
            text = "Sin más respuestas configuradas."
        modelo_por_tarea = {
            "chat": "claude-sonnet-4-6",
            "drafting": "claude-opus-4-7",
            "extraction": "claude-haiku-4-5",
        }
        return LLMResponse(
            text=text,
            modelo_usado=modelo_por_tarea.get(tarea, "claude-opus-4-7"),
            input_tokens=1000,
            output_tokens=200,
            cache_read_tokens=12000,
            cache_creation_tokens=0,
        )


def _seccion_test() -> Seccion:
    return Seccion(
        id="4.4.assumptions",
        nombre="Key Assumptions",
        numero="4.4",
        obligatoria=True,
        intencion="Captura de supuestos del modelo",
        preguntas_guia=("¿Qué supuestos clave usa el modelo?",),
    )


def _documento_test() -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(
            nombre_modelo="Test Model",
            model_owner="Owner",
            fae="FAE",
            intended_use="testing",
        ),
        secciones=[_seccion_test()],
    )


def test_iniciar_entrevista_devuelve_primera_pregunta() -> None:
    fake = FakeLLM(["¿Cuáles son los supuestos de mortalidad de tu modelo?"])
    engine = InterviewEngine(fake)
    documento = _documento_test()
    seccion = documento.secciones[0]

    estado, primera_pregunta = engine.iniciar(documento, seccion)

    assert "supuestos" in primera_pregunta.lower()
    assert estado.documento_id == str(documento.id)
    assert estado.seccion_id == seccion.id
    assert not estado.cerrada
    # 2 mensajes: kickoff (user) + respuesta de Claude (assistant)
    assert len(estado.mensajes) == 2
    assert estado.mensajes[1].rol == "assistant"


def test_responder_continua_la_entrevista() -> None:
    fake = FakeLLM(
        [
            "¿Qué tabla de mortalidad?",  # primera pregunta
            "¿Y qué año de la tabla?",  # segunda pregunta
        ]
    )
    engine = InterviewEngine(fake)
    documento = _documento_test()
    seccion = documento.secciones[0]

    estado, _ = engine.iniciar(documento, seccion)
    estado, respuesta, cerrada = engine.responder(
        documento, seccion, estado, "Usamos la tabla SOA 2017."
    )

    assert "año" in respuesta.lower()
    assert not cerrada
    assert estado.mensajes[-1].rol == "assistant"
    assert estado.mensajes[-1].contenido == respuesta


def test_responder_detecta_seccion_completa() -> None:
    fake = FakeLLM(
        [
            "Pregunta 1",
            "SECCION_COMPLETA\n\nResumen capturado: supuestos de mortalidad SOA 2017.",
        ]
    )
    engine = InterviewEngine(fake)
    documento = _documento_test()
    seccion = documento.secciones[0]

    estado, _ = engine.iniciar(documento, seccion)
    estado, _, cerrada = engine.responder(documento, seccion, estado, "Toda la información")

    assert cerrada is True
    assert estado.cerrada is True
    # El audit_trail del documento registró el cierre
    assert any(e.tipo == "seccion_completada" for e in documento.audit_trail)


def test_responder_sobre_seccion_cerrada_levanta_error() -> None:
    fake = FakeLLM(["primera pregunta", "SECCION_COMPLETA\nlisto"])
    engine = InterviewEngine(fake)
    documento = _documento_test()
    seccion = documento.secciones[0]

    estado, _ = engine.iniciar(documento, seccion)
    estado, _, cerrada = engine.responder(documento, seccion, estado, "respuesta")
    assert cerrada is True

    with pytest.raises(ValueError, match="ya está cerrada"):
        engine.responder(documento, seccion, estado, "otra respuesta")


def test_system_blocks_tienen_cache_control_en_contexto_fijo() -> None:
    """Validamos prompt caching: el primer bloque de system DEBE tener cache_control."""
    fake = FakeLLM(["pregunta"])
    engine = InterviewEngine(fake)
    documento = _documento_test()
    seccion = documento.secciones[0]

    engine.iniciar(documento, seccion)

    tarea, system_blocks, _ = fake.llamadas[0]
    assert tarea == "chat", "InterviewEngine debe pedir tarea='chat' (Sonnet 4.6)"
    assert len(system_blocks) >= 2
    # Los primeros dos bloques (contexto fijo + tono+instrucción) deben cachearse
    assert system_blocks[0].get("cache_control") == {"type": "ephemeral"}
    assert system_blocks[1].get("cache_control") == {"type": "ephemeral"}
    # El bloque variable (estado) NO debe tener cache_control
    assert (
        "cache_control" not in system_blocks[-1] or system_blocks[-1].get("cache_control") is None
    )
