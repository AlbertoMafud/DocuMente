"""Router: versiones (snapshots inmutables del documento).

Endpoints:
- GET    /documentos/{id}/versiones              — lista
- POST   /documentos/{id}/versiones              — crear snapshot ahora
- GET    /versiones/{version_id}                  — metadata
- GET    /versiones/{version_id}/snapshot         — payload JSON crudo
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from src.api.auth import CurrentUser
from src.api.deps import DocRepoDep, VersionRepoDep
from src.api.errors import not_found
from src.api.schemas import CrearVersionRequest, VersionDTO
from src.core.usecases import CrearVersion

router = APIRouter(tags=["versiones"])


@router.get("/documentos/{documento_id}/versiones", response_model=list[VersionDTO])
def listar_versiones(
    documento_id: UUID,
    doc_repo: DocRepoDep,
    version_repo: VersionRepoDep,
    user: CurrentUser,
) -> list[VersionDTO]:
    """Devuelve las versiones del documento (numeradas desc)."""
    if doc_repo.obtener(documento_id) is None:
        raise not_found("Documento")
    versiones = version_repo.listar_por_documento(documento_id)
    return [VersionDTO.from_domain(v) for v in versiones]


@router.post(
    "/documentos/{documento_id}/versiones",
    response_model=VersionDTO,
    status_code=status.HTTP_201_CREATED,
)
def crear_version(
    documento_id: UUID,
    payload: CrearVersionRequest,
    doc_repo: DocRepoDep,
    version_repo: VersionRepoDep,
    user: CurrentUser,
) -> VersionDTO:
    """Crea un snapshot inmutable del documento actual.

    Si el snapshot es idéntico al de la última versión (mismo hash),
    devuelve la versión existente — idempotencia natural.
    """
    documento = doc_repo.obtener(documento_id)
    if documento is None:
        raise not_found("Documento")
    actor = payload.actor or user
    uc = CrearVersion(doc_repo=doc_repo, version_repo=version_repo)
    resultado = uc.ejecutar(documento, comentario=payload.comentario, actor=actor)
    return VersionDTO.from_domain(resultado.version)


@router.get("/versiones/{version_id}", response_model=VersionDTO)
def obtener_version(
    version_id: UUID,
    version_repo: VersionRepoDep,
    user: CurrentUser,
) -> VersionDTO:
    """Metadata de una versión específica."""
    v = version_repo.obtener(version_id)
    if v is None:
        raise not_found("Versión")
    return VersionDTO.from_domain(v)


@router.get(
    "/versiones/{version_id}/snapshot",
    responses={200: {"content": {"application/json": {}}}},
    response_class=Response,
)
def obtener_snapshot(
    version_id: UUID,
    version_repo: VersionRepoDep,
    user: CurrentUser,
) -> Response:
    """Devuelve el snapshot_json crudo (sin envolver) de la versión.

    Útil para diff entre versiones o reconstruir estados previos.
    """
    v = version_repo.obtener(version_id)
    if v is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Versión no encontrada")
    return Response(
        content=v.snapshot_json,
        media_type="application/json",
    )
