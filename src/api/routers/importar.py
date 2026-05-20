"""Router: importación de documentos existentes (.docx/.pdf ancla + fuentes).

Endpoint:
- POST   /documentos/importar    — multipart/form-data con `ancla` (file)
                                   y opcional `fuentes` (multi-file).
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile, status

from src.api.auth import CurrentUser
from src.api.deps import DocRepoDep, LlmClientDep
from src.api.schemas import DocumentoDTO
from src.core.usecases import GapAnalyzer, ImportarDocumento
from src.docs.readers.anchor_reader import AnchorReader
from src.storage.storage import FilesystemStorage

router = APIRouter(prefix="/documentos", tags=["importar"])

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


@router.post(
    "/importar",
    response_model=DocumentoDTO,
    status_code=status.HTTP_201_CREATED,
)
async def importar_documento(
    ancla: UploadFile = File(  # noqa: B008
        ..., description="Archivo .docx o .pdf que da estructura."
    ),
    fuentes: list[UploadFile] = File(  # noqa: B008
        default_factory=list,
        description="Fuentes adicionales para auto-poblar secciones vacías.",
    ),
    actor: str = Form(default="default"),
    repo: DocRepoDep = None,  # type: ignore[assignment]
    llm: LlmClientDep = None,  # type: ignore[assignment]
    user: CurrentUser = "default",  # type: ignore[assignment]
) -> DocumentoDTO:
    """Importa un documento .docx/.pdf y devuelve el documento parseado.

    El archivo ancla se parsea contra el catálogo NYL Model Development.
    Las fuentes adicionales (PDF/XLSX/TXT/DOCX) se procesan para auto-poblar
    secciones vacías mediante SugerenciasMultiFuente — requiere LLM.
    """
    contenido_ancla = await ancla.read()
    nombre_ancla = ancla.filename or "documento.docx"

    fuentes_adicionales: list[tuple[BytesIO, str]] = []
    for f in fuentes:
        if f.filename is None:
            continue
        contenido = await f.read()
        fuentes_adicionales.append((BytesIO(contenido), f.filename))

    storage = FilesystemStorage(_DATA_DIR)
    uc = ImportarDocumento(
        storage=storage,
        reader=AnchorReader(),
        repo=repo,
        analyzer=GapAnalyzer(),
        llm=llm,
    )
    resultado = uc.ejecutar(
        archivo=BytesIO(contenido_ancla),
        nombre_original=nombre_ancla,
        user_id=actor or user,
        fuentes_adicionales=fuentes_adicionales or None,
    )
    return DocumentoDTO.from_domain(resultado.documento)
