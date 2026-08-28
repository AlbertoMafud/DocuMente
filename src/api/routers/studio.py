"""Router: Template Studio — creación y gobierno de templates dinámicos.

Fase 1 (admin): extraer estructura de un .docx → propuesta LLM → curación →
lint → publicar. Los endpoints marcados con `RequireAdmin` exigen el token de
admin cuando `DOCUMENTE_ADMIN_TOKEN` está configurado (spec §3).

`StudioError` hereda de `ValueError`, así que el handler global lo traduce a
HTTP 400 con el mensaje mostrable al usuario — sin try/except en cada handler.
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field

from src.api.auth import CurrentUser, RequireAdmin
from src.api.deps import LlmClientDep
from src.api.errors import not_found
from src.core.models.template_dinamico import (
    EstadoTemplate,
    ResultadoLint,
    SeccionCatalogoDinamica,
    TemplateDinamico,
)
from src.core.usecases.extraer_estructura_template import ExtraerEstructuraTemplate
from src.core.usecases.proponer_catalogo import ProponerCatalogo
from src.core.usecases.template_studio import (
    ActualizarSeccionesTemplate,
    BorrarTemplateBorrador,
    CorrerLintTemplate,
    CrearNuevaVersionTemplate,
    CrearTemplateBorrador,
    PublicarTemplate,
    RetirarTemplate,
)
from src.storage.repositories import TemplateDinamicoRepository

router = APIRouter(prefix="/studio", tags=["template-studio"])


def _repo() -> TemplateDinamicoRepository:
    return TemplateDinamicoRepository()


# --- DTOs ---


class SeccionCandidataDTO(BaseModel):
    titulo: str
    numero: str
    nivel: int
    n_caracteres: int


class ExtraccionDTO(BaseModel):
    """Estructura detectada + propuesta del LLM (pasos 2 y 3 del wizard)."""

    secciones_detectadas: list[SeccionCandidataDTO]
    n_tablas: int
    advertencias: list[str]
    propuesta: list[SeccionCatalogoDinamica]
    notas_llm: list[str]


class CrearTemplateRequest(BaseModel):
    nombre: str
    descripcion: str = ""
    area_duena: str = ""
    slug: str | None = None
    archivo_origen: str | None = None
    secciones: list[SeccionCatalogoDinamica] = Field(default_factory=list)


class ActualizarMetadataRequest(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    area_duena: str | None = None


class ActualizarSeccionesRequest(BaseModel):
    secciones: list[SeccionCatalogoDinamica]


class TransicionRequest(BaseModel):
    accion: Literal["publicar", "retirar"]
    aceptar_advertencias: bool = False


class TemplateListItem(BaseModel):
    id: UUID
    slug: str
    nombre: str
    descripcion: str
    area_duena: str
    estado: EstadoTemplate
    version: int
    n_secciones: int
    lint_aprobado: bool | None
    actualizado_en: str

    @classmethod
    def from_domain(cls, t: TemplateDinamico) -> TemplateListItem:
        return cls(
            id=t.id,
            slug=t.slug,
            nombre=t.nombre,
            descripcion=t.descripcion,
            area_duena=t.area_duena,
            estado=t.estado,
            version=t.version,
            n_secciones=len(t.secciones),
            lint_aprobado=t.resultado_lint.aprobado if t.resultado_lint else None,
            actualizado_en=t.actualizado_en.isoformat(),
        )


# --- Endpoints ---


@router.post("/templates/extraer", response_model=ExtraccionDTO)
async def extraer_y_proponer(
    admin: RequireAdmin,
    llm: LlmClientDep,
    archivo: Annotated[UploadFile, File(description="El .docx del template a convertir")],
    nombre: Annotated[str, Form()],
    descripcion: Annotated[str, Form()] = "",
) -> ExtraccionDTO:
    """Paso 2+3: extrae la estructura del .docx y pide la propuesta al LLM.

    La extracción es determinística; la propuesta requiere LLM. Sin LLM
    configurado se devuelve la estructura detectada y una advertencia — el
    admin puede construir el catálogo a mano desde ahí.
    """
    nombre_archivo = archivo.filename or "template.docx"
    if not nombre_archivo.lower().endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan archivos .docx como template de origen.",
        )

    contenido = await archivo.read()
    from io import BytesIO

    estructura = ExtraerEstructuraTemplate().ejecutar(BytesIO(contenido))

    detectadas = [
        SeccionCandidataDTO(
            titulo=s.titulo,
            numero=s.numero,
            nivel=s.nivel,
            n_caracteres=len(s.texto),
        )
        for s in estructura.secciones
    ]
    advertencias = list(estructura.advertencias)

    if llm is None:
        advertencias.append(
            "El asistente de IA no está disponible — se muestra solo la estructura "
            "detectada. Puedes construir el catálogo manualmente."
        )
        return ExtraccionDTO(
            secciones_detectadas=detectadas,
            n_tablas=estructura.n_tablas_total,
            advertencias=advertencias,
            propuesta=[],
            notas_llm=[],
        )

    propuesta = ProponerCatalogo(llm).ejecutar(
        nombre_template=nombre,
        descripcion=descripcion,
        estructura=estructura,
    )
    advertencias.extend(propuesta.advertencias)
    return ExtraccionDTO(
        secciones_detectadas=detectadas,
        n_tablas=estructura.n_tablas_total,
        advertencias=advertencias,
        propuesta=propuesta.secciones,
        notas_llm=propuesta.notas_llm,
    )


@router.post("/templates", response_model=TemplateDinamico, status_code=status.HTTP_201_CREATED)
def crear_template(
    payload: CrearTemplateRequest,
    admin: RequireAdmin,
) -> TemplateDinamico:
    """Persiste el borrador con la propuesta ya curada por el admin."""
    return CrearTemplateBorrador(repo=_repo()).ejecutar(
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        area_duena=payload.area_duena,
        secciones=payload.secciones,
        creado_por=admin,
        archivo_origen=payload.archivo_origen,
        slug=payload.slug,
    )


@router.get("/templates", response_model=list[TemplateListItem])
def listar_templates_studio(
    user: CurrentUser,
    estado: EstadoTemplate | None = None,
) -> list[TemplateListItem]:
    """Lista los templates del Studio, opcionalmente filtrados por estado."""
    return [TemplateListItem.from_domain(t) for t in _repo().listar(estado=estado)]


@router.get("/templates/{template_id}", response_model=TemplateDinamico)
def obtener_template(template_id: UUID, user: CurrentUser) -> TemplateDinamico:
    template = _repo().obtener(template_id)
    if template is None:
        raise not_found("Template")
    return template


@router.patch("/templates/{template_id}", response_model=TemplateDinamico)
def actualizar_metadata(
    template_id: UUID,
    payload: ActualizarMetadataRequest,
    admin: RequireAdmin,
) -> TemplateDinamico:
    """Actualiza nombre/descripción/área. El slug NO se cambia (es la identidad)."""
    repo = _repo()
    template = repo.obtener(template_id)
    if template is None:
        raise not_found("Template")
    if payload.nombre is not None:
        template.nombre = payload.nombre
    if payload.descripcion is not None:
        template.descripcion = payload.descripcion
    if payload.area_duena is not None:
        template.area_duena = payload.area_duena
    repo.guardar(template)
    return template


@router.put("/templates/{template_id}/secciones", response_model=TemplateDinamico)
def actualizar_secciones(
    template_id: UUID,
    payload: ActualizarSeccionesRequest,
    admin: RequireAdmin,
) -> TemplateDinamico:
    """Reemplaza el catálogo curado completo (paso 4 del wizard)."""
    repo = _repo()
    if repo.obtener(template_id) is None:
        raise not_found("Template")
    return ActualizarSeccionesTemplate(repo=repo).ejecutar(
        template_id, payload.secciones, actor=admin
    )


@router.post("/templates/{template_id}/lint", response_model=ResultadoLint)
def correr_lint(template_id: UUID, admin: RequireAdmin) -> ResultadoLint:
    """Corre la capa determinística del lint (L1-L9) y persiste el resultado."""
    repo = _repo()
    if repo.obtener(template_id) is None:
        raise not_found("Template")
    template = CorrerLintTemplate(repo=repo).ejecutar(template_id, actor=admin)
    assert template.resultado_lint is not None  # el use case siempre lo asigna
    return template.resultado_lint


@router.post("/templates/{template_id}/estado", response_model=TemplateDinamico)
def transicionar(
    template_id: UUID,
    payload: TransicionRequest,
    admin: RequireAdmin,
) -> TemplateDinamico:
    """Publica o retira el template (Fase 1: autoridad directa del admin)."""
    repo = _repo()
    if repo.obtener(template_id) is None:
        raise not_found("Template")
    if payload.accion == "publicar":
        return PublicarTemplate(repo=repo).ejecutar(
            template_id,
            actor=admin,
            aceptar_advertencias=payload.aceptar_advertencias,
        )
    return RetirarTemplate(repo=repo).ejecutar(template_id, actor=admin)


@router.post(
    "/templates/{template_id}/nueva-version",
    response_model=TemplateDinamico,
    status_code=status.HTTP_201_CREATED,
)
def nueva_version(template_id: UUID, admin: RequireAdmin) -> TemplateDinamico:
    """Copia un template publicado/retirado a un borrador v+1 editable."""
    repo = _repo()
    if repo.obtener(template_id) is None:
        raise not_found("Template")
    return CrearNuevaVersionTemplate(repo=repo).ejecutar(template_id, actor=admin)


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def borrar_template(template_id: UUID, admin: RequireAdmin) -> Response:
    """Borra un template — solo permitido en estado borrador."""
    repo = _repo()
    if repo.obtener(template_id) is None:
        raise not_found("Template")
    BorrarTemplateBorrador(repo=repo).ejecutar(template_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
