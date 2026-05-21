"""Router: catálogos de plantillas (NYL Model Development y Prophet).

Endpoints:
- GET   /templates                       — lista de tipos soportados
- GET   /templates/mrm/secciones         — catálogo NYL completo
- GET   /templates/mrm/capitulos         — agrupación por capítulo (1-9)
- GET   /templates/prophet/secciones     — catálogo Prophet
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from src.api.auth import CurrentUser
from src.core.template_catalog import (
    CAPITULOS_NYL,
    TEMPLATE_MODEL_DEVELOPMENT,
    SeccionCatalogo,
)
from src.core.template_catalog_prophet import (
    TEMPLATE_PROPHET,
    SeccionCatalogoProphet,
)

router = APIRouter(prefix="/templates", tags=["templates"])


class _SeccionCatalogoDTO(BaseModel):
    id: str
    nombre: str
    numero: str
    obligatoria: bool
    intencion: str = ""
    preguntas_guia: list[str] = []


class _CapituloDTO(BaseModel):
    numero: str
    nombre: str
    secciones: list[_SeccionCatalogoDTO]


class _TemplateInfo(BaseModel):
    tipo: str
    nombre: str
    n_secciones: int


def _cat_to_dto(s: SeccionCatalogo | SeccionCatalogoProphet) -> _SeccionCatalogoDTO:
    return _SeccionCatalogoDTO(
        id=s.id,
        nombre=s.nombre,
        numero=getattr(s, "numero", ""),
        obligatoria=getattr(s, "obligatoria", True),
        intencion=getattr(s, "intencion", ""),
        preguntas_guia=list(getattr(s, "preguntas_guia", [])),
    )


@router.get("", response_model=list[_TemplateInfo])
def listar_templates(user: CurrentUser) -> list[_TemplateInfo]:
    """Lista los tipos de template disponibles."""
    return [
        _TemplateInfo(
            tipo="model_development",
            nombre="NYL Model Development Template",
            n_secciones=len(TEMPLATE_MODEL_DEVELOPMENT),
        ),
        _TemplateInfo(
            tipo="prophet",
            nombre="Ficha Prophet",
            n_secciones=len(TEMPLATE_PROPHET),
        ),
    ]


@router.get("/mrm/secciones", response_model=list[_SeccionCatalogoDTO])
def listar_secciones_mrm(user: CurrentUser) -> list[_SeccionCatalogoDTO]:
    """Catálogo NYL Model Development plano (28 secciones)."""
    return [_cat_to_dto(s) for s in TEMPLATE_MODEL_DEVELOPMENT]


@router.get("/mrm/capitulos", response_model=list[_CapituloDTO])
def listar_capitulos_mrm(user: CurrentUser) -> list[_CapituloDTO]:
    """Agrupación de secciones en los 9 capítulos NYL."""
    from collections import defaultdict

    por_capitulo: dict[str, list[SeccionCatalogo]] = defaultdict(list)
    for s in TEMPLATE_MODEL_DEVELOPMENT:
        cap_num = s.numero.split(".")[0] if s.numero else "?"
        por_capitulo[cap_num].append(s)

    return [
        _CapituloDTO(
            numero=num,
            nombre=CAPITULOS_NYL.get(num, ""),
            secciones=[_cat_to_dto(s) for s in por_capitulo[num]],
        )
        for num in CAPITULOS_NYL
    ]


@router.get("/prophet/secciones", response_model=list[_SeccionCatalogoDTO])
def listar_secciones_prophet(user: CurrentUser) -> list[_SeccionCatalogoDTO]:
    """Catálogo Ficha Prophet."""
    return [_cat_to_dto(s) for s in TEMPLATE_PROPHET]
