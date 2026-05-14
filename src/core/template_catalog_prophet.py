from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.core.models.seccion import Seccion

TipoContenidoProphet = Literal["campos", "tabla", "texto"]


@dataclass(frozen=True)
class SeccionCatalogoProphet:
    id: str
    numero: str
    nombre: str
    obligatoria: bool
    intencion: str
    tipo_contenido: TipoContenidoProphet
    schema_tabla: tuple[str, ...] = field(default_factory=tuple)


TEMPLATE_PROPHET: tuple[SeccionCatalogoProphet, ...] = (
    SeccionCatalogoProphet(
        id="identificacion", numero="1", nombre="Identificación del modelo",
        obligatoria=True, tipo_contenido="campos",
        intencion="Datos básicos: nombre, área, proceso, encargado, frecuencia de uso, ruta del modelo, tiempo de ejecución.",
    ),
    SeccionCatalogoProphet(
        id="objetivo_alcance", numero="2", nombre="Objetivo y alcance",
        obligatoria=True, tipo_contenido="texto",
        intencion="Propósito del modelo, qué problema ataca y qué reportes alimenta (NBM, PM, IRR).",
    ),
    SeccionCatalogoProphet(
        id="responsables_roles", numero="3", nombre="Responsables y roles",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Quién opera, valida y aprueba el modelo.",
        schema_tabla=("persona", "rol", "area"),
    ),
    SeccionCatalogoProphet(
        id="corridas_runs", numero="4", nombre="Corridas (Runs)",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Detalle de cada corrida: número, descripción, ¿ALM?, tiempo ejecución, corrida precedente, outputs.",
        schema_tabla=("numero", "detalle", "es_alm", "tiempo_ejecucion", "corrida_precedente", "outputs_principales", "responsable"),
    ),
    SeccionCatalogoProphet(
        id="variables_criticas", numero="5", nombre="Variables críticas",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Variables críticas: nombre, descripción, fórmula, corrida, frecuencia, responsable, dependencias.",
        schema_tabla=("nombre", "descripcion", "formula", "corrida", "frecuencia_actualizacion", "responsable", "variables_dependientes"),
    ),
    SeccionCatalogoProphet(
        id="inputs_dependencias", numero="6", nombre="Inputs y dependencias",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Inputs externos: nombre, área proveedora, frecuencia, qué se actualiza.",
        schema_tabla=("input", "area_proveedora", "frecuencia", "que_se_actualiza"),
    ),
    SeccionCatalogoProphet(
        id="supuestos", numero="7", nombre="Supuestos relevantes",
        obligatoria=True, tipo_contenido="texto",
        intencion="Supuestos actuariales: mortalidad, lapsos, tasas, gastos, etc.",
    ),
    SeccionCatalogoProphet(
        id="outputs_reportes", numero="8", nombre="Outputs y reportes",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Outputs del modelo: output, reporte que alimenta, audiencia, frecuencia.",
        schema_tabla=("output", "reporte", "audiencia", "frecuencia"),
    ),
    SeccionCatalogoProphet(
        id="componentes_librerias", numero="9", nombre="Componentes y librerías Prophet",
        obligatoria=False, tipo_contenido="texto",
        intencion="Librerías Prophet (UL, Conventional, ALM) y otros componentes técnicos.",
    ),
    SeccionCatalogoProphet(
        id="historial_cambios", numero="10", nombre="Historial de cambios",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Cambios por periodo: periodo, descripción del cambio, responsable.",
        schema_tabla=("periodo", "cambio_realizado", "responsable"),
    ),
    SeccionCatalogoProphet(
        id="limitaciones_riesgos", numero="11", nombre="Limitaciones y riesgos",
        obligatoria=False, tipo_contenido="texto",
        intencion="Limitaciones conocidas, dependencias externas críticas y riesgos operacionales.",
    ),
    SeccionCatalogoProphet(
        id="matriz_conocimiento", numero="12", nombre="Matriz de conocimiento técnico",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Capacidades Prophet por persona con nivel (NO CONOCE/BÁSICO/INTERMEDIO/AVANZADO).",
        schema_tabla=("persona", "capacidad", "nivel"),
    ),
)


def por_id_prophet(seccion_id: str) -> SeccionCatalogoProphet | None:
    return next((s for s in TEMPLATE_PROPHET if s.id == seccion_id), None)


def construir_secciones_vacias_prophet() -> list[Seccion]:
    return [
        Seccion(
            id=s.id, nombre=s.nombre, numero=s.numero,
            obligatoria=s.obligatoria, intencion=s.intencion,
        )
        for s in TEMPLATE_PROPHET
    ]
