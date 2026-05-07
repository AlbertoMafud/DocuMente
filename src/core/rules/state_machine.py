"""DocumentStateMachine — reglas oficiales de transición de estado.

Fuente de verdad: `docs/MRM_REQUIREMENTS.md` §10 (transiciones permitidas)
y §12 (validaciones bloqueantes). Esta clase es lógica pura del dominio:
no depende de UI, BD ni LLM.

Estados (definidos en `Documento.EstadoDocumento`):
    draft → in_review → approved → published → retired

Política: cualquier intento de transición no listada se considera bloqueada.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.core.models import Documento
from src.core.models.documento import EstadoDocumento

# Mapa de transiciones permitidas (sin las validaciones extra todavía).
# Cualquier par no presente aquí está prohibido.
_TRANSICIONES_PERMITIDAS: dict[EstadoDocumento, set[EstadoDocumento]] = {
    "draft": {"in_review"},
    "in_review": {"approved", "draft"},
    "approved": {"published", "in_review"},
    "published": {"retired"},
    "retired": set(),
}


@dataclass(frozen=True)
class ResultadoTransicion:
    """Veredicto del state machine sobre una transición candidata."""

    permitida: bool
    razones: list[str] = field(default_factory=list)
    """Razones de bloqueo (o vacío si permitida). Listadas para mostrar al usuario."""


class DocumentStateMachine:
    """Decide si un Documento puede transicionar a un estado destino."""

    def validar_transicion(
        self,
        documento: Documento,
        destino: EstadoDocumento,
    ) -> ResultadoTransicion:
        """Devuelve si `documento.estado → destino` está permitida y por qué no si no."""
        razones: list[str] = []
        origen = documento.estado

        if origen == destino:
            razones.append("No se puede transicionar al mismo estado.")
            return ResultadoTransicion(permitida=False, razones=razones)

        if origen == "retired":
            razones.append("El documento está retirado y es inmutable.")
            return ResultadoTransicion(permitida=False, razones=razones)

        permitidos = _TRANSICIONES_PERMITIDAS.get(origen, set())
        if destino not in permitidos:
            razones.append(
                f"Transición no permitida: '{origen}' → '{destino}'. "
                f"Desde '{origen}' solo se permite: {sorted(permitidos) or 'ninguna'}."
            )
            return ResultadoTransicion(permitida=False, razones=razones)

        # Validaciones específicas por transición
        if origen == "draft" and destino == "in_review" and documento.porcentaje_resuelto < 1.0:
            faltantes = sum(
                1
                for s in documento.secciones_obligatorias
                if s.completitud not in ("completa", "omitida")
            )
            razones.append(
                f"{faltantes} sección(es) obligatoria(s) sin resolver. "
                "Cada una debe completarse u omitirse explícitamente con motivo."
            )

        if (
            origen == "in_review"
            and destino == "approved"
            and not _tiene_evento(documento, "signoff_reviewer")
        ):
            razones.append("Falta sign-off del Reviewer. Registra la firma antes de aprobar.")

        if (
            origen == "approved"
            and destino == "published"
            and not _tiene_evento(documento, "signoff_fae")
        ):
            razones.append("Falta sign-off del FAE. Registra la firma antes de publicar.")

        return ResultadoTransicion(permitida=not razones, razones=razones)


def _tiene_evento(documento: Documento, tipo: str) -> bool:
    """True si el audit_trail contiene al menos un evento del tipo dado."""
    return any(e.tipo == tipo for e in documento.audit_trail)
