"""Tests del StructureRealigner (B.1)."""

from __future__ import annotations

from src.core.models import Documento
from src.core.models.documento import MetadataModelo
from src.core.template_catalog import construir_secciones_vacias
from src.core.usecases.structure_realigner import (
    ResultadoRealign,
    StructureRealigner,
    _parsear_json_respuesta,
)
from tests.unit.test_interview_engine import FakeLLM


def _doc_con_cobertura_baja() -> Documento:
    """Documento con todas las secciones vacías (cobertura 0%)."""
    return Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="X"),
        secciones=construir_secciones_vacias(),
    )


def _doc_con_cobertura_alta() -> Documento:
    """Documento con la mayoría de secciones pobladas (cobertura > 50%)."""
    doc = _doc_con_cobertura_baja()
    # Llenar 80% de las secciones
    secciones = doc.secciones
    n_llenar = int(0.8 * len(secciones))
    for s in secciones[:n_llenar]:
        s.contenido = "Contenido detectado por el reader"
        s.completitud = "completa"
    return doc


def test_no_se_ejecuta_si_cobertura_es_mayor_o_igual_al_umbral() -> None:
    """Si el reader ya pobló >50%, NO debe llamar al LLM."""
    doc = _doc_con_cobertura_alta()
    llm = FakeLLM(["nunca debería ser llamado"])

    resultado = StructureRealigner(llm).ejecutar(
        doc, texto_ancla_crudo="texto del ancla", umbral_cobertura=0.5
    )

    assert isinstance(resultado, ResultadoRealign)
    assert resultado.ejecutado is False
    assert resultado.secciones_remapeadas == 0
    assert len(llm.llamadas) == 0


def test_no_se_ejecuta_si_texto_ancla_esta_vacio() -> None:
    doc = _doc_con_cobertura_baja()
    llm = FakeLLM(["nunca"])

    resultado = StructureRealigner(llm).ejecutar(doc, texto_ancla_crudo="   ")

    assert resultado.ejecutado is False
    assert len(llm.llamadas) == 0


def test_remapea_fragmentos_a_secciones_segun_respuesta_llm() -> None:
    """LLM devuelve JSON mapeando fragmentos. El use case los aplica."""
    doc = _doc_con_cobertura_baja()
    respuesta_json = (
        '{"4.4.assumptions": "Supuesto verbatim del ancla.", '
        '"5.1.raw_data": "Fuentes de datos enumeradas literalmente."}'
    )
    llm = FakeLLM([respuesta_json])

    resultado = StructureRealigner(llm).ejecutar(
        doc, texto_ancla_crudo="texto suficientemente largo del ancla"
    )

    assert resultado.ejecutado is True
    assert resultado.secciones_remapeadas == 2
    s_assump = doc.seccion_por_id("4.4.assumptions")
    s_raw = doc.seccion_por_id("5.1.raw_data")
    assert s_assump is not None and s_assump.contenido is not None
    assert "[Re-estructurado desde ancla — revisar]" in s_assump.contenido
    assert "Supuesto verbatim del ancla." in s_assump.contenido
    assert s_assump.completitud == "parcial"
    assert s_raw is not None and "Fuentes de datos" in (s_raw.contenido or "")


def test_no_sobreescribe_secciones_que_ya_tienen_contenido() -> None:
    """Si el reader detectó una sección, el realigner no la pisa."""
    doc = _doc_con_cobertura_baja()
    # Pre-poblar manualmente una sección como si el reader la hubiera detectado
    s_existente = doc.seccion_por_id("4.4.assumptions")
    assert s_existente is not None
    s_existente.contenido = "Contenido detectado por reader"
    s_existente.completitud = "completa"

    respuesta_json = '{"4.4.assumptions": "Fragmento del ancla que NO debe aplicarse"}'
    llm = FakeLLM([respuesta_json])

    resultado = StructureRealigner(llm).ejecutar(doc, texto_ancla_crudo="texto del ancla")

    # Ejecutó (cobertura era baja) pero NO remapeó 4.4 porque ya tenía contenido
    assert resultado.ejecutado is True
    assert resultado.secciones_remapeadas == 0
    s = doc.seccion_por_id("4.4.assumptions")
    assert s is not None
    assert s.contenido == "Contenido detectado por reader"
    assert s.completitud == "completa"


def test_idioma_en_usa_prefijo_en_ingles() -> None:
    doc = _doc_con_cobertura_baja()
    llm = FakeLLM(['{"4.4.assumptions": "An assumption from the anchor."}'])

    StructureRealigner(llm).ejecutar(doc, texto_ancla_crudo="anchor text", idioma="en")

    s = doc.seccion_por_id("4.4.assumptions")
    assert s is not None and s.contenido is not None
    assert "[Re-structured from anchor — review]" in s.contenido


def test_resultado_reporta_cobertura_antes_y_despues() -> None:
    doc = _doc_con_cobertura_baja()  # cobertura inicial = 0
    llm = FakeLLM(['{"4.4.assumptions": "Frag1", "5.1.raw_data": "Frag2"}'])

    resultado = StructureRealigner(llm).ejecutar(doc, texto_ancla_crudo="texto del ancla")

    assert resultado.cobertura_antes == 0.0
    assert resultado.cobertura_despues > 0.0
    # 2 secciones de 28 ≈ 0.0714
    assert resultado.cobertura_despues > resultado.cobertura_antes


def test_seccion_inexistente_en_mapeo_se_ignora_sin_fallar() -> None:
    """Si el LLM inventa una key que no existe en el catálogo, se ignora."""
    doc = _doc_con_cobertura_baja()
    llm = FakeLLM(['{"99.99.fake": "fragmento", "4.4.assumptions": "supuesto válido"}'])

    resultado = StructureRealigner(llm).ejecutar(doc, texto_ancla_crudo="texto")

    assert resultado.secciones_remapeadas == 1  # solo el válido
    s = doc.seccion_por_id("4.4.assumptions")
    assert s is not None and "supuesto válido" in (s.contenido or "")


def test_respuesta_llm_json_invalido_propaga_error_sin_pisar_documento() -> None:
    """Si el JSON no parsea, resultado lleva 0 remapeos y NO levanta excepción."""
    doc = _doc_con_cobertura_baja()
    llm = FakeLLM(["esto no es JSON, es prosa libre"])

    resultado = StructureRealigner(llm).ejecutar(doc, texto_ancla_crudo="texto")

    # Ejecutó (cobertura baja, hubo texto), parseó 0
    assert resultado.ejecutado is True
    assert resultado.secciones_remapeadas == 0
    # El documento no cambió
    assert all(s.completitud == "vacia" for s in doc.secciones)


def test_llm_crashea_se_registra_error_sin_aborta_flujo() -> None:
    """Si el LLM lanza excepción, devuelve resultado con errores."""

    class CrashLLM:
        def __init__(self) -> None:
            self.llamadas = 0

        def chat(self, **_kwargs: object) -> object:
            self.llamadas += 1
            raise RuntimeError("API timeout simulado")

    doc = _doc_con_cobertura_baja()

    resultado = StructureRealigner(CrashLLM()).ejecutar(  # type: ignore[arg-type]
        doc, texto_ancla_crudo="texto"
    )

    assert resultado.ejecutado is True
    assert resultado.secciones_remapeadas == 0
    assert resultado.hubo_errores is True
    assert "RuntimeError" in resultado.errores[0]


def test_texto_largo_se_trunca_para_control_de_costo() -> None:
    """Texto mayor a max_texto_chars se trunca antes del LLM."""
    doc = _doc_con_cobertura_baja()
    texto_largo = "a" * 100_000
    llm = FakeLLM(['{"4.4.assumptions": "supuesto"}'])

    StructureRealigner(llm).ejecutar(doc, texto_ancla_crudo=texto_largo, max_texto_chars=5_000)

    # Verificamos que la llamada al LLM tuvo texto truncado
    _tarea, _system, messages = llm.llamadas[0]
    contenido_usuario = messages[0]["content"]
    assert isinstance(contenido_usuario, str)
    # El texto del ancla en el prompt no puede exceder 5000 + boilerplate
    assert "a" * 5_001 not in contenido_usuario


def test_registra_metricas_uso_en_documento() -> None:
    doc = _doc_con_cobertura_baja()
    llm = FakeLLM(['{"4.4.assumptions": "frag"}'])
    assert len(doc.metricas_uso.llamadas) == 0

    StructureRealigner(llm).ejecutar(doc, texto_ancla_crudo="texto")

    assert len(doc.metricas_uso.llamadas) >= 1


# Tests del parser de JSON --------------------------------------------------


def test_parsear_json_acepta_fences_de_codigo() -> None:
    texto = '```json\n{"a": "b"}\n```'
    assert _parsear_json_respuesta(texto) == {"a": "b"}


def test_parsear_json_acepta_prosa_antes_y_despues() -> None:
    texto = 'Aquí va la respuesta:\n{"a": "b"}\nEspero te sirva.'
    assert _parsear_json_respuesta(texto) == {"a": "b"}


def test_parsear_json_filtra_values_vacios() -> None:
    texto = '{"a": "contenido", "b": "  ", "c": ""}'
    assert _parsear_json_respuesta(texto) == {"a": "contenido"}


def test_parsear_json_devuelve_dict_vacio_si_invalido() -> None:
    assert _parsear_json_respuesta("not json") == {}
    assert _parsear_json_respuesta("") == {}


def test_documento_cobertura_catalogo_property() -> None:
    """La propiedad nueva devuelve la fracción de secciones con contenido."""
    doc = _doc_con_cobertura_baja()
    assert doc.cobertura_catalogo == 0.0

    # Poblar 5 de 28
    for s in doc.secciones[:5]:
        s.contenido = "algo"
    assert doc.cobertura_catalogo == 5 / len(doc.secciones)
