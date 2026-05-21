"""Router: apéndices (tabla/PDF/fórmula LaTeX) por sección.

Endpoints:
- POST   /documentos/{id}/secciones/{sid}/apendices/tabla    — XLSX/CSV upload
- POST   /documentos/{id}/secciones/{sid}/apendices/pdf      — PDF upload
- POST   /documentos/{id}/secciones/{sid}/apendices/formula  — LaTeX
- GET    /documentos/{id}/apendices                          — lista de apéndices
- DELETE /documentos/{id}/apendices/{apendice_id}            — borrar
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from src.api.auth import CurrentUser
from src.api.deps import DocRepoDep, EntrevistaRepoDep
from src.api.errors import not_found
from src.api.schemas import OkResponse
from src.core.usecases import (
    AdjuntarFormulaApendice,
    AdjuntarPdfApendice,
    AdjuntarTablaApendice,
)
from src.storage.storage import FilesystemStorage

router = APIRouter(prefix="/documentos/{documento_id}", tags=["apendices"])

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


class ApendiceDTO(BaseModel):
    id: UUID
    seccion_origen_id: str
    titulo: str
    tipo: str
    nombre_archivo_original: str
    contenido_md: str = ""


def _ap_to_dto(ap) -> ApendiceDTO:  # type: ignore[no-untyped-def]
    return ApendiceDTO(
        id=ap.id,
        seccion_origen_id=ap.seccion_origen_id,
        titulo=ap.titulo,
        tipo=ap.tipo,
        nombre_archivo_original=ap.nombre_archivo_original,
        contenido_md=ap.contenido_md or "",
    )


@router.get("/apendices", response_model=list[ApendiceDTO])
def listar_apendices(
    documento_id: UUID,
    repo: DocRepoDep,
    user: CurrentUser,
) -> list[ApendiceDTO]:
    """Lista los apéndices del documento."""
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    return [_ap_to_dto(ap) for ap in doc.apendices]


@router.post(
    "/secciones/{seccion_id}/apendices/tabla",
    response_model=list[ApendiceDTO],
    status_code=status.HTTP_201_CREATED,
)
async def adjuntar_tabla(
    documento_id: UUID,
    seccion_id: str,
    archivo: UploadFile = File(..., description=".xlsx, .xls o .csv"),  # noqa: B008
    titulo_base: str = Form(..., description="Título base; multihoja agrega ' — {hoja}'"),
    doc_repo: DocRepoDep = None,  # type: ignore[assignment]
    entrevista_repo: EntrevistaRepoDep = None,  # type: ignore[assignment]
    user: CurrentUser = "default",  # type: ignore[assignment]
) -> list[ApendiceDTO]:
    """Sube un Excel/CSV y crea uno o más apéndices (uno por hoja con datos)."""
    documento = doc_repo.obtener(documento_id)
    if documento is None:
        raise not_found("Documento")
    seccion = documento.seccion_por_id(seccion_id)
    if seccion is None:
        raise not_found(f"Sección '{seccion_id}'")

    contenido = await archivo.read()
    nombre = archivo.filename or "tabla.xlsx"

    uc = AdjuntarTablaApendice(
        storage=FilesystemStorage(_DATA_DIR),
        doc_repo=doc_repo,
        estado_repo=entrevista_repo,
    )
    try:
        resultados = uc.ejecutar_multihoja(
            documento=documento,
            seccion=seccion,
            archivo=BytesIO(contenido),
            nombre_original=nombre,
            titulo_base=titulo_base,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return [_ap_to_dto(r.apendice) for r in resultados]


@router.post(
    "/secciones/{seccion_id}/apendices/pdf",
    response_model=ApendiceDTO,
    status_code=status.HTTP_201_CREATED,
)
async def adjuntar_pdf(
    documento_id: UUID,
    seccion_id: str,
    archivo: UploadFile = File(..., description=".pdf"),  # noqa: B008
    titulo: str = Form(..., description="Título del apéndice."),
    doc_repo: DocRepoDep = None,  # type: ignore[assignment]
    entrevista_repo: EntrevistaRepoDep = None,  # type: ignore[assignment]
    user: CurrentUser = "default",  # type: ignore[assignment]
) -> ApendiceDTO:
    """Sube un PDF — cada página se embebe como imagen al exportar."""
    documento = doc_repo.obtener(documento_id)
    if documento is None:
        raise not_found("Documento")
    seccion = documento.seccion_por_id(seccion_id)
    if seccion is None:
        raise not_found(f"Sección '{seccion_id}'")

    contenido = await archivo.read()
    nombre = archivo.filename or "documento.pdf"

    uc = AdjuntarPdfApendice(
        storage=FilesystemStorage(_DATA_DIR),
        doc_repo=doc_repo,
        estado_repo=entrevista_repo,
    )
    try:
        resultado = uc.ejecutar(
            documento=documento,
            seccion=seccion,
            archivo=BytesIO(contenido),
            nombre_original=nombre,
            titulo=titulo,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _ap_to_dto(resultado.apendice)


class _FormulaRequest(BaseModel):
    latex_source: str
    titulo: str


@router.post(
    "/secciones/{seccion_id}/apendices/formula",
    response_model=ApendiceDTO,
    status_code=status.HTTP_201_CREATED,
)
def adjuntar_formula(
    documento_id: UUID,
    seccion_id: str,
    payload: _FormulaRequest,
    doc_repo: DocRepoDep,
    entrevista_repo: EntrevistaRepoDep,
    user: CurrentUser,
) -> ApendiceDTO:
    """Adjunta una fórmula LaTeX (se renderea como imagen al exportar)."""
    documento = doc_repo.obtener(documento_id)
    if documento is None:
        raise not_found("Documento")
    seccion = documento.seccion_por_id(seccion_id)
    if seccion is None:
        raise not_found(f"Sección '{seccion_id}'")

    uc = AdjuntarFormulaApendice(doc_repo=doc_repo, estado_repo=entrevista_repo)
    try:
        resultado = uc.ejecutar(
            documento=documento,
            seccion=seccion,
            latex_source=payload.latex_source,
            titulo=payload.titulo,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _ap_to_dto(resultado.apendice)


@router.delete("/apendices/{apendice_id}", response_model=OkResponse)
def borrar_apendice(
    documento_id: UUID,
    apendice_id: UUID,
    repo: DocRepoDep,
    user: CurrentUser,
) -> OkResponse:
    """Quita un apéndice del documento (no borra el archivo del storage)."""
    documento = repo.obtener(documento_id)
    if documento is None:
        raise not_found("Documento")
    idx = next(
        (i for i, ap in enumerate(documento.apendices) if ap.id == apendice_id),
        None,
    )
    if idx is None:
        raise not_found("Apéndice")
    documento.apendices.pop(idx)
    repo.guardar(documento)
    return OkResponse(mensaje="Apéndice eliminado.")
