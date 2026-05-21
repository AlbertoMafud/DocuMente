"""Tests del TraductorDocumento — traducción al inglés corporativo americano."""

from __future__ import annotations

from src.core.models import Apendice, Documento, MetadataModelo, Seccion
from src.core.usecases.traductor import IDIOMAS_SOPORTADOS, TraductorDocumento
from tests.unit.test_interview_engine import FakeLLM


def _doc_seed() -> Documento:
    return Documento(
        metadata_modelo=MetadataModelo(
            nombre_modelo="Modelo VNB",
            intended_use="Cálculo trimestral del valor de nuevo negocio",
            use_restrictions="Solo para reporting interno",
        ),
        secciones=[
            Seccion(
                id="2.1.model_uses",
                nombre="Model Uses",
                numero="2.1",
                obligatoria=True,
                contenido="El modelo calcula VNB trimestralmente.",
                completitud="completa",
            ),
            Seccion(
                id="2.2.model_scope",
                nombre="Model Scope",
                numero="2.2",
                obligatoria=True,
                contenido="",
                completitud="vacia",
            ),
        ],
        apendices=[
            Apendice(
                seccion_origen_id="2.1.model_uses",
                titulo="Tabla de factores",
                contenido_md="**Datos:** 5 productos\n\n| Producto | Factor |\n|---|---|\n| A | 0.1 |",
            )
        ],
    )


def test_traducir_devuelve_doc_con_secciones_en_ingles() -> None:
    """Cada sección con contenido se traduce vía LLM.

    Orden de procesamiento: intended_use → use_restrictions → secciones → apéndices.
    """
    llm = FakeLLM(
        [
            "Quarterly calculation of new business value.",  # intended_use
            "For internal reporting only.",  # use_restrictions
            "The model calculates VNB on a quarterly basis.",  # sección 2.1
            "**Data:** 5 products\n\n| Product | Factor |\n|---|---|\n| A | 0.1 |",  # apéndice contenido
            "Factor table",  # apéndice título
        ]
    )
    doc = _doc_seed()

    traducido = TraductorDocumento(llm).traducir(doc, idioma_objetivo="en")

    seccion_traducida = traducido.seccion_por_id("2.1.model_uses")
    assert seccion_traducida is not None
    assert (
        "VNB" in seccion_traducida.contenido or "quarterly" in seccion_traducida.contenido.lower()
    )
    assert traducido.metadata_modelo.intended_use.startswith("Quarterly")
    assert traducido.apendices[0].titulo == "Factor table"


def test_traducir_no_llama_llm_para_seccion_vacia() -> None:
    """Secciones sin contenido no necesitan traducción."""
    llm = FakeLLM(["never called for empty"] * 10)
    doc = Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="X"),
        secciones=[
            Seccion(
                id="s1",
                nombre="X",
                numero="1",
                obligatoria=True,
                contenido="",
                completitud="vacia",
            )
        ],
    )
    TraductorDocumento(llm).traducir(doc, idioma_objetivo="en")

    # No debe haber llamada para sección vacía
    assert len(llm.llamadas) == 0


def test_traducir_es_devuelve_documento_sin_modificar() -> None:
    """Si idioma_objetivo == 'es', no llama LLM y devuelve doc sin cambios."""
    llm = FakeLLM(["nunca debería llamarse"])
    doc = _doc_seed()

    resultado = TraductorDocumento(llm).traducir(doc, idioma_objetivo="es")

    assert resultado is doc
    assert len(llm.llamadas) == 0


def test_traducir_seccion_omitida_con_motivo_predefinido_no_llama_llm() -> None:
    """Motivo predefinido en español ('No aplica al modelo') se traduce por
    swap directo (no llama LLM) a 'Not applicable to the model'.
    """
    llm = FakeLLM(["No deberia llamarse"] * 5)
    doc = Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="X"),
        secciones=[
            Seccion(
                id="s1",
                nombre="X",
                numero="1",
                obligatoria=True,
                contenido=None,
                completitud="omitida",
                motivo_omision="No aplica al modelo",
            )
        ],
    )
    traducido = TraductorDocumento(llm).traducir(doc, idioma_objetivo="en")

    s = traducido.seccion_por_id("s1")
    assert s is not None
    assert s.completitud == "omitida"
    assert s.motivo_omision == "Not applicable to the model"
    assert len(llm.llamadas) == 0


def test_traducir_seccion_omitida_con_motivo_libre_llama_llm() -> None:
    """Motivo de texto libre (de 'Otro especificar') pasa por LLM."""
    llm = FakeLLM(["Free-text reason translated to English"])
    doc = Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="X"),
        secciones=[
            Seccion(
                id="s1",
                nombre="X",
                numero="1",
                obligatoria=True,
                contenido=None,
                completitud="omitida",
                motivo_omision="Razón de texto libre que el usuario tipeó",
            )
        ],
    )
    traducido = TraductorDocumento(llm).traducir(doc, idioma_objetivo="en")

    s = traducido.seccion_por_id("s1")
    assert s is not None
    assert s.motivo_omision == "Free-text reason translated to English"
    assert len(llm.llamadas) == 1


def test_traducir_motivo_predefinido_con_comentario_separa_y_traduce() -> None:
    """Motivo con la forma '<predefinido> — <comentario>': swap del predefinido
    + LLM solo para el comentario libre.
    """
    llm = FakeLLM(["the model does not use ESG"])
    doc = Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="X"),
        secciones=[
            Seccion(
                id="s1",
                nombre="X",
                numero="1",
                obligatoria=True,
                contenido=None,
                completitud="omitida",
                motivo_omision="No aplica al modelo — el modelo no usa ESG",
            )
        ],
    )
    traducido = TraductorDocumento(llm).traducir(doc, idioma_objetivo="en")

    s = traducido.seccion_por_id("s1")
    assert s is not None
    assert s.motivo_omision == "Not applicable to the model — the model does not use ESG"
    assert len(llm.llamadas) == 1  # solo el comentario


def test_traducir_seccion_omitida_sin_motivo_no_llama_llm() -> None:
    """Sección omitida sin motivo no debe llamar LLM ni romper."""
    llm = FakeLLM(["nunca"] * 3)
    doc = Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="X"),
        secciones=[
            Seccion(
                id="s1",
                nombre="X",
                numero="1",
                obligatoria=True,
                contenido=None,
                completitud="omitida",
                motivo_omision=None,
            )
        ],
    )
    TraductorDocumento(llm).traducir(doc, idioma_objetivo="en")
    assert len(llm.llamadas) == 0


def test_traducir_tarea_correcta_chat_no_drafting() -> None:
    """Traducción usa tarea='chat' (Sonnet) — no necesitamos calidad Opus para traducir."""
    llm = FakeLLM(["translation"] * 10)
    doc = _doc_seed()
    TraductorDocumento(llm).traducir(doc, idioma_objetivo="en")

    for tarea, _, _ in llm.llamadas:
        assert tarea == "chat", f"Esperaba tarea 'chat', se usó '{tarea}'"


def test_traducir_registra_metricas_uso() -> None:
    llm = FakeLLM(["translation"] * 10)
    doc = _doc_seed()
    assert len(doc.metricas_uso.llamadas) == 0

    TraductorDocumento(llm).traducir(doc, idioma_objetivo="en")

    assert len(doc.metricas_uso.llamadas) > 0


def test_idiomas_soportados_incluye_es_y_en() -> None:
    assert "es" in IDIOMAS_SOPORTADOS
    assert "en" in IDIOMAS_SOPORTADOS


def test_idiomas_soportados_incluye_modos_normalize_y_bilingue() -> None:
    assert "es_normalize" in IDIOMAS_SOPORTADOS
    assert "en_normalize" in IDIOMAS_SOPORTADOS
    assert "bilingue" in IDIOMAS_SOPORTADOS


def test_modo_bilingue_no_toca_documento() -> None:
    """Modo 'bilingue' es no-op: documento sale tal cual entró."""
    llm = FakeLLM(["nunca"])
    doc = _doc_seed()
    contenido_original = doc.seccion_por_id("2.1.model_uses").contenido  # type: ignore[union-attr]
    intended_original = doc.metadata_modelo.intended_use

    TraductorDocumento(llm).traducir(doc, idioma_objetivo="bilingue")

    assert doc.seccion_por_id("2.1.model_uses").contenido == contenido_original  # type: ignore[union-attr]
    assert doc.metadata_modelo.intended_use == intended_original
    assert len(llm.llamadas) == 0


def test_modo_es_normalize_detecta_es_y_preserva_sin_traducir() -> None:
    """Si todo el contenido ya está en español, normalizar-ES no debe traducir."""
    # FakeLLM devuelve "es" para cada detección (5 detectores aprox.):
    # intended_use, use_restrictions, sección 2.1, apéndice contenido, apéndice título
    llm = FakeLLM(["es", "es", "es", "es", "es"])
    doc = _doc_seed()
    contenido_original = doc.seccion_por_id("2.1.model_uses").contenido  # type: ignore[union-attr]

    TraductorDocumento(llm).traducir(doc, idioma_objetivo="es_normalize")

    # El contenido no debe cambiar — el detector dijo que ya estaba en es
    assert doc.seccion_por_id("2.1.model_uses").contenido == contenido_original  # type: ignore[union-attr]
    # Todas las llamadas fueron de detección (tarea='extraction'), ninguna de traducción
    tareas = [tarea for tarea, _, _ in llm.llamadas]
    assert all(t == "extraction" for t in tareas)


def test_modo_es_normalize_traduce_secciones_en_ingles() -> None:
    """Si una sección está en inglés, normalizar-ES la traduce a español."""
    # Patrón de respuestas:
    # 1. detect intended_use → "en"
    # 2. translate intended_use → "Cálculo del VNB"
    # 3. detect use_restrictions → "es" (ya está en español)
    # 4. detect sección 2.1 → "es"
    # 5. detect apéndice contenido → "es"
    # 6. detect apéndice título → "es"
    llm = FakeLLM(["en", "Cálculo del VNB", "es", "es", "es", "es"])
    doc = _doc_seed()
    doc.metadata_modelo.intended_use = "Quarterly calculation of new business value"

    TraductorDocumento(llm).traducir(doc, idioma_objetivo="es_normalize")

    assert doc.metadata_modelo.intended_use == "Cálculo del VNB"


def test_modo_en_normalize_traduce_solo_secciones_en_espanol() -> None:
    """Modo en_normalize: si una sección ya está en inglés, NO la traduce."""
    # Patrón:
    # 1. detect intended_use → "en" (ya en inglés)
    # 2. detect use_restrictions → "es"
    # 3. translate use_restrictions → "For internal reporting only."
    # 4. detect sección 2.1 → "es"
    # 5. translate sección 2.1 → "The model calculates VNB quarterly."
    # 6. detect apéndice contenido → "en"
    # 7. detect apéndice título → "en"
    llm = FakeLLM(
        [
            "en",
            "es",
            "For internal reporting only.",
            "es",
            "The model calculates VNB quarterly.",
            "en",
            "en",
        ]
    )
    doc = _doc_seed()
    intended_original = "Quarterly NBV calculation"
    doc.metadata_modelo.intended_use = intended_original

    TraductorDocumento(llm).traducir(doc, idioma_objetivo="en_normalize")

    assert doc.metadata_modelo.intended_use == intended_original  # preservado
    assert doc.metadata_modelo.use_restrictions == "For internal reporting only."
    seccion = doc.seccion_por_id("2.1.model_uses")
    assert seccion is not None
    assert seccion.contenido == "The model calculates VNB quarterly."


def test_modo_normalize_si_detector_falla_traduce_de_todos_modos() -> None:
    """Si el detector LLM crashea, asumimos 'mixed' → traducir (no ocultar contenido).

    Patrón de respuestas: la primera (detect intended_use) lanza, sigue con resto.
    """
    from src.llm import LLMResponse

    class FlakyDetector:
        def __init__(self) -> None:
            self.llamadas = 0

        def chat(self, *, tarea: str, **_kwargs: object) -> LLMResponse:
            self.llamadas += 1
            if tarea == "extraction":
                raise RuntimeError("detector simulado caído")
            # Tarea 'chat' = traducción: respuesta válida
            return LLMResponse(
                text="(traducción)",
                modelo_usado="claude-sonnet-4-6",
                input_tokens=10,
                output_tokens=5,
                cache_read_tokens=0,
                cache_creation_tokens=0,
            )

    doc = _doc_seed()
    intended_original = doc.metadata_modelo.intended_use

    TraductorDocumento(FlakyDetector()).traducir(  # type: ignore[arg-type]
        doc, idioma_objetivo="en_normalize"
    )

    # Al fallar detector, asumió "mixed" → tradujo
    assert doc.metadata_modelo.intended_use != intended_original
    assert doc.metadata_modelo.intended_use == "(traducción)"


def test_modo_no_soportado_levanta_value_error() -> None:
    import pytest

    llm = FakeLLM([])
    doc = _doc_seed()

    with pytest.raises(ValueError, match="no soportado"):
        TraductorDocumento(llm).traducir(doc, idioma_objetivo="fr_normalize")  # type: ignore[arg-type]
