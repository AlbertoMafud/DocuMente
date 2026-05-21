"""Router: brechas (gap analysis) y auditoría de un documento.

Endpoints:
- GET    /documentos/{id}/brechas       — GapAnalyzer sobre el documento
- GET    /documentos/{id}/auditoria     — audit_trail completo
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from src.api.auth import CurrentUser
from src.api.deps import DocRepoDep
from src.api.errors import not_found
from src.api.schemas import BrechaDTO, EventoDTO
from src.core.usecases import GapAnalyzer

router = APIRouter(prefix="/documentos/{documento_id}", tags=["analisis"])


@router.get("/brechas", response_model=list[BrechaDTO])
def listar_brechas(
    documento_id: UUID,
    repo: DocRepoDep,
    user: CurrentUser,
) -> list[BrechaDTO]:
    """Ejecuta el GapAnalyzer y devuelve las brechas detectadas.

    El cálculo es síncrono y rápido — son reglas estáticas sobre el
    documento (no llama al LLM).
    """
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    brechas = GapAnalyzer().analizar(doc)
    return [BrechaDTO.from_domain(b) for b in brechas]


@router.get("/auditoria", response_model=list[EventoDTO])
def listar_auditoria(
    documento_id: UUID,
    repo: DocRepoDep,
    user: CurrentUser,
    limit: int = Query(default=200, ge=1, le=1000),
    desde: int = Query(default=0, ge=0, description="Offset para paginación simple."),
) -> list[EventoDTO]:
    """Devuelve el audit_trail del documento (más reciente primero)."""
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    eventos = sorted(doc.audit_trail, key=lambda e: e.timestamp, reverse=True)
    return [EventoDTO.from_domain(e) for e in eventos[desde : desde + limit]]
