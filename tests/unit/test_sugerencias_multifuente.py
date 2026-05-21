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

        async def chat_async(self, **_kwargs: object) -> object:
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


# ===== Tests de paralelización (S17.A) =====


def _doc_con_n_secciones_vacias(n: int) -> Documento:
    """Crea un Documento con N secciones vacías para benchmark."""
    return Documento(
        metadata_modelo=MetadataModelo(nombre_modelo="Bench"),
        secciones=[
            Seccion(
                id=f"sec.{i}",
                nombre=f"Sección {i}",
                numero=f"1.{i}",
                obligatoria=True,
                contenido=None,
                completitud="vacia",
                intencion=f"Descripción {i}",
            )
            for i in range(n)
        ],
    )


def test_paralelizacion_reduce_wall_clock_vs_secuencial() -> None:
    """Con LLM que tarda 0.5s por llamada, 10 secciones en paralelo deben
    completar en < 3s (no en 5s como serían secuenciales).

    Este test demuestra el ROI principal de S17.A: paralelización real.
    """
    import asyncio
    import time

    from src.llm import LLMResponse

    class SlowLLM:
        """LLM falso que tarda 0.5s por llamada — simula latencia real."""

        def __init__(self) -> None:
            self.llamadas = 0

        def chat(self, **_kwargs: object) -> LLMResponse:
            raise RuntimeError("usar chat_async en este test")

        async def chat_async(self, **_kwargs: object) -> LLMResponse:
            self.llamadas += 1
            await asyncio.sleep(0.5)
            return LLMResponse(
                text="Borrador generado.",
                modelo_usado="claude-sonnet-4-6",
                input_tokens=100,
                output_tokens=50,
                cache_read_tokens=0,
                cache_creation_tokens=0,
            )

    doc = _doc_con_n_secciones_vacias(10)
    fuentes = [_fuente("notas.txt", "texto fuente")]
    llm = SlowLLM()

    inicio = time.perf_counter()
    resultado = SugerenciasMultiFuente(llm).ejecutar(  # type: ignore[arg-type]
        doc, fuentes, concurrencia=5
    )
    duracion = time.perf_counter() - inicio

    # 10 llamadas a 0.5s c/u en serie = 5s. En paralelo con 5 simultáneas
    # = ~1s (2 batches de 5). Damos holgura para overhead de asyncio.
    assert resultado.secciones_pobladas == 10
    assert resultado.secciones_intentadas == 10
    assert llm.llamadas == 10
    assert duracion < 2.5, (
        f"Paralelización falló: 10 secciones tardaron {duracion:.2f}s "
        f"(esperado < 2.5s con concurrencia=5; sería ~5s secuencial)"
    )


def test_concurrencia_limita_paralelas_simultaneas() -> None:
    """El Semaphore(N) garantiza que NO se hacen más de N llamadas a la vez.

    Mide el máximo de llamadas activas simultáneamente — si concurrencia=3,
    nunca debe haber 4 en vuelo.
    """
    import asyncio

    from src.llm import LLMResponse

    class CountingLLM:
        def __init__(self) -> None:
            self.en_vuelo = 0
            self.max_en_vuelo = 0
            self._lock = asyncio.Lock()

        def chat(self, **_kwargs: object) -> LLMResponse:
            raise RuntimeError("usar async")

        async def chat_async(self, **_kwargs: object) -> LLMResponse:
            async with self._lock:
                self.en_vuelo += 1
                self.max_en_vuelo = max(self.max_en_vuelo, self.en_vuelo)
            try:
                await asyncio.sleep(0.1)
                return LLMResponse(
                    text="ok",
                    modelo_usado="claude-sonnet-4-6",
                    input_tokens=10,
                    output_tokens=5,
                    cache_read_tokens=0,
                    cache_creation_tokens=0,
                )
            finally:
                async with self._lock:
                    self.en_vuelo -= 1

    doc = _doc_con_n_secciones_vacias(10)
    fuentes = [_fuente("notas.txt", "x")]
    llm = CountingLLM()

    SugerenciasMultiFuente(llm).ejecutar(  # type: ignore[arg-type]
        doc, fuentes, concurrencia=3
    )

    assert llm.max_en_vuelo <= 3, (
        f"Semaphore no respetado: hubo {llm.max_en_vuelo} llamadas simultáneas (esperado ≤ 3)"
    )
    assert llm.max_en_vuelo >= 2, (
        "Si max_en_vuelo es 1, no hubo paralelismo real — probablemente el código sigue secuencial"
    )


def test_callback_progress_se_invoca_por_cada_seccion() -> None:
    """El callback on_progress debe llamarse exactamente N veces
    (una por sección procesada), con la información correcta."""
    import asyncio

    from src.core.usecases.sugerencias_multifuente import EventoProgreso
    from src.llm import LLMResponse

    class FastLLM:
        async def chat_async(self, **_kwargs: object) -> LLMResponse:
            return LLMResponse(
                text="Borrador.",
                modelo_usado="claude-sonnet-4-6",
                input_tokens=10,
                output_tokens=5,
                cache_read_tokens=0,
                cache_creation_tokens=0,
            )

        def chat(self, **_kwargs: object) -> LLMResponse:
            raise RuntimeError("usar async")

    doc = _doc_con_n_secciones_vacias(5)
    fuentes = [_fuente("notas.txt", "x")]
    eventos: list[EventoProgreso] = []

    async def capturar(e: EventoProgreso) -> None:
        eventos.append(e)

    asyncio.run(
        SugerenciasMultiFuente(FastLLM()).ejecutar_async(  # type: ignore[arg-type]
            doc, fuentes, on_progress=capturar, concurrencia=2
        )
    )

    assert len(eventos) == 5
    # Cada evento debe traer total=5 y completadas debe ser monotónico 1..5
    completadas = sorted(e.completadas for e in eventos)
    assert completadas == [1, 2, 3, 4, 5]
    assert all(e.total == 5 for e in eventos)
    assert all(e.estado == "poblada" for e in eventos)
