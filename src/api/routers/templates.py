"""Router: catálogos de plantillas (NYL Model Development y Prophet).

Endpoints:
- GET   /templates                       — lista de tipos soportados
- GET   /templates/mrm/secciones         — catálogo NYL completo
- GET   /templates/mrm/capitulos         — agrupación por capítulo (1-9)
- GET   /templates/prophet/secciones     — catálogo Prophet
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
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
    """Lista los tipos de template disponibles para crear documentos.

    Resuelve por el registro: incluye los congelados (MRM, Prophet) y los
    dinámicos publicados en el Template Studio — la UI de "Crear documento"
    se vuelve dinámica sin cambios adicionales.
    """
    from src.core.template_registry import listar_templates as _listar_specs

    return [
        _TemplateInfo(tipo=spec.id, nombre=spec.nombre, n_secciones=len(spec.catalogo))
        for spec in _listar_specs()
    ]


@router.get("/{tipo}/catalogo", response_model=list[_SeccionCatalogoDTO])
def listar_secciones_de_tipo(tipo: str, user: CurrentUser) -> list[_SeccionCatalogoDTO]:
    """Catálogo de cualquier tipo registrado (congelado o dinámico).

    Genérico vía registro. Los paths /mrm/... y /prophet/... se conservan por
    compatibilidad con el frontend actual.
    """
    from src.core.template_registry import TemplateDesconocidoError, resolver_template

    try:
        spec = resolver_template(tipo)
    except TemplateDesconocidoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        _SeccionCatalogoDTO(
            id=s.id,
            nombre=s.nombre,
            numero=s.numero,
            obligatoria=s.obligatoria,
            intencion=s.intencion,
            preguntas_guia=list(s.preguntas_guia),
        )
        for s in spec.catalogo
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
