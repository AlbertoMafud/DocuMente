"""Use cases de transición de estado y registro de sign-off.

Estos use cases son la única vía para mover un documento entre estados del
ciclo de vida MRM. Toda transición pasa por `DocumentStateMachine` y queda
registrada en el audit_trail.

Diseñado para multi-user post-MVP: el `actor` ya viaja explícitamente como
parámetro; no hay supuestos de "default".
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from src.core.models import EventoAuditoria
from src.core.models.documento import EstadoDocumento
from src.core.rules.state_machine import DocumentStateMachine
from src.storage.repositories import DocumentoRepository

RolSignoff = Literal["reviewer", "fae"]


class TransicionRechazada(Exception):
    """La transición fue bloqueada por la state machine."""

    def __init__(self, razones: list[str]) -> None:
        self.razones = razones
        super().__init__("; ".join(razones))


class CambiarEstadoDocumento:
    """Use case: aplicar una transición de estado validada al documento."""

    def __init__(
        self,
        doc_repo: DocumentoRepository,
        state_machine: DocumentStateMachine | None = None,
    ) -> None:
        self.doc_repo = doc_repo
        self.state_machine = state_machine or DocumentStateMachine()

    def ejecutar(
        self,
        documento_id: UUID,
        *,
        destino: EstadoDocumento,
        actor: str,
    ) -> None:
        documento = self.doc_repo.obtener(documento_id)
        if documento is None:
            raise ValueError(f"Documento {documento_id} no encontrado.")

        resultado = self.state_machine.validar_transicion(documento, destino)
        if not resultado.permitida:
            raise TransicionRechazada(resultado.razones)

        origen = documento.estado
        documento.estado = destino
        documento.registrar_evento(
            EventoAuditoria(
                actor=actor,
                tipo="transicion_estado",
                descripcion=f"Estado cambiado de '{origen}' a '{destino}'.",
                metadata={"origen": origen, "destino": destino},
            )
        )
        self.doc_repo.guardar(documento)


class RegistrarSignoff:
    """Use case: el usuario afirma su rol (Reviewer o FAE) y firma."""

    def __init__(self, doc_repo: DocumentoRepository) -> None:
        self.doc_repo = doc_repo

    def ejecutar(
        self,
        documento_id: UUID,
        *,
        rol: RolSignoff,
        actor: str,
    ) -> None:
        documento = self.doc_repo.obtener(documento_id)
        if documento is None:
            raise ValueError(f"Documento {documento_id} no encontrado.")

        tipo = "signoff_reviewer" if rol == "reviewer" else "signoff_fae"
        descripcion = (
            f"Sign-off como {rol.upper()} registrado por '{actor}'."
            " Confirma independencia respecto a Owner y Developer del modelo."
        )
        documento.registrar_evento(
            EventoAuditoria(
                actor=actor,
                tipo=tipo,
                descripcion=descripcion,
                metadata={"rol": rol},
            )
        )
        self.doc_repo.guardar(documento)
