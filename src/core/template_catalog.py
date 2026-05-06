"""Catálogo del template oficial NYL Model Development.

Esta es la **representación en código** de las 32 secciones definidas en
`docs/TEMPLATE_MODEL_DEV.md`. Es la fuente que consume `DocxReader` para
mapear contenido extraído a IDs de sección, y `GapAnalyzer` para evaluar
completitud contra el estándar.

Cualquier cambio al template oficial (`SMNYL/Templates/NYL Model Development
Template.docx`) debe reflejarse aquí Y en `docs/TEMPLATE_MODEL_DEV.md`
manteniéndolos sincronizados.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SeccionCatalogo:
    """Definición canónica de una sección del template oficial."""

    id: str
    numero: str
    nombre: str
    obligatoria: bool
    intencion: str
    aliases: tuple[str, ...] = field(default_factory=tuple)
    """Variantes de nombre que el reader debe reconocer (sinónimos comunes)."""
    preguntas_guia: tuple[str, ...] = field(default_factory=tuple)


# Secciones del NYL Model Development Template — orden y obligatoriedad
# extraídos verbatim de docs/TEMPLATE_MODEL_DEV.md.
TEMPLATE_MODEL_DEVELOPMENT: tuple[SeccionCatalogo, ...] = (
    SeccionCatalogo(
        id="1.3.problem_statement",
        numero="1.3",
        nombre="Problem Statement",
        obligatoria=True,
        intencion=(
            "Descripción de alto nivel del problema o necesidad que el modelo "
            "resuelve, incluyendo restricciones informacionales, computacionales "
            "o analíticas bajo las que se desarrolló."
        ),
        aliases=(
            "problem",
            "problema",
            "1. problem statement",
            "objetivo",
            "objetivo del modelo",
            "propósito",
        ),
        preguntas_guia=(
            "¿Cuál es el problema o necesidad que este modelo resuelve?",
            "¿Existe un modelo previo? ¿Por qué fue insuficiente?",
            "¿Hay restricciones (plataforma, regulatorias, computacionales) bajo las que tuvo que diseñarse?",
            "¿Cuáles son los productos o líneas de negocio que cubre?",
        ),
    ),
    SeccionCatalogo(
        id="2.1.model_uses",
        numero="2.1",
        nombre="Model Uses",
        obligatoria=True,
        intencion="Descripción de todos los usuarios intencionados y frecuencia de uso.",
        aliases=("uses", "usos", "2.1 model uses"),
        preguntas_guia=(
            "¿Quiénes son los usuarios intencionados del modelo?",
            "¿Con qué frecuencia se usa? (diaria, mensual, trimestral, ad-hoc)",
            "¿Qué usos están explícitamente fuera del alcance?",
        ),
    ),
    SeccionCatalogo(
        id="2.2.model_scope",
        numero="2.2",
        nombre="Model Scope",
        obligatoria=True,
        intencion="Productos modelados, descripciones de alto y bajo nivel.",
        aliases=("scope", "alcance", "2.2 model scope", "ámbito de aplicación"),
        preguntas_guia=(
            "¿Qué productos cubre el modelo? Lista enumerada.",
            "Para cada producto: ¿qué features modela y cuáles deja fuera? ¿por qué?",
            "¿Cuál es el tamaño de cada bloque (reservas, número de pólizas, montos)?",
        ),
    ),
    SeccionCatalogo(
        id="2.3.business_impact",
        numero="2.3",
        nombre="Business Impact of Model Usage",
        obligatoria=True,
        intencion="Cómo el modelo encaja en el negocio y cómo se usan sus resultados.",
        aliases=("business impact", "impacto", "2.3 business impact"),
        preguntas_guia=(
            "¿Cómo encaja este modelo en las decisiones del negocio?",
            "¿Sus resultados son requeridos por alguna regulación? ¿Cuál?",
        ),
    ),
    SeccionCatalogo(
        id="3.1.ancillary",
        numero="3.1",
        nombre="Ancillary document list",
        obligatoria=True,
        intencion="Lista de documentos relacionados con ubicaciones.",
        aliases=(
            "ancillary",
            "documentos auxiliares",
            "3.1 ancillary",
            "enlace con documentos relacionados",
            "documentos relacionados",
        ),
    ),
    SeccionCatalogo(
        id="3.2.additional",
        numero="3.2",
        nombre="Additional Documents",
        obligatoria=False,
        intencion="Lista de documentación adicional relacionada.",
        aliases=("additional documents", "3.2 additional"),
    ),
    SeccionCatalogo(
        id="4.1.diagram",
        numero="4.1",
        nombre="Schematic Diagram",
        obligatoria=True,
        intencion="Diagrama del sistema de modelado: data sources, modelos upstream, outputs, plataforma.",
        aliases=("diagram", "diagrama", "4.1 schematic"),
    ),
    SeccionCatalogo(
        id="4.2.theory",
        numero="4.2",
        nombre="Model Theory and Logic",
        obligatoria=True,
        intencion="Algoritmo central, lógica y enfoques alternativos considerados.",
        aliases=("theory", "logic", "teoría", "4.2 model theory"),
        preguntas_guia=(
            "¿Cuál es el algoritmo o teoría central del modelo?",
            "¿Está construido sobre una plataforma existente? ¿Qué lógica adicional añadiste?",
            "¿Qué enfoques alternativos consideraste y por qué no los elegiste?",
        ),
    ),
    SeccionCatalogo(
        id="4.3.risk_drivers",
        numero="4.3",
        nombre="Key Risk Drivers",
        obligatoria=True,
        intencion="Lista y contexto de los principales drivers de riesgo del modelo.",
        aliases=("risk drivers", "drivers de riesgo", "4.3 key risk"),
        preguntas_guia=(
            "¿Cuáles son los 3-5 drivers principales de riesgo del modelo?",
            "Para cada uno: ¿por qué es relevante y cómo está modelado?",
        ),
    ),
    SeccionCatalogo(
        id="4.4.assumptions",
        numero="4.4",
        nombre="Key Assumptions",
        obligatoria=True,
        intencion="Todos los supuestos económicos o de seguros, con fuentes y enfoques de modelado.",
        aliases=("assumptions", "supuestos", "4.4 key assumptions"),
        preguntas_guia=(
            "Para cada supuesto: ¿qué fuente lo respalda? ¿qué documento/study?",
            "¿Cuáles son los rangos plausibles de cada supuesto?",
            "¿Hay supuestos que se sospecha pueden necesitar revisión?",
        ),
    ),
    SeccionCatalogo(
        id="5.1.raw_data",
        numero="5.1",
        nombre="Raw Data Sources and Data Quality",
        obligatoria=True,
        intencion="Lista de proveedores y ubicación de specs finales para data raw.",
        aliases=("raw data", "datos crudos", "5.1 raw data"),
    ),
    SeccionCatalogo(
        id="5.2.upstream",
        numero="5.2",
        nombre="Upstream Models & Company Determined Assumptions",
        obligatoria=True,
        intencion="Lista de modelos upstream y supuestos determinados por la empresa.",
        aliases=("upstream", "modelos upstream", "5.2 upstream"),
    ),
    SeccionCatalogo(
        id="5.3.1.aggregations",
        numero="5.3.1",
        nombre="Data Aggregations",
        obligatoria=False,
        intencion="Información sobre agregación de datos (si aplica).",
        aliases=("aggregations", "agregaciones", "5.3.1"),
    ),
    SeccionCatalogo(
        id="5.3.2.segmentations",
        numero="5.3.2",
        nombre="Segmentations",
        obligatoria=False,
        intencion="Información sobre segmentación relevante (si aplica).",
        aliases=("segmentations", "segmentaciones", "5.3.2"),
    ),
    SeccionCatalogo(
        id="5.3.3.averages_proxies",
        numero="5.3.3",
        nombre="Use of Averages or Proxies",
        obligatoria=False,
        intencion="Identificar dónde se usan promedios o proxies.",
        aliases=("averages", "proxies", "5.3.3"),
    ),
    SeccionCatalogo(
        id="5.4.data_limitations",
        numero="5.4",
        nombre="Known Input and Data Limitations",
        obligatoria=True,
        intencion="Lista de limitaciones encontradas en datos o supuestos y acciones tomadas.",
        aliases=("data limitations", "limitaciones de datos", "5.4 known"),
    ),
    SeccionCatalogo(
        id="5.5.input_changes",
        numero="5.5",
        nombre="Record of Input Changes or Decisions Made",
        obligatoria=False,
        intencion="Bitácora viva de cambios de input y decisiones.",
        aliases=("input changes", "5.5 record"),
    ),
    SeccionCatalogo(
        id="6.1.specification",
        numero="6.1",
        nombre="Specification Process",
        obligatoria=True,
        intencion="Proceso de especificación del modelo (cambio o construcción nueva).",
        aliases=("specification", "especificación", "6.1 specification"),
    ),
    SeccionCatalogo(
        id="6.2.approach",
        numero="6.2",
        nombre="Approach Used",
        obligatoria=True,
        intencion="Metodología detallada del modelo finalmente seleccionado.",
        aliases=("approach", "enfoque", "6.2 approach", "procedimiento", "metodología"),
    ),
    SeccionCatalogo(
        id="6.3.dev_testing",
        numero="6.3",
        nombre="Development Testing",
        obligatoria=True,
        intencion="Tests realizados para evaluar componentes y funcionamiento general.",
        aliases=("development testing", "testing de desarrollo", "6.3 development"),
    ),
    SeccionCatalogo(
        id="6.4.limitations",
        numero="6.4",
        nombre="Limitations Revealed During Testing",
        obligatoria=True,
        intencion="Limitaciones del modelo descubiertas durante testing.",
        aliases=("limitations testing", "6.4 limitations"),
    ),
    SeccionCatalogo(
        id="6.5.process_changes",
        numero="6.5",
        nombre="Record of Process Changes",
        obligatoria=False,
        intencion="Bitácora viva de cambios de proceso durante el build.",
        aliases=("process changes", "6.5 record"),
    ),
    SeccionCatalogo(
        id="7.1.platform",
        numero="7.1",
        nombre="Platform",
        obligatoria=True,
        intencion="Plataforma donde corre el modelo y cómo se integra.",
        aliases=("platform", "plataforma", "7.1 platform"),
    ),
    SeccionCatalogo(
        id="7.2.runs",
        numero="7.2",
        nombre="Model Runs",
        obligatoria=True,
        intencion="Instrucciones de ejecución por use case y settings de control.",
        aliases=("model runs", "runs", "7.2 model runs"),
    ),
    SeccionCatalogo(
        id="7.3.perf_testing",
        numero="7.3",
        nombre="Performance Testing",
        obligatoria=True,
        intencion="Testing para asegurar que el modelo refleja correctamente las specs.",
        aliases=("performance testing", "7.3 performance"),
    ),
    SeccionCatalogo(
        id="7.4.prod_limitations",
        numero="7.4",
        nombre="Production and Performance Limitations",
        obligatoria=True,
        intencion="Limitaciones por la implementación en producción.",
        aliases=("production limitations", "7.4 production"),
    ),
    SeccionCatalogo(
        id="8.governance",
        numero="8",
        nombre="Model Governance",
        obligatoria=True,
        intencion="Gobernanza de software, datos, controles, signoff, escalación.",
        aliases=("governance", "gobernanza", "8 model governance"),
    ),
    SeccionCatalogo(
        id="9.monitoring",
        numero="9",
        nombre="On-going Monitoring",
        obligatoria=True,
        intencion="Procedimientos de monitoreo de performance del modelo.",
        aliases=(
            "monitoring",
            "monitoreo",
            "9 on-going",
            "frecuencia de la revisión",
            "frecuencia de revisión",
        ),
    ),
)


def por_id(seccion_id: str) -> SeccionCatalogo | None:
    """Devuelve la entrada del catálogo por ID, o None."""
    return next((s for s in TEMPLATE_MODEL_DEVELOPMENT if s.id == seccion_id), None)
