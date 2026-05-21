"""Router: versiones (snapshots inmutables del documento).

Endpoints:
- GET    /documentos/{id}/versiones              — lista
- POST   /documentos/{id}/versiones              — crear snapshot ahora
- GET    /documentos/{id}/versiones/{numero}     — vista read-only de una versión
- POST   /documentos/{id}/versiones/{numero}/exportar    — DOCX de una versión
- POST   /documentos/{id}/versiones/{numero}/restaurar   — restaurar a versión N
- GET    /versiones/{version_id}                  — metadata por UUID
- GET    /versiones/{version_id}/snapshot         — payload JSON crudo
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from src.api.auth import CurrentUser
from src.api.deps import DocRepoDep, LlmClientDep, VersionRepoDep
from src.api.errors import not_found
from src.api.schemas import CrearVersionRequest, DocumentoDTO, VersionDTO
from src.core.models import Documento
from src.core.usecases import (
    CrearVersion,
    ExportarDocumento,
    RestaurarVersion,
    VersionNoEncontrada,
)

router = APIRouter(tags=["versiones"])

_TEMPLATE_MRM = (
    Path(__file__).resolve().parent.parent.parent
    / "docs"
    / "templates"
    / "model_development_smnyl_final.docx"
)

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _content_disposition(filename: str) -> str:
    """Construye Content-Disposition seguro para Unicode (RFC 6266 + 5987).

    Espejo del helper en src/api/routers/exportar.py — no se duplica por
    ahora porque importar entre routers añade fricción mínima.
    """
    ascii_fallback = filename.encode("ascii", "replace").decode("ascii").replace("?", "_")
    utf8_quoted = quote(filename, safe="")
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{utf8_quoted}"


@router.get("/documentos/{documento_id}/versiones", response_model=list[VersionDTO])
def listar_versiones(
    documento_id: UUID,
    doc_repo: DocRepoDep,
    version_repo: VersionRepoDep,
    user: CurrentUser,
) -> list[VersionDTO]:
    """Devuelve las versiones del documento (numeradas asc)."""
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


@router.get(
    "/documentos/{documento_id}/versiones/{numero}",
    response_model=DocumentoDTO,
)
def obtener_documento_de_version(
    documento_id: UUID,
    numero: int,
    doc_repo: DocRepoDep,
    version_repo: VersionRepoDep,
    user: CurrentUser,
) -> DocumentoDTO:
    """Devuelve el contenido del documento tal como estaba en la versión N.

    Read-only: el documento "activo" no se toca. Útil para vista previa
    histórica antes de decidir si restaurar.
    """
    if doc_repo.obtener(documento_id) is None:
        raise not_found("Documento")
    version = version_repo.por_doc_y_numero(documento_id, numero)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El documento no tiene una versión v{numero}.",
        )
    documento_snapshot = Documento.model_validate_json(version.snapshot_json)
    return DocumentoDTO.from_domain(documento_snapshot)


@router.post(
    "/documentos/{documento_id}/versiones/{numero}/exportar",
    responses={200: {"content": {_DOCX_MIME: {}}}},
    response_class=Response,
)
def exportar_version(
    documento_id: UUID,
    numero: int,
    doc_repo: DocRepoDep,
    version_repo: VersionRepoDep,
    llm: LlmClientDep,
    user: CurrentUser,
) -> Response:
    """Genera el DOCX de una versión histórica (NO la activa).

    Reusa `ExportarDocumento` pero apuntando al snapshot deserializado.
    No crea una versión nueva (la versión exportada YA ES versionada).
    """
    if doc_repo.obtener(documento_id) is None:
        raise not_found("Documento")
    version = version_repo.por_doc_y_numero(documento_id, numero)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El documento no tiene una versión v{numero}.",
        )

    documento_snapshot = Documento.model_validate_json(version.snapshot_json)

    # Repo "fake" que devuelve el snapshot deserializado — el use case
    # solo necesita doc_repo.obtener(); no toca persistencia para exportar.
    class _SnapshotRepo:
        def obtener(self, _id: UUID) -> Documento | None:
            return documento_snapshot

        def guardar(self, _doc: Documento) -> None:
            return None  # noop — la versión no se modifica

    uc = ExportarDocumento(
        doc_repo=_SnapshotRepo(),  # type: ignore[arg-type]
        template_path=_TEMPLATE_MRM,
        llm=llm,
    )
    resultado = uc.ejecutar(
        documento_id,
        actor=user,
        idioma_objetivo="bilingue",
        crear_version=False,
    )

    # Nombre incluye el número de versión para que se distinga del activo
    nombre_modelo = documento_snapshot.metadata_modelo.nombre_modelo or "documento"
    nombre_archivo = f"{nombre_modelo.replace(' ', '_')}_v{numero}.docx"
    return Response(
        content=resultado.contenido,
        media_type=_DOCX_MIME,
        headers={
            "Content-Disposition": _content_disposition(nombre_archivo),
            "X-Documente-Version": str(numero),
        },
    )


@router.post(
    "/documentos/{documento_id}/versiones/{numero}/restaurar",
    response_model=DocumentoDTO,
)
def restaurar_version(
    documento_id: UUID,
    numero: int,
    doc_repo: DocRepoDep,
    version_repo: VersionRepoDep,
    user: CurrentUser,
) -> DocumentoDTO:
    """Restaura el documento al contenido de la versión N.

    Crea automáticamente un snapshot del estado actual ANTES (comentario
    "Pre-restore from vN") para que el usuario no pierda trabajo. Registra
    evento `version_restaurada` en el audit_trail.
    """
    uc = RestaurarVersion(doc_repo=doc_repo, version_repo=version_repo)
    try:
        resultado = uc.ejecutar(documento_id, numero, actor=user)
    except VersionNoEncontrada as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return DocumentoDTO.from_domain(resultado.documento)


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
