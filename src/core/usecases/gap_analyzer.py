"""GapAnalyzer: compara un Documento vs el template oficial y produce brechas.

Las brechas resultantes son las que la UI muestra como cards verde/amarillo/rojo
en el dashboard, y las que el InterviewEngine (Fase 2) usará para priorizar
qué preguntar al usuario.

Reglas de severidad:
- **Alta**: sección obligatoria que está vacía
- **Media**: sección obligatoria que está parcial (poco contenido) o que falta
  contenido crítico (supuestos, limitaciones)
- **Baja**: sección opcional vacía, o sección obligatoria completa pero con
  recomendaciones menores
"""

from __future__ import annotations

from src.core.models import Brecha, Documento, Seccion

# Secciones donde la falta de contenido es especialmente grave para MRM
# (capturan supuestos, limitaciones, riesgos — críticas para tier high-risk).
_SECCIONES_CRITICAS_MRM = frozenset(
    {
        "4.4.assumptions",
        "5.4.data_limitations",
        "6.4.limitations",
        "4.3.risk_drivers",
    }
)


def _brecha_obligatoria_vacia(seccion: Seccion) -> Brecha:
    es_critica = seccion.id in _SECCIONES_CRITICAS_MRM
    sugerencia = (
        "Sección crítica para MRM (captura supuestos/limitaciones/riesgos). "
        "Iniciar entrevista cuanto antes."
        if es_critica
        else "Iniciar entrevista para esta sección o editarla manualmente."
    )
    return Brecha(
        seccion_id=seccion.id,
        tipo="seccion_vacia",
        severidad="alta",
        mensaje=f"La sección '{seccion.numero} {seccion.nombre}' está vacía y es obligatoria.",
        sugerencia=sugerencia,
    )


def _brecha_obligatoria_parcial(seccion: Seccion) -> Brecha:
    return Brecha(
        seccion_id=seccion.id,
        tipo="seccion_incompleta",
        severidad="media",
        mensaje=(
            f"La sección '{seccion.numero} {seccion.nombre}' tiene contenido pero "
            "parece incompleta (poco texto)."
        ),
        sugerencia="Iniciar entrevista para enriquecer la sección.",
    )


def _brecha_opcional_vacia(seccion: Seccion) -> Brecha:
    return Brecha(
        seccion_id=seccion.id,
        tipo="seccion_vacia",
        severidad="baja",
        mensaje=(
            f"La sección opcional '{seccion.numero} {seccion.nombre}' no tiene "
            "contenido. Es recomendable completarla pero no es bloqueante."
        ),
        sugerencia="Considera si aplica a tu modelo; si sí, completarla mejora la calidad.",
    )


def _brecha_metadata_faltante(documento: Documento) -> Brecha | None:
    md = documento.metadata_modelo
    faltantes: list[str] = []
    campos_obligatorios_metadata = {
        "nombre_modelo": "Nombre del modelo",
        "model_owner": "Model Owner",
        "fae": "Functional Area Executive (FAE)",
        "intended_use": "Uso intencionado",
    }
    for attr, label in campos_obligatorios_metadata.items():
        if not getattr(md, attr):
            faltantes.append(label)
    if not faltantes:
        return None
    return Brecha(
        seccion_id="1.1.attributes",
        tipo="metadata_faltante",
        severidad="alta",
        mensaje=f"Faltan campos de metadata obligatorios: {', '.join(faltantes)}.",
        sugerencia="Completar la tabla de atributos del modelo (sección 1.1).",
    )


class GapAnalyzer:
    """Compara un Documento contra el catálogo y produce brechas accionables."""

    def analizar(self, documento: Documento) -> list[Brecha]:
        brechas: list[Brecha] = []

        meta_brecha = _brecha_metadata_faltante(documento)
        if meta_brecha is not None:
            brechas.append(meta_brecha)

        for seccion in documento.secciones:
            if seccion.obligatoria:
                if seccion.completitud == "vacia":
                    brechas.append(_brecha_obligatoria_vacia(seccion))
                elif seccion.completitud == "parcial":
                    brechas.append(_brecha_obligatoria_parcial(seccion))
                # 'completa' → no genera brecha
            else:
                if seccion.completitud == "vacia":
                    brechas.append(_brecha_opcional_vacia(seccion))

        # Orden: severidad alta primero, después media, después baja, y dentro
        # de cada nivel respetar orden numérico de sección.
        prioridad = {"alta": 0, "media": 1, "baja": 2}
        return sorted(brechas, key=lambda b: (prioridad[b.severidad], b.seccion_id))
