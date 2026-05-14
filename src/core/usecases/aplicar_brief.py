"""Use case AplicarBrief — convierte respuestas del Brief Inicial en borradores
de las secciones de mayor valor del template NYL.

El Brief Inicial es un cuestionario opcional de 10 preguntas de alto impacto
que el usuario contesta una sola vez al crear un documento. Cada respuesta
se mapea a una sección del template y se convierte en borrador vía LLM.

Esto reduce drásticamente la fricción de la entrevista — el usuario entra al
dashboard con 6+ secciones ya pre-pobladas en lugar de en blanco.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Final

from anthropic.types import MessageParam, TextBlockParam

from src.core.models import Documento
from src.core.usecases.strings_localizados import Idioma, t
from src.llm import LLMClient
from src.llm.pricing import construir_llamada
from src.llm.prompts.brief_a_seccion import BRIEF_A_SECCION_SYSTEM, construir_prompt_brief


@dataclass(frozen=True)
class PreguntaBrief:
    """Una pregunta del brief + la sección destino."""

    numero: int
    texto: str
    placeholder: str
    seccion_id: str


# Preset fijo de 10 preguntas (no varía por tier — son las de mayor impacto).
PREGUNTAS_BRIEF: Final[tuple[PreguntaBrief, ...]] = (
    PreguntaBrief(
        numero=1,
        texto="¿Cuál es el propósito principal del modelo? ¿Qué decisión apoya?",
        placeholder=(
            "Ej. Estima el valor de nuevo negocio (VNB) trimestralmente para "
            "apoyar las decisiones de pricing y la asignación de capital de los "
            "productos individuales."
        ),
        seccion_id="1.3.problem_statement",
    ),
    PreguntaBrief(
        numero=2,
        texto="¿Quién usa los outputs del modelo y para qué?",
        placeholder=(
            "Ej. Pricing → ajusta tarifas. Finanzas → calcula VNB para reporting "
            "trimestral. ALM → input de proyecciones."
        ),
        seccion_id="2.1.model_uses",
    ),
    PreguntaBrief(
        numero=3,
        texto="¿Qué incluye y qué NO incluye el modelo (alcance)?",
        placeholder=(
            "Ej. Cubre productos individuales UL y tradicionales en pesos. NO "
            "cubre grupo, microseguros, ni productos descontinuados."
        ),
        seccion_id="2.2.model_scope",
    ),
    PreguntaBrief(
        numero=4,
        texto="¿Cuál es el impacto al negocio si el modelo falla o se atrasa?",
        placeholder=(
            "Ej. Sin VNB, no se cierra el reporte trimestral; bloquea decisiones "
            "del comité de pricing; afecta attestation MRM."
        ),
        seccion_id="2.3.business_impact",
    ),
    PreguntaBrief(
        numero=5,
        texto="¿Qué metodología/algoritmo central usa el modelo?",
        placeholder=(
            "Ej. Proyección actuarial determinista con escenarios económicos del "
            "ESG corporativo; descuento por tasa de cartera; mortalidad SOA 2017."
        ),
        seccion_id="4.2.theory",
    ),
    PreguntaBrief(
        numero=6,
        texto="¿Cuáles son los principales riesgos técnicos o metodológicos?",
        placeholder=(
            "Ej. Sensibilidad alta a curvas de tasa; dependencia de calibración "
            "anual de lapse; supuestos de mortalidad fuera de la experiencia."
        ),
        seccion_id="4.3.risk_drivers",
    ),
    PreguntaBrief(
        numero=7,
        texto="Top 5 supuestos clave del modelo (cuantitativos o cualitativos).",
        placeholder=(
            "Ej. Tabla SOA 2017 ajustada por factor 0.85; lapse base 8% anual; "
            "tasa de inversión 7.5%; ESG escenario base; mix de productos del BP."
        ),
        seccion_id="4.4.assumptions",
    ),
    PreguntaBrief(
        numero=8,
        texto="Top 3 fuentes de datos (sistema o área que las provee).",
        placeholder=("Ej. SOFIA (model points); Inversiones (tasas y ESG); BP (ventas)."),
        seccion_id="5.1.raw_data",
    ),
    PreguntaBrief(
        numero=9,
        texto="¿Cuáles son las limitaciones conocidas en producción?",
        placeholder=(
            "Ej. No soporta productos en USD; tiempo de corrida 40 min limita "
            "ad-hoc; calibración manual de lapse cada cierre."
        ),
        seccion_id="7.4.prod_limitations",
    ),
    PreguntaBrief(
        numero=10,
        texto="¿Cómo se monitorea su performance hoy?",
        placeholder=(
            "Ej. Comparación trimestral output vs realizado; revisión de "
            "sensibilidades; attestation anual de MRM."
        ),
        seccion_id="9.monitoring",
    ),
)


class AplicarBrief:
    """Use case: convierte respuestas del Brief Inicial en borradores de sección."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def ejecutar(
        self,
        documento: Documento,
        respuestas: dict[int, str],
        *,
        idioma: Idioma = "es",
    ) -> int:
        """Genera borradores para cada respuesta no vacía y devuelve cuántas se aplicaron.

        Args:
            documento: documento donde escribir los borradores (in-place).
            respuestas: dict `{numero_pregunta: respuesta}` (1-10).
            idioma: idioma del prefijo "[Borrador — revisar]".
        """
        prefijo = t("borrador_revisar", idioma)
        aplicadas = 0

        for pregunta in PREGUNTAS_BRIEF:
            respuesta = respuestas.get(pregunta.numero, "")
            if not respuesta or not respuesta.strip():
                continue

            seccion = documento.seccion_por_id(pregunta.seccion_id)
            if seccion is None:
                continue
            # No pisar contenido existente (importar puede traer secciones llenas)
            if seccion.completitud not in ("vacia",):
                continue

            with contextlib.suppress(Exception):
                draft = self._convertir(
                    documento,
                    seccion_nombre=seccion.nombre,
                    seccion_intencion=seccion.intencion or seccion.nombre,
                    pregunta=pregunta.texto,
                    respuesta=respuesta.strip(),
                )
                if draft:
                    seccion.contenido = f"{prefijo}\n\n{draft.strip()}"
                    seccion.completitud = "parcial"
                    aplicadas += 1

        return aplicadas

    def _convertir(
        self,
        documento: Documento,
        *,
        seccion_nombre: str,
        seccion_intencion: str,
        pregunta: str,
        respuesta: str,
    ) -> str:
        system_blocks: list[TextBlockParam] = [{"type": "text", "text": BRIEF_A_SECCION_SYSTEM}]
        user_msg = construir_prompt_brief(
            seccion_nombre=seccion_nombre,
            seccion_intencion=seccion_intencion,
            pregunta=pregunta,
            respuesta_usuario=respuesta,
        )
        messages: list[MessageParam] = [{"role": "user", "content": user_msg}]

        respuesta_llm = self.llm.chat(
            tarea="chat",
            system_blocks=system_blocks,
            messages=messages,
            max_tokens=1024,
        )
        documento.metricas_uso.agregar(
            construir_llamada(
                modelo=respuesta_llm.modelo_usado,
                tarea="chat",
                input_tokens=respuesta_llm.input_tokens,
                output_tokens=respuesta_llm.output_tokens,
                cache_read_tokens=respuesta_llm.cache_read_tokens,
                cache_creation_tokens=respuesta_llm.cache_creation_tokens,
            )
        )
        return respuesta_llm.text.strip()
