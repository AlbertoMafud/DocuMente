"""Tests del use case SugerenciasMultiFuente."""

from __future__ import annotations

from src.core.models import Documento, FuenteContexto, MetadataModelo, Seccion
from src.core.usecases.sugerencias_multifuente import (
    ResultadoSugerencias,
    SugerenciasMultiFuente,
)
from tests.unit.test_interview_engine import FakeLLM


def _doc_con_seccion_vacia() -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="X"),
        secciones=[
            Seccion(
                id="2.1.model_uses",
                nombre="Model Uses",
                numero="2.1",
                obligatoria=True,
                contenido=None,
                completitud="vacia",
                intencion="Para qué se usa el modelo.",
            ),
            Seccion(
                id="2.2.model_scope",
                nombre="Model Scope",
                numero="2.2",
                obligatoria=True,
                contenido="Ya tiene contenido",
                completitud="completa",
            ),
        ],
    )


def _fuente(nombre: str, texto: str) -> FuenteContexto:
    return FuenteContexto(nombre_archivo=nombre, tipo="txt", texto_extraido=texto)


def test_sugiere_solo_para_secciones_vacias() -> None:
    """No debe pisar secciones con contenido existente."""
    doc = _doc_con_seccion_vacia()
    llm = FakeLLM(["Sugerencia para 2.1 basada en fuente. (fuente: notas.txt)"])
    fuentes = [_fuente("notas.txt", "Texto fuente con información relevante.")]

    resultado = SugerenciasMultiFuente(llm).ejecutar(doc, fuentes)

    assert isinstance(resultado, ResultadoSugerencias)
    assert resultado.secciones_pobladas == 1
    assert resultado.secciones_intentadas == 1
    assert resultado.fuentes_usadas == 1
    assert resultado.errores == []
    seccion_vacia = doc.seccion_por_id("2.1.model_uses")
    seccion_completa = doc.seccion_por_id("2.2.model_scope")
    assert seccion_vacia is not None
    assert seccion_completa is not None
    assert seccion_vacia.contenido is not None
    assert "[Borrador automático — revisar]" in seccion_vacia.contenido
    assert "Sugerencia para 2.1" in seccion_vacia.contenido
    assert seccion_vacia.completitud == "parcial"
    # La que ya tenía contenido no se tocó
    assert seccion_completa.contenido == "Ya tiene contenido"
    assert seccion_completa.completitud == "completa"


def test_sin_fuentes_no_llama_llm() -> None:
    doc = _doc_con_seccion_vacia()
    llm = FakeLLM(["nunca"])

    resultado = SugerenciasMultiFuente(llm).ejecutar(doc, [])

    assert resultado.secciones_pobladas == 0
    assert resultado.fuentes_usadas == 0
    assert len(llm.llamadas) == 0


def test_fuentes_con_texto_vacio_se_ignoran() -> None:
    """Fuente sin texto extraído no debe disparar llamada LLM."""
    doc = _doc_con_seccion_vacia()
    llm = FakeLLM(["nunca"])
    fuentes_vacias = [_fuente("vacia.txt", "")]

    resultado = SugerenciasMultiFuente(llm).ejecutar(doc, fuentes_vacias)

    assert resultado.secciones_pobladas == 0
    assert resultado.fuentes_usadas == 0
    assert len(llm.llamadas) == 0


def test_si_llm_dice_sin_informacion_no_rellena_seccion() -> None:
    """Si Claude devuelve el marcador `[Sin información...]`, no se inyecta."""
    doc = _doc_con_seccion_vacia()
    llm = FakeLLM(["[Sin información en fuentes adjuntas]"])
    fuentes = [_fuente("irrelevante.txt", "Texto que no toca la sección.")]

    resultado = SugerenciasMultiFuente(llm).ejecutar(doc, fuentes)

    assert resultado.secciones_pobladas == 0
    assert resultado.secciones_intentadas == 1
    seccion = doc.seccion_por_id("2.1.model_uses")
    assert seccion is not None
    assert seccion.completitud == "vacia"
    assert seccion.contenido is None


def test_registra_metricas_uso() -> None:
    doc = _doc_con_seccion_vacia()
    llm = FakeLLM(["draft"])
    fuentes = [_fuente("a.txt", "texto")]

    SugerenciasMultiFuente(llm).ejecutar(doc, fuentes)

    assert len(doc.metricas_uso.llamadas) >= 1


def test_max_secciones_limita_el_alcance() -> None:
    """`max_secciones=0` debe no rellenar nada."""
    doc = _doc_con_seccion_vacia()
    llm = FakeLLM(["draft"])
    fuentes = [_fuente("a.txt", "texto")]

    resultado = SugerenciasMultiFuente(llm).ejecutar(doc, fuentes, max_secciones=0)

    assert resultado.secciones_pobladas == 0


def test_fuentes_default_lee_del_documento() -> None:
    """Si no pasas `fuentes`, las toma de `documento.fuentes_contexto`."""
    doc = _doc_con_seccion_vacia()
    doc.fuentes_contexto.append(_fuente("doc_interno.txt", "Contenido del archivo."))
    llm = FakeLLM(["Sugerencia desde fuente del doc."])

    resultado = SugerenciasMultiFuente(llm).ejecutar(doc)

    assert resultado.secciones_pobladas == 1


def test_error_llm_se_propaga_a_resultado_y_no_aborta_flujo() -> None:
    """Si el LLM crashea para una sección, se registra error y se sigue."""

    class CrashLLM:
        def __init__(self) -> None:
            self.llamadas = 0

        def chat(self, **_kwargs: object) -> object:
            self.llamadas += 1
            raise RuntimeError("simulated API failure")

    doc = _doc_con_seccion_vacia()
    fuentes = [_fuente("notas.txt", "texto útil")]

    resultado = SugerenciasMultiFuente(CrashLLM()).ejecutar(doc, fuentes)  # type: ignore[arg-type]

    assert resultado.secciones_pobladas == 0
    assert resultado.secciones_intentadas == 1
    assert resultado.hubo_errores is True
    assert len(resultado.errores) == 1
    assert "2.1.model_uses" in resultado.errores[0]
    assert "RuntimeError" in resultado.errores[0]
    # La sección original NO se mutó (sigue vacía)
    seccion = doc.seccion_por_id("2.1.model_uses")
    assert seccion is not None
    assert seccion.completitud == "vacia"
    assert seccion.contenido is None
