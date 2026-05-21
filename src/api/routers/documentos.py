"""Router: CRUD de documentos + visibilidad + metadata + transiciones + signoff.

Endpoints:
- GET    /documentos              — listar (filtrado por visibilidad y user)
- POST   /documentos              — crear en blanco (MRM o Prophet)
- GET    /documentos/{id}         — obtener completo
- PATCH  /documentos/{id}/metadata        — editar metadata del modelo
- POST   /documentos/{id}/archivar
- POST   /documentos/{id}/desarchivar
- POST   /documentos/{id}/papelera
- POST   /documentos/{id}/restaurar
- DELETE /documentos/{id}/permanente
- POST   /documentos/{id}/estado          — cambio de estado MRM
- POST   /documentos/{id}/signoff         — registrar firma reviewer/fae
- POST   /papelera/purgar                 — job de purga manual (idempotente)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

from src.api.auth import CurrentUser
from src.api.deps import DocRepoDep, LlmClientDep
from src.api.errors import not_found
from src.api.schemas import (
    CambiarEstadoRequest,
    CrearDocumentoRequest,
    DocumentoDTO,
    DocumentoListItem,
    EditarMetadataRequest,
    OkResponse,
    RegistrarSignoffRequest,
)
from src.core.models import EventoAuditoria
from src.core.template_catalog_prophet import construir_secciones_vacias_prophet
from src.core.usecases import (
    ArchivarDocumento,
    CambiarEstadoDocumento,
    CrearDocumentoEnBlanco,
    RegistrarSignoff,
    purgar_papelera_expirada,
)

router = APIRouter(prefix="/documentos", tags=["documentos"])

Visibilidad = Literal["activos", "archivados", "papelera", "todos"]


@router.get("", response_model=list[DocumentoListItem])
def listar_documentos(
    repo: DocRepoDep,
    user: CurrentUser,
    visibilidad: Visibilidad = Query(  # noqa: B008
        default="activos",
        description="Filtro de visibilidad: activos (default), archivados, papelera, o todos.",
    ),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[DocumentoListItem]:
    """Lista los documentos del usuario filtrados por visibilidad."""
    if visibilidad == "papelera":
        docs = repo.listar_por_usuario(user, solo_papelera=True)
    elif visibilidad == "archivados":
        all_docs = repo.listar_por_usuario(user, incluir_archivados=True)
        docs = [d for d in all_docs if d.archivado]
    elif visibilidad == "todos":
        docs = repo.listar_por_usuario(user, incluir_archivados=True)
    else:  # activos
        docs = repo.listar_por_usuario(user)
    return [DocumentoListItem.from_domain(d) for d in docs[:limit]]


@router.post("", response_model=DocumentoDTO, status_code=status.HTTP_201_CREATED)
def crear_documento(
    payload: CrearDocumentoRequest,
    repo: DocRepoDep,
    user: CurrentUser,
) -> DocumentoDTO:
    """Crea un documento en blanco con las secciones del template.

    - `tipo=model_development` usa el catálogo NYL Model Development.
    - `tipo=prophet` usa el catálogo Prophet.
    """
    actor = payload.actor or user
    if payload.tipo == "prophet":
        # Prophet usa template propio — generamos sin el use case MRM.
        from src.core.models import Documento
        from src.core.models.documento import MetadataModelo

        nombre = payload.nombre_modelo.strip() or "Ficha Prophet sin nombre"
        documento = Documento(
            user_id=actor,
            tipo="prophet",
            metadata_modelo=MetadataModelo(nombre_modelo=nombre),
            secciones=construir_secciones_vacias_prophet(),
        )
        documento.registrar_evento(
            EventoAuditoria(
                timestamp=datetime.now(UTC),
                actor=actor,
                tipo="documento_creado",
                descripcion=f"Ficha Prophet creada: {nombre}",
                metadata={"tipo": "prophet"},
            )
        )
        repo.guardar(documento)
        return DocumentoDTO.from_domain(documento)

    # MRM Model Development
    nombre = payload.nombre_modelo.strip() or "Documento sin nombre"
    # CrearDocumentoEnBlanco exige nombre + model_id no vacíos. Para crear
    # sin model_id desde la API, generamos un placeholder editable después.
    model_id = nombre.replace(" ", "_").lower() or "doc"
    uc = CrearDocumentoEnBlanco(repo=repo)
    resultado = uc.ejecutar(
        nombre_modelo=nombre,
        model_id=model_id,
        user_id=actor,
    )
    return DocumentoDTO.from_domain(resultado.documento)


class _CrearConFuentesResponse(BaseModel):
    """Respuesta enriquecida del endpoint multipart de creación con fuentes."""

    documento: DocumentoDTO
    fuentes_extraidas: int
    fuentes_descartadas: list[str]
    secciones_prellenadas: int
    llm_disponible: bool
    advertencias: list[str]


@router.post(
    "/crear-con-fuentes",
    response_model=_CrearConFuentesResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_con_fuentes(
    repo: DocRepoDep,
    llm: LlmClientDep,
    user: CurrentUser,
    nombre_modelo: str = Form(...),
    actor: str | None = Form(default=None),
    fuentes: list[UploadFile] = File(default=[]),  # noqa: B008
) -> _CrearConFuentesResponse:
    """Crea un documento MRM en blanco + opcionalmente prellena secciones
    a partir de archivos fuente (PDF, DOCX, XLSX, CSV, TXT).

    Si hay LLM disponible y se subieron fuentes con texto útil, ejecuta
    `SugerenciasMultiFuente` para generar borradores automáticos en las
    secciones aplicables. Cada fuente que falle al extraerse se reporta
    en `fuentes_descartadas` — el flujo no se aborta.

    Solo soporta tipo `model_development` (Prophet usa otro flow).
    """
    actor_final = (actor or user).strip() or user
    nombre = nombre_modelo.strip() or "Documento sin nombre"
    model_id = nombre.replace(" ", "_").lower() or "doc"

    # Convertir UploadFile → tuple[IO[bytes], filename] que espera el UC
    fuentes_payload: list[tuple] = []
    for f in fuentes:
        if f.filename:
            fuentes_payload.append((f.file, f.filename))

    uc = CrearDocumentoEnBlanco(repo=repo, llm=llm)
    resultado = uc.ejecutar(
        nombre_modelo=nombre,
        model_id=model_id,
        user_id=actor_final,
        fuentes_adicionales=fuentes_payload or None,
    )

    return _CrearConFuentesResponse(
        documento=DocumentoDTO.from_domain(resultado.documento),
        fuentes_extraidas=resultado.fuentes_extraidas,
        fuentes_descartadas=resultado.fuentes_descartadas,
        secciones_prellenadas=resultado.secciones_prellenadas,
        llm_disponible=resultado.llm_disponible,
        advertencias=resultado.advertencias,
    )


@router.get("/{documento_id}", response_model=DocumentoDTO)
def obtener_documento(
    documento_id: UUID,
    repo: DocRepoDep,
    user: CurrentUser,
) -> DocumentoDTO:
    """Devuelve un documento completo con todas sus secciones."""
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    return DocumentoDTO.from_domain(doc)


@router.patch("/{documento_id}/metadata", response_model=DocumentoDTO)
def editar_metadata(
    documento_id: UUID,
    payload: EditarMetadataRequest,
    repo: DocRepoDep,
    user: CurrentUser,
) -> DocumentoDTO:
    """Actualiza la metadata del modelo. Solo se aplican los campos enviados."""
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")

    cambios: dict[str, object] = {}
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        if valor is None:
            continue
        anterior = getattr(doc.metadata_modelo, campo, None)
        if anterior != valor:
            setattr(doc.metadata_modelo, campo, valor)
            cambios[campo] = valor

    if cambios:
        doc.registrar_evento(
            EventoAuditoria(
                timestamp=datetime.now(UTC),
                actor=user,
                tipo="metadata_actualizada",
                descripcion=f"Metadata actualizada: {', '.join(cambios.keys())}",
                metadata={k: str(v) for k, v in cambios.items()},
            )
        )
        repo.guardar(doc)
    return DocumentoDTO.from_domain(doc)


# --- Visibilidad ---


class _AccionVisibilidadRequest(BaseModel):
    razon: str = ""
    actor: str = "default"


@router.post("/{documento_id}/archivar", response_model=DocumentoListItem)
def archivar(
    documento_id: UUID,
    payload: _AccionVisibilidadRequest,
    repo: DocRepoDep,
    user: CurrentUser,
) -> DocumentoListItem:
    actor = payload.actor or user
    uc = ArchivarDocumento(repo)
    uc.archivar(documento_id, actor=actor, razon=payload.razon)
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    return DocumentoListItem.from_domain(doc)


@router.post("/{documento_id}/desarchivar", response_model=DocumentoListItem)
def desarchivar(
    documento_id: UUID,
    repo: DocRepoDep,
    user: CurrentUser,
) -> DocumentoListItem:
    uc = ArchivarDocumento(repo)
    uc.desarchivar(documento_id, actor=user)
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    return DocumentoListItem.from_domain(doc)


@router.post("/{documento_id}/papelera", response_model=DocumentoListItem)
def enviar_a_papelera(
    documento_id: UUID,
    payload: _AccionVisibilidadRequest,
    repo: DocRepoDep,
    user: CurrentUser,
) -> DocumentoListItem:
    actor = payload.actor or user
    uc = ArchivarDocumento(repo)
    uc.enviar_a_papelera(documento_id, actor=actor, razon=payload.razon)
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    return DocumentoListItem.from_domain(doc)


@router.post("/{documento_id}/restaurar", response_model=DocumentoListItem)
def restaurar_de_papelera(
    documento_id: UUID,
    repo: DocRepoDep,
    user: CurrentUser,
) -> DocumentoListItem:
    uc = ArchivarDocumento(repo)
    uc.restaurar_de_papelera(documento_id, actor=user)
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    return DocumentoListItem.from_domain(doc)


@router.delete("/{documento_id}/permanente", response_model=OkResponse)
def eliminar_permanente(
    documento_id: UUID,
    repo: DocRepoDep,
    user: CurrentUser,
) -> OkResponse:
    """Borra el documento físicamente. Requiere rol admin.

    El flag `es_admin` se setea en True solo si el bearer token corresponde
    al password administrativo (el mismo que el gate). Una vez Cognito esté
    real (Fase A.1.c), se leerá del JWT claim.
    """
    uc = ArchivarDocumento(repo)
    try:
        uc.eliminar_permanente(documento_id, actor=user, es_admin=True)
    except (ValueError, PermissionError) as e:
        codigo = (
            status.HTTP_403_FORBIDDEN
            if isinstance(e, PermissionError)
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=codigo, detail=str(e)) from e
    return OkResponse(mensaje="Documento eliminado permanentemente.")


# --- Transiciones de estado MRM ---


@router.post("/{documento_id}/estado", response_model=DocumentoDTO)
def cambiar_estado(
    documento_id: UUID,
    payload: CambiarEstadoRequest,
    repo: DocRepoDep,
    user: CurrentUser,
) -> DocumentoDTO:
    """Mueve el documento entre estados MRM (draft → in_review → approved → published).

    Si la transición es inválida según la state machine, devuelve 409 Conflict
    con la lista de razones.
    """
    actor = payload.actor or user
    uc = CambiarEstadoDocumento(repo)
    uc.ejecutar(documento_id, destino=payload.destino, actor=actor)
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    return DocumentoDTO.from_domain(doc)


@router.post("/{documento_id}/signoff", response_model=DocumentoDTO)
def registrar_signoff(
    documento_id: UUID,
    payload: RegistrarSignoffRequest,
    repo: DocRepoDep,
    user: CurrentUser,
) -> DocumentoDTO:
    """Registra firma de Reviewer o FAE. Solo válido en estado in_review."""
    actor = payload.actor or user
    uc = RegistrarSignoff(repo)
    uc.ejecutar(documento_id, rol=payload.rol, actor=actor)
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    return DocumentoDTO.from_domain(doc)


# --- Job de purga ---


@router.post("/papelera/purgar", response_model=OkResponse, tags=["mantenimiento"])
def purgar_papelera(
    repo: DocRepoDep,
    user: CurrentUser,
    dias: int = Query(default=30, ge=1, description="Umbral en días para purga."),
) -> OkResponse:
    """Borra documentos que llevan más de `dias` en papelera.

    Idempotente. Se puede llamar manualmente o desde un cron.
    """
    n_purgados = purgar_papelera_expirada(repo, dias_retencion=dias)
    return OkResponse(mensaje=f"Purgados {n_purgados} documento(s) de papelera.")
