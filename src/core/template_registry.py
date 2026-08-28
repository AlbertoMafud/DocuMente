"""Registro de templates — resolución unificada de tipos de documento.

Pieza central de integración del Template Studio (spec §7): todo consumidor
(crear documento, entrevista, gap analyzer, export, importación) resuelve el
tipo de documento aquí en lugar de hacer `if tipo == "prophet"`.

Dos orígenes de templates:
- **"codigo"** — los catálogos congelados (`model_development`, `prophet`).
  Sus archivos `template_catalog*.py` NO se tocan: el registro los envuelve
  al vuelo convirtiéndolos a `SeccionCatalogoDinamica` (superset de ambos).
- **"dinamico"** — creados en el Template Studio, persistidos en BD con
  estado `publicado`. Se cargan bajo demanda vía el repositorio.

Nota de capas: la resolución de dinámicos importa el repositorio DENTRO de
la función (mismo patrón que los use cases, que ya dependen de storage).
Los templates de código se resuelven sin tocar BD.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.core.models.seccion import Seccion
from src.core.models.template_dinamico import SeccionCatalogoDinamica, TemplateDinamico
from src.core.template_catalog import TEMPLATE_MODEL_DEVELOPMENT
from src.core.template_catalog_prophet import TEMPLATE_PROPHET

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "docs" / "templates"

TIPOS_CODIGO = ("model_development", "prophet")


class TemplateDesconocidoError(KeyError):
    """El tipo solicitado no existe ni en código ni publicado en BD."""


@dataclass(frozen=True)
class ReglasCompletitud:
    """Umbrales del gap analyzer por template.

    v1: los defaults replican las heurísticas actuales — un template dinámico
    se comporta igual que los congelados. Personalización por template queda
    explícitamente fuera de v1 (spec §13).
    """

    chars_completa: int = 200
    chars_parcial: int = 1


@dataclass(frozen=True)
class TemplateSpec:
    """La 'receta' resuelta de un tipo de documento."""

    id: str
    nombre: str
    version: int
    origen: str  # "codigo" | "dinamico"
    catalogo: tuple[SeccionCatalogoDinamica, ...]
    ruta_plantilla_word: Path | None
    writer: str  # "mrm" | "prophet" | "generico"
    reglas_completitud: ReglasCompletitud = field(default_factory=ReglasCompletitud)


def _spec_mrm() -> TemplateSpec:
    catalogo = tuple(
        SeccionCatalogoDinamica(
            id=s.id,
            numero=s.numero,
            nombre=s.nombre,
            obligatoria=s.obligatoria,
            intencion=s.intencion,
            tipo_contenido="texto",
            aliases=list(s.aliases),
            preguntas_guia=list(s.preguntas_guia),
        )
        for s in TEMPLATE_MODEL_DEVELOPMENT
    )
    return TemplateSpec(
        id="model_development",
        nombre="Model Development (MRM)",
        version=1,
        origen="codigo",
        catalogo=catalogo,
        ruta_plantilla_word=_TEMPLATES_DIR / "model_development_smnyl.docx",
        writer="mrm",
    )


def _spec_prophet() -> TemplateSpec:
    catalogo = tuple(
        SeccionCatalogoDinamica(
            id=s.id,
            numero=s.numero,
            nombre=s.nombre,
            obligatoria=s.obligatoria,
            intencion=s.intencion,
            tipo_contenido=s.tipo_contenido,
            schema_tabla=list(s.schema_tabla),
        )
        for s in TEMPLATE_PROPHET
    )
    return TemplateSpec(
        id="prophet",
        nombre="Ficha Prophet (Modelos Actuariales)",
        version=1,
        origen="codigo",
        catalogo=catalogo,
        ruta_plantilla_word=_TEMPLATES_DIR / "prophet_model_doc_smnyl.docx",
        writer="prophet",
    )


def _spec_desde_dinamico(template: TemplateDinamico) -> TemplateSpec:
    return TemplateSpec(
        id=template.slug,
        nombre=template.nombre,
        version=template.version,
        origen="dinamico",
        catalogo=tuple(template.secciones),
        # v1: los dinámicos exportan con el writer genérico institucional.
        ruta_plantilla_word=None,
        writer="generico",
    )


def resolver_template(tipo: str) -> TemplateSpec:
    """Devuelve el `TemplateSpec` del tipo dado.

    Orden de resolución: templates de código primero (congelados, sin BD),
    luego dinámicos publicados en BD.

    Raises:
        TemplateDesconocidoError: si el tipo no existe en ningún origen.
    """
    if tipo == "model_development":
        return _spec_mrm()
    if tipo == "prophet":
        return _spec_prophet()

    from src.storage.repositories import TemplateDinamicoRepository

    template = TemplateDinamicoRepository().obtener_publicado_por_slug(tipo)
    if template is None:
        raise TemplateDesconocidoError(
            f"Tipo de documento '{tipo}' no registrado (ni en código ni publicado)."
        )
    return _spec_desde_dinamico(template)


def listar_templates(*, incluir_dinamicos: bool = True) -> list[TemplateSpec]:
    """Lista los templates disponibles para crear documentos."""
    specs = [_spec_mrm(), _spec_prophet()]
    if incluir_dinamicos:
        from src.storage.repositories import TemplateDinamicoRepository

        specs.extend(
            _spec_desde_dinamico(t) for t in TemplateDinamicoRepository().listar(estado="publicado")
        )
    return specs


def construir_secciones_desde_spec(spec: TemplateSpec) -> list[Seccion]:
    """Construye las `Seccion` vacías de un documento nuevo del tipo dado.

    Mismo contrato que `construir_secciones_vacias()` (MRM) y su gemela
    Prophet: cada llamada devuelve secciones independientes. El documento
    COPIA su estructura al nacer — por eso retirar un template no rompe
    documentos existentes (spec §5).
    """
    return [
        Seccion(
            id=s.id,
            nombre=s.nombre,
            numero=s.numero,
            obligatoria=s.obligatoria,
            intencion=s.intencion,
            preguntas_guia=list(s.preguntas_guia),
        )
        for s in spec.catalogo
    ]
