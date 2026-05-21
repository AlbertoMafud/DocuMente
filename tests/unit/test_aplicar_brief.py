"""Tests del use case AplicarBrief — Brief Inicial → borradores."""

from __future__ import annotations

from src.core.models import Documento, MetadataModelo
from src.core.template_catalog import construir_secciones_vacias
from src.core.usecases.aplicar_brief import PREGUNTAS_BRIEF, AplicarBrief, ResultadoBrief
from tests.unit.test_interview_engine import FakeLLM


def _doc_nuevo() -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="X"),
        secciones=construir_secciones_vacias(),
    )


def test_preguntas_brief_tiene_10_items() -> None:
    assert len(PREGUNTAS_BRIEF) == 10


def test_cada_pregunta_apunta_a_seccion_existente_del_catalogo() -> None:
    """Las 10 preguntas mapean a IDs reales del catálogo NYL — sin typos."""
    ids_validos = {s.id for s in construir_secciones_vacias()}
    for q in PREGUNTAS_BRIEF:
        assert q.seccion_id in ids_validos, f"Pregunta {q.numero} apunta a ID inexistente"


def test_aplicar_brief_genera_borrador_por_respuesta_no_vacia() -> None:
    doc = _doc_nuevo()
    llm = FakeLLM(["Draft 1", "Draft 2"])
    respuestas = {1: "Respuesta uno", 2: "Respuesta dos"}

    resultado = AplicarBrief(llm).ejecutar(doc, respuestas)

    assert isinstance(resultado, ResultadoBrief)
    assert resultado.secciones_aplicadas == 2
    assert resultado.respuestas_recibidas == 2
    assert resultado.errores == []
    s1 = doc.seccion_por_id(PREGUNTAS_BRIEF[0].seccion_id)
    s2 = doc.seccion_por_id(PREGUNTAS_BRIEF[1].seccion_id)
    assert s1 is not None and s1.contenido is not None
    assert "[Borrador — revisar]" in s1.contenido
    assert "Draft 1" in s1.contenido
    assert s1.completitud == "parcial"
    assert s2 is not None and s2.contenido is not None
    assert "Draft 2" in s2.contenido


def test_respuesta_vacia_no_dispara_llm() -> None:
    doc = _doc_nuevo()
    llm = FakeLLM(["nunca"])
    respuestas = {1: "", 2: "   "}

    resultado = AplicarBrief(llm).ejecutar(doc, respuestas)

    assert resultado.secciones_aplicadas == 0
    assert resultado.respuestas_recibidas == 0
    assert len(llm.llamadas) == 0


def test_aplicar_brief_no_sobreescribe_seccion_con_contenido() -> None:
    """Si la sección ya tiene contenido (caso 'Mejorar existente'), no se pisa."""
    doc = _doc_nuevo()
    # Manualmente pongo contenido en la sección destino de la pregunta 1
    pregunta = PREGUNTAS_BRIEF[0]
    seccion_existente = doc.seccion_por_id(pregunta.seccion_id)
    assert seccion_existente is not None
    seccion_existente.contenido = "Contenido previo del usuario"
    seccion_existente.completitud = "completa"

    llm = FakeLLM(["draft que no debe aplicarse"])
    resultado = AplicarBrief(llm).ejecutar(doc, {1: "Nueva respuesta"})

    assert resultado.secciones_aplicadas == 0
    assert resultado.respuestas_recibidas == 1  # se contó pero no se aplicó
    s = doc.seccion_por_id(pregunta.seccion_id)
    assert s is not None
    assert s.contenido == "Contenido previo del usuario"
    assert s.completitud == "completa"


def test_aplicar_brief_en_idioma_en_usa_prefijo_draft_review() -> None:
    """Con idioma='en', el prefijo del borrador es '[Draft — review]'."""
    doc = _doc_nuevo()
    llm = FakeLLM(["English draft"])
    respuestas = {1: "Some response"}

    AplicarBrief(llm).ejecutar(doc, respuestas, idioma="en")

    s = doc.seccion_por_id(PREGUNTAS_BRIEF[0].seccion_id)
    assert s is not None and s.contenido is not None
    assert "[Draft — review]" in s.contenido


def test_aplicar_brief_registra_metricas() -> None:
    doc = _doc_nuevo()
    llm = FakeLLM(["draft"])
    respuestas = {1: "Algo"}

    AplicarBrief(llm).ejecutar(doc, respuestas)

    assert len(doc.metricas_uso.llamadas) == 1


def test_aplicar_brief_propaga_errores_llm_sin_abortar() -> None:
    """Si el LLM crashea en una pregunta, se sigue con las demás."""
    from src.llm import LLMResponse

    class FlakyLLM:
        def __init__(self) -> None:
            self.llamadas = 0

        def chat(self, **_kwargs: object) -> LLMResponse:
            self.llamadas += 1
            if self.llamadas == 1:
                raise RuntimeError("rate limit simulado")
            return LLMResponse(
                text="Draft OK",
                modelo_usado="claude-haiku-4-5",
                input_tokens=10,
                output_tokens=5,
                cache_read_tokens=0,
                cache_creation_tokens=0,
            )

    doc = _doc_nuevo()
    resultado = AplicarBrief(FlakyLLM()).ejecutar(  # type: ignore[arg-type]
        doc, {1: "primera respuesta", 2: "segunda respuesta"}
    )

    assert resultado.respuestas_recibidas == 2
    assert resultado.secciones_aplicadas == 1  # solo la segunda pasó
    assert len(resultado.errores) == 1
    assert "Pregunta 1" in resultado.errores[0]
    assert "RuntimeError" in resultado.errores[0]
