"""Tests del DocumentPolisher (B.2)."""

from __future__ import annotations

from src.core.models import Documento
from src.core.models.documento import MetadataModelo
from src.core.models.seccion import Seccion
from src.core.usecases.document_polisher import (
    DocumentPolisher,
    ResultadoPolish,
    SugerenciaPolish,
    _hallazgo_valido,
    _parsear_array_respuesta,
    _serializar_documento,
)
from tests.unit.test_interview_engine import FakeLLM


def _doc_con_secciones_pobladas() -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="Test"),
        secciones=[
            Seccion(
                id="4.2.theory",
                nombre="Theory",
                numero="4.2",
                obligatoria=True,
                contenido="El modelo usa GBM con paths estocásticos.",
                completitud="completa",
            ),
            Seccion(
                id="4.3.risk_drivers",
                nombre="Risk Drivers",
                numero="4.3",
                obligatoria=True,
                contenido="El modelo es determinista, sin componente estocástico.",
                completitud="completa",
            ),
        ],
    )


def test_revisar_devuelve_sugerencias_parseadas() -> None:
    """LLM devuelve un array JSON válido → se parsea a SugerenciaPolish."""
    doc = _doc_con_secciones_pobladas()
    respuesta = (
        "["
        '{"seccion_id": "4.3.risk_drivers", '
        '"tipo": "contradiccion", '
        '"severidad": "alta", '
        '"descripcion": "4.2 dice GBM estocástico, 4.3 dice determinista.", '
        '"secciones_afectadas": ["4.2.theory", "4.3.risk_drivers"], '
        '"texto_sugerido": "Alinear: o 4.2 omite GBM, o 4.3 reconoce el componente estocástico."}'
        "]"
    )
    llm = FakeLLM([respuesta])

    resultado = DocumentPolisher(llm).revisar(doc)

    assert isinstance(resultado, ResultadoPolish)
    assert resultado.ejecutado is True
    assert len(resultado.sugerencias) == 1
    s = resultado.sugerencias[0]
    assert s.tipo == "contradiccion"
    assert s.severidad == "alta"
    assert "GBM" in s.descripcion
    assert "4.2.theory" in s.secciones_afectadas
    assert "4.3.risk_drivers" in s.secciones_afectadas
    assert s.texto_sugerido is not None
    assert resultado.n_alta == 1
    assert resultado.n_media == 0
    assert resultado.n_baja == 0


def test_revisar_sin_observaciones_devuelve_lista_vacia() -> None:
    doc = _doc_con_secciones_pobladas()
    llm = FakeLLM(["[]"])

    resultado = DocumentPolisher(llm).revisar(doc)

    assert resultado.ejecutado is True
    assert resultado.sugerencias == []
    assert resultado.hubo_errores is False


def test_revisar_ordena_por_severidad_alta_primero() -> None:
    doc = _doc_con_secciones_pobladas()
    respuesta = (
        "["
        '{"seccion_id": "4.2.theory", "tipo": "redaccion", "severidad": "baja", '
        '"descripcion": "menor"},'
        '{"seccion_id": "4.3.risk_drivers", "tipo": "contradiccion", "severidad": "alta", '
        '"descripcion": "crítico"},'
        '{"seccion_id": "4.2.theory", "tipo": "inconsistencia", "severidad": "media", '
        '"descripcion": "moderado"}'
        "]"
    )
    llm = FakeLLM([respuesta])

    resultado = DocumentPolisher(llm).revisar(doc)

    severidades = [s.severidad for s in resultado.sugerencias]
    assert severidades == ["alta", "media", "baja"]


def test_revisar_filtra_hallazgos_malformados() -> None:
    """Items con tipo inválido o severidad faltante se descartan."""
    doc = _doc_con_secciones_pobladas()
    respuesta = (
        "["
        '{"seccion_id": "4.2.theory", "tipo": "invento_no_existe", "severidad": "alta",'
        ' "descripcion": "inválido"},'
        '{"seccion_id": "", "tipo": "redaccion", "severidad": "media", "descripcion": "sin id"},'
        '{"seccion_id": "4.3.risk_drivers", "tipo": "redaccion", "severidad": "media",'
        ' "descripcion": "válido"}'
        "]"
    )
    llm = FakeLLM([respuesta])

    resultado = DocumentPolisher(llm).revisar(doc)

    assert len(resultado.sugerencias) == 1
    assert resultado.sugerencias[0].descripcion == "válido"


def test_revisar_llm_crashea_resulta_en_errores() -> None:
    class CrashLLM:
        def chat(self, **_kwargs: object) -> object:
            raise RuntimeError("API timeout")

    doc = _doc_con_secciones_pobladas()
    resultado = DocumentPolisher(CrashLLM()).revisar(doc)  # type: ignore[arg-type]

    assert resultado.ejecutado is True
    assert resultado.sugerencias == []
    assert resultado.hubo_errores is True
    assert "RuntimeError" in resultado.errores[0]


def test_revisar_respuesta_no_json_devuelve_lista_vacia() -> None:
    doc = _doc_con_secciones_pobladas()
    llm = FakeLLM(["respuesta libre sin JSON"])

    resultado = DocumentPolisher(llm).revisar(doc)

    assert resultado.ejecutado is True
    assert resultado.sugerencias == []
    assert resultado.hubo_errores is False  # JSON inválido != error de LLM


def test_revisar_registra_metricas_uso() -> None:
    doc = _doc_con_secciones_pobladas()
    llm = FakeLLM(["[]"])

    DocumentPolisher(llm).revisar(doc)

    assert len(doc.metricas_uso.llamadas) >= 1


def test_revisar_documento_sin_secciones_no_llama_llm() -> None:
    doc = Documento(metadata_modelo=MetadataModelo(nombre_modelo="X"), secciones=[])
    llm = FakeLLM(["nunca"])

    resultado = DocumentPolisher(llm).revisar(doc)

    assert resultado.ejecutado is False
    assert len(llm.llamadas) == 0


# --- Helpers internos --------------------------------------------------------


def test_serializar_documento_incluye_seccion_vacia_y_omitida() -> None:
    """Secciones vacías/omitidas se marcan explícitamente para detectar refs rotas."""
    doc = Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="X"),
        secciones=[
            Seccion(
                id="1.1",
                nombre="A",
                numero="1.1",
                obligatoria=True,
                contenido="poblada",
                completitud="completa",
            ),
            Seccion(id="2.1", nombre="B", numero="2.1", obligatoria=True, completitud="vacia"),
            Seccion(
                id="3.1",
                nombre="C",
                numero="3.1",
                obligatoria=False,
                completitud="omitida",
                motivo_omision="No aplica",
            ),
        ],
    )
    texto = _serializar_documento(doc)
    assert "poblada" in texto
    assert "[EMPTY]" in texto
    assert "[OMITTED — No aplica]" in texto


def test_serializar_documento_trunca_secciones_largas() -> None:
    doc = Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="X"),
        secciones=[
            Seccion(
                id="1.1",
                nombre="A",
                numero="1.1",
                obligatoria=True,
                contenido="x" * 10_000,
                completitud="completa",
            ),
        ],
    )
    texto = _serializar_documento(doc, max_chars_por_seccion=500)
    assert "[…truncated for length…]" in texto


def test_parsear_array_acepta_fences() -> None:
    texto = '```json\n[{"a": "b"}]\n```'
    assert _parsear_array_respuesta(texto) == [{"a": "b"}]


def test_parsear_array_acepta_prosa_alrededor() -> None:
    texto = 'Aquí va: [{"a": "b"}] espero te sirva.'
    assert _parsear_array_respuesta(texto) == [{"a": "b"}]


def test_parsear_array_invalido_devuelve_lista_vacia() -> None:
    assert _parsear_array_respuesta("not json") == []
    assert _parsear_array_respuesta('{"not": "array"}') == []


def test_hallazgo_valido_acepta_dict_correcto() -> None:
    d = {
        "seccion_id": "1.1",
        "tipo": "redaccion",
        "severidad": "media",
        "descripcion": "x",
    }
    sug = _hallazgo_valido(d)
    assert isinstance(sug, SugerenciaPolish)
    assert sug.secciones_afectadas == ["1.1"]  # default = [seccion_id]


def test_hallazgo_valido_rechaza_tipo_invalido() -> None:
    d = {
        "seccion_id": "1.1",
        "tipo": "tipo_inventado",
        "severidad": "media",
        "descripcion": "x",
    }
    assert _hallazgo_valido(d) is None
