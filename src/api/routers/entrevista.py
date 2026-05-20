"""Router: entrevista LLM por sección.

Endpoints:
- POST   /documentos/{id}/entrevista/{sid}/iniciar       — IniciarEntrevista
- POST   /documentos/{id}/entrevista/{sid}/responder     — ResponderPregunta
- GET    /documentos/{id}/entrevista/{sid}/estado        — leer estado actual
- DELETE /documentos/{id}/entrevista/{sid}               — descartar entrevista en curso
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.api.auth import CurrentUser
from src.api.deps import DocRepoDep, EntrevistaRepoDep, LlmClientDep
from src.api.errors import not_found
from src.api.schemas import (
    IniciarEntrevistaResponse,
    OkResponse,
    ResponderPreguntaRequest,
    TurnoEntrevistaDTO,
)
from src.api.schemas.entrevista import MensajeDTO
from src.core.usecases import (
    Drafter,
    IniciarEntrevista,
    InterviewEngine,
    KnowledgeExtractor,
    ResponderPregunta,
    TurnoEntrevista,
)

router = APIRouter(
    prefix="/documentos/{documento_id}/entrevista/{seccion_id}",
    tags=["entrevista"],
)


def _turno_dto(turno: TurnoEntrevista) -> TurnoEntrevistaDTO:
    return TurnoEntrevistaDTO(
        respuesta_asistente=turno.respuesta_claude,
        seccion_cerrada=turno.seccion_cerrada,
        borrador=turno.borrador,
        n_mensajes=len(turno.estado.mensajes),
    )


def _ensure_llm(llm) -> None:  # type: ignore[no-untyped-def]
    if llm is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Entrevista requiere LLM configurado. "
                "Define ANTHROPIC_API_KEY en .env."
            ),
        )


@router.post("/iniciar", response_model=IniciarEntrevistaResponse)
def iniciar_entrevista(
    documento_id: UUID,
    seccion_id: str,
    doc_repo: DocRepoDep,
    entrevista_repo: EntrevistaRepoDep,
    llm: LlmClientDep,
    user: CurrentUser,
) -> IniciarEntrevistaResponse:
    """Arranca o reanuda una entrevista sobre la sección.

    Si ya había un estado en progreso, lo retoma sin perder mensajes.
    """
    _ensure_llm(llm)
    assert llm is not None  # type-narrow para mypy
    engine = InterviewEngine(llm)
    uc = IniciarEntrevista(engine, doc_repo, entrevista_repo)
    turno = uc.ejecutar(documento_id, seccion_id)
    return IniciarEntrevistaResponse(
        turno=_turno_dto(turno),
        seccion_id=seccion_id,
        mensajes=[MensajeDTO.from_domain(m) for m in turno.estado.mensajes],
    )


@router.post("/responder", response_model=TurnoEntrevistaDTO)
def responder_pregunta(
    documento_id: UUID,
    seccion_id: str,
    payload: ResponderPreguntaRequest,
    doc_repo: DocRepoDep,
    entrevista_repo: EntrevistaRepoDep,
    llm: LlmClientDep,
    user: CurrentUser,
) -> TurnoEntrevistaDTO:
    """Procesa el turno del usuario: dispara LLM, persiste estado.

    Si el motor marca la sección como cerrada y el Drafter produce un
    borrador suficiente, devuelve el `borrador` en el response.
    """
    _ensure_llm(llm)
    assert llm is not None
    engine = InterviewEngine(llm)
    drafter = Drafter(llm)
    extractor = KnowledgeExtractor(llm)
    uc = ResponderPregunta(engine, drafter, doc_repo, entrevista_repo, extractor)
    turno = uc.ejecutar(documento_id, seccion_id, payload.respuesta)
    return _turno_dto(turno)


@router.get("/estado", response_model=IniciarEntrevistaResponse)
def obtener_estado(
    documento_id: UUID,
    seccion_id: str,
    doc_repo: DocRepoDep,
    entrevista_repo: EntrevistaRepoDep,
    user: CurrentUser,
) -> IniciarEntrevistaResponse:
    """Devuelve la entrevista en curso sin tocar LLM.

    Útil para que el frontend hidrate el chat al reabrir la página.
    """
    doc = doc_repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    estado = entrevista_repo.obtener(str(documento_id), seccion_id)
    if estado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay entrevista activa para esta sección.",
        )
    ultimo_assistant = next(
        (m.contenido for m in reversed(estado.mensajes) if m.rol == "assistant"),
        "",
    )
    return IniciarEntrevistaResponse(
        turno=TurnoEntrevistaDTO(
            respuesta_asistente=ultimo_assistant,
            seccion_cerrada=estado.cerrada,
            borrador=None,
            n_mensajes=len(estado.mensajes),
        ),
        seccion_id=seccion_id,
        mensajes=[MensajeDTO.from_domain(m) for m in estado.mensajes],
    )


@router.delete("", response_model=OkResponse)
def descartar_entrevista(
    documento_id: UUID,
    seccion_id: str,
    entrevista_repo: EntrevistaRepoDep,
    user: CurrentUser,
) -> OkResponse:
    """Borra la entrevista en curso para esta sección (no afecta al documento)."""
    entrevista_repo.borrar(str(documento_id), seccion_id)
    return OkResponse(mensaje="Entrevista descartada.")
