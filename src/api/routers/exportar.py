"""Router: export DOCX (MRM y Prophet) + polish + versionado.

Endpoints:
- POST   /documentos/{id}/exportar          — ExportarDocumento (MRM)
- POST   /documentos/{id}/exportar/prophet  — DocxWriterProphet (Prophet)
- POST   /documentos/{id}/polish            — DocumentPolisher (sugerencias coherencia)
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel

from src.api.auth import CurrentUser
from src.api.deps import DocRepoDep, LlmClientDep
from src.api.errors import not_found
from src.api.schemas import ExportarRequest
from src.core.models import EventoAuditoria
from src.core.usecases import (
    DocumentPolisher,
    DocxWriterProphet,
    ExportarDocumento,
    SugerenciaPolish,
)

router = APIRouter(prefix="/documentos/{documento_id}", tags=["exportar"])

_TEMPLATE_MRM = (
    Path(__file__).resolve().parent.parent.parent
    / "docs"
    / "templates"
    / "model_development_smnyl_final.docx"
)

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _content_disposition(filename: str) -> str:
    """Construye Content-Disposition seguro para Unicode (RFC 6266 + 5987).

    HTTP headers son latin-1 por spec. Si el filename tiene caracteres no
    representables (ej. em-dash en nombres de modelos), `filename="..."`
    crashea. Se añade `filename*=UTF-8''<percent-encoded>` para clientes
    modernos y un ASCII fallback para clientes antiguos.
    """
    ascii_fallback = filename.encode("ascii", "replace").decode("ascii").replace("?", "_")
    utf8_quoted = quote(filename, safe="")
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{utf8_quoted}"


@router.post(
    "/exportar",
    responses={200: {"content": {_DOCX_MIME: {}}}},
    response_class=Response,
)
def exportar_docx(
    documento_id: UUID,
    payload: ExportarRequest,
    repo: DocRepoDep,
    llm: LlmClientDep,
    user: CurrentUser,
) -> Response:
    """Genera el .docx con marca SMNYL y lo devuelve como descarga directa.

    Headers:
    - `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`
    - `Content-Disposition: attachment; filename="<nombre>.docx"`
    """
    actor = payload.actor or user
    if payload.polish and llm is not None:
        doc = repo.obtener(documento_id)
        if doc is None:
            raise not_found("Documento")
        DocumentPolisher(llm).revisar(doc)
        repo.guardar(doc)

    uc = ExportarDocumento(
        doc_repo=repo,
        template_path=_TEMPLATE_MRM,
        llm=llm,
    )
    resultado = uc.ejecutar(
        documento_id,
        actor=actor,
        idioma_objetivo=payload.idioma_objetivo,
        crear_version=payload.crear_version,
        comentario_version=payload.comentario_version,
    )
    return Response(
        content=resultado.contenido,
        media_type=_DOCX_MIME,
        headers={
            "Content-Disposition": _content_disposition(resultado.nombre_archivo),
            "X-Documente-Version": (
                str(resultado.version.version.numero) if resultado.version is not None else ""
            ),
        },
    )


@router.post(
    "/exportar/prophet",
    responses={200: {"content": {_DOCX_MIME: {}}}},
    response_class=Response,
)
def exportar_ficha_prophet(
    documento_id: UUID,
    repo: DocRepoDep,
    user: CurrentUser,
) -> Response:
    """Genera la Ficha Prophet DOCX. Requiere `tipo='prophet'`."""
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    if doc.tipo != "prophet":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este endpoint solo aplica a documentos tipo 'prophet'.",
        )

    writer = DocxWriterProphet()
    docx_bytes = writer.render(doc)
    nombre = (
        f"Ficha_Prophet_{doc.metadata_modelo.nombre_modelo.replace(' ', '_') or 'sin_nombre'}.docx"
    )
    doc.registrar_evento(
        EventoAuditoria(
            timestamp=datetime.now(UTC),
            actor=user,
            tipo="exportado",
            descripcion=f"Ficha Prophet exportada ({len(docx_bytes):,} bytes).",
            metadata={"nombre_archivo": nombre, "tipo": "prophet"},
        )
    )
    repo.guardar(doc)
    return Response(
        content=docx_bytes,
        media_type=_DOCX_MIME,
        headers={"Content-Disposition": _content_disposition(nombre)},
    )


class _PolishResultadoDTO(BaseModel):
    sugerencias: list[SugerenciaPolish]
    n_sugerencias: int


@router.post("/polish", response_model=_PolishResultadoDTO)
def polish_documento(
    documento_id: UUID,
    repo: DocRepoDep,
    llm: LlmClientDep,
    user: CurrentUser,
) -> _PolishResultadoDTO:
    """Ejecuta DocumentPolisher: Claude revisa el documento completo y
    reporta inconsistencias entre secciones (no modifica nada).

    Requiere LLM configurado (ANTHROPIC_API_KEY). Si no está, devuelve 503.
    """
    if llm is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM no configurado. Define ANTHROPIC_API_KEY en .env.",
        )
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    resultado = DocumentPolisher(llm).revisar(doc)
    repo.guardar(doc)
    return _PolishResultadoDTO(
        sugerencias=list(resultado.sugerencias),
        n_sugerencias=len(resultado.sugerencias),
    )
