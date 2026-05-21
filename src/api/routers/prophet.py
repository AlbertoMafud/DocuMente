"""Router: Prophet — detectar modelos en Excel + crear Ficha Prophet desde registro.

Endpoints:
- POST   /prophet/detectar         — sube Excel, devuelve modelos detectados
- POST   /prophet/importar         — sube Excel + fila_idx + nombre, crea documento
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile, status
from pydantic import BaseModel

from src.api.auth import CurrentUser
from src.api.deps import DocRepoDep, LlmClientDep
from src.api.schemas import DocumentoDTO
from src.core.usecases import (
    DetectarModelosProphet,
    ImportarRegistroProphet,
    ModeloProphetInfo,
)

router = APIRouter(prefix="/prophet", tags=["prophet"])


class _DeteccionResponse(BaseModel):
    modelos: list[ModeloProphetInfo]
    advertencias: list[str] = []


@router.post("/detectar", response_model=_DeteccionResponse)
async def detectar_modelos(
    archivo: UploadFile = File(..., description="Excel del registro Prophet."),  # noqa: B008
    llm: LlmClientDep = None,  # type: ignore[assignment]
    user: CurrentUser = "default",  # type: ignore[assignment]
) -> _DeteccionResponse:
    """Analiza el Excel del registro y devuelve los modelos detectados.

    Útil para presentar al usuario una lista de modelos del registro antes
    de elegir cuál importar como Ficha Prophet.
    """
    contenido = await archivo.read()
    uc = DetectarModelosProphet(llm=llm)
    resultado = uc.ejecutar(contenido)
    return _DeteccionResponse(
        modelos=list(resultado.modelos),
        advertencias=list(resultado.advertencias),
    )


@router.post(
    "/importar",
    response_model=DocumentoDTO,
    status_code=status.HTTP_201_CREATED,
)
async def importar_registro(
    archivo: UploadFile = File(..., description="Excel del registro Prophet."),  # noqa: B008
    fila_idx: int = Form(..., description="Fila base-0 en Descripcion_General del modelo."),
    nombre_modelo: str = Form(..., description="Nombre humano del modelo (ej. 'VNB')."),
    actor: str = Form(default="default"),
    repo: DocRepoDep = None,  # type: ignore[assignment]
    llm: LlmClientDep = None,  # type: ignore[assignment]
    user: CurrentUser = "default",  # type: ignore[assignment]
) -> DocumentoDTO:
    """Crea una Ficha Prophet pre-poblada a partir del registro Excel."""
    contenido = await archivo.read()
    uc = ImportarRegistroProphet(repo=repo, llm=llm)
    resultado = uc.ejecutar(
        xlsx_bytes=contenido,
        fila_idx=fila_idx,
        nombre_modelo=nombre_modelo,
        user_id=actor or user,
    )
    if resultado.documento is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "mensaje": "No se pudo importar el registro.",
                "advertencias": resultado.advertencias,
            },
        )
    return DocumentoDTO.from_domain(resultado.documento)
