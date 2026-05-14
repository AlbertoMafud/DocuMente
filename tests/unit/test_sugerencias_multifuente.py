"""Tests del use case SugerenciasMultiFuente."""

from __future__ import annotations

from src.core.models import Documento, FuenteContexto, MetadataModelo, Seccion
from src.core.usecases.sugerencias_multifuente import SugerenciasMultiFuente
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

    rellenadas = SugerenciasMultiFuente(llm).ejecutar(doc, fuentes)

    assert rellenadas == 1
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

    rellenadas = SugerenciasMultiFuente(llm).ejecutar(doc, [])

    assert rellenadas == 0
    assert len(llm.llamadas) == 0


def test_fuentes_con_texto_vacio_se_ignoran() -> None:
    """Fuente sin texto extraído no debe disparar llamada LLM."""
    doc = _doc_con_seccion_vacia()
    llm = FakeLLM(["nunca"])
    fuentes_vacias = [_fuente("vacia.txt", "")]

    rellenadas = SugerenciasMultiFuente(llm).ejecutar(doc, fuentes_vacias)

    assert rellenadas == 0
    assert len(llm.llamadas) == 0


def test_si_llm_dice_sin_informacion_no_rellena_seccion() -> None:
    """Si Claude devuelve el marcador `[Sin información...]`, no se inyecta."""
    doc = _doc_con_seccion_vacia()
    llm = FakeLLM(["[Sin información en fuentes adjuntas]"])
    fuentes = [_fuente("irrelevante.txt", "Texto que no toca la sección.")]

    rellenadas = SugerenciasMultiFuente(llm).ejecutar(doc, fuentes)

    assert rellenadas == 0
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

    rellenadas = SugerenciasMultiFuente(llm).ejecutar(doc, fuentes, max_secciones=0)

    assert rellenadas == 0


def test_fuentes_default_lee_del_documento() -> None:
    """Si no pasas `fuentes`, las toma de `documento.fuentes_contexto`."""
    doc = _doc_con_seccion_vacia()
    doc.fuentes_contexto.append(_fuente("doc_interno.txt", "Contenido del archivo."))
    llm = FakeLLM(["Sugerencia desde fuente del doc."])

    rellenadas = SugerenciasMultiFuente(llm).ejecutar(doc)

    assert rellenadas == 1
