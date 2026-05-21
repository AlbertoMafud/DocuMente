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

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
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
from src.core.models import (
    Documento,
    EventoAuditoria,
    FuenteContexto,
    MetadataModelo,
)
from src.core.template_catalog import construir_secciones_vacias
from src.core.template_catalog_prophet import construir_secciones_vacias_prophet
from src.core.usecases import (
    ArchivarDocumento,
    CambiarEstadoDocumento,
    CrearDocumentoEnBlanco,
    RegistrarSignoff,
    purgar_papelera_expirada,
)
from src.core.usecases.sugerencias_multifuente import (
    EventoProgreso,
    SugerenciasMultiFuente,
)
from src.docs.readers import extraer_texto
from src.llm.vision_describer import VisionDescriber

logger = logging.getLogger(__name__)

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
    describir_imagenes: bool = Form(default=False),
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
        describir_imagenes=describir_imagenes,
    )

    return _CrearConFuentesResponse(
        documento=DocumentoDTO.from_domain(resultado.documento),
        fuentes_extraidas=resultado.fuentes_extraidas,
        fuentes_descartadas=resultado.fuentes_descartadas,
        secciones_prellenadas=resultado.secciones_prellenadas,
        llm_disponible=resultado.llm_disponible,
        advertencias=resultado.advertencias,
    )


def _sse_event(event: str, data: dict) -> str:
    """Formatea un evento SSE estándar — type + JSON payload."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/crear-con-fuentes/stream")
async def crear_con_fuentes_stream(
    repo: DocRepoDep,
    llm: LlmClientDep,
    user: CurrentUser,
    nombre_modelo: str = Form(...),
    actor: str | None = Form(default=None),
    describir_imagenes: bool = Form(default=False),
    fuentes: list[UploadFile] = File(default=[]),  # noqa: B008
) -> StreamingResponse:
    """Versión streaming de `crear-con-fuentes` — emite Server-Sent Events.

    Eventos:
    - `created`: documento esqueleto guardado (rápido, sin LLM).
        data: {"documento_id": "...", "total_secciones": 28, "fuentes_extraidas": N}
    - `progress`: una sección terminó de procesar (LLM).
        data: {"seccion_id", "seccion_nombre", "seccion_numero",
               "completadas", "total", "estado"}
    - `done`: pipeline completo.
        data: {"documento_id", "secciones_prellenadas", "advertencias"}
    - `error`: fallo no recuperable.
        data: {"detail"}

    El cliente debe usar EventSource o equivalente para consumir.
    """
    actor_final = (actor or user).strip() or user
    nombre = nombre_modelo.strip() or "Documento sin nombre"
    model_id = nombre.replace(" ", "_").lower() or "doc"

    # Leer todos los bytes de las fuentes ahora (antes del StreamingResponse).
    # Los UploadFile no son seguros de consumir desde un async generator que
    # vive después de que el handler regresa.
    fuentes_data: list[tuple[bytes, str]] = []
    for f in fuentes:
        if f.filename:
            contenido = await f.read()
            fuentes_data.append((contenido, f.filename))

    async def event_stream() -> AsyncIterator[str]:
        try:
            # 1. Crear documento esqueleto sin LLM (rápido)
            from io import BytesIO

            documento = Documento(
                user_id=actor_final,
                metadata_modelo=MetadataModelo(nombre_modelo=nombre, model_id=model_id),
                secciones=construir_secciones_vacias(),
            )
            documento.registrar_evento(
                EventoAuditoria(
                    actor=actor_final,
                    tipo="documento_creado",
                    descripcion=f"Documento creado desde cero: {nombre}",
                    metadata={"model_id": model_id, "stream": "true"},
                )
            )

            # 2. Procesar fuentes (extraer texto, no llama LLM excepto visión)
            vision_describer = (
                VisionDescriber(llm) if (describir_imagenes and llm is not None) else None
            )
            fuentes_descartadas: list[str] = []
            for raw_bytes, archivo_nombre in fuentes_data:
                try:
                    tipo, texto = extraer_texto(
                        BytesIO(raw_bytes),
                        archivo_nombre,
                        vision_describer=vision_describer,
                    )
                except Exception as exc:
                    logger.warning(
                        "Stream: no se pudo extraer '%s': %s",
                        archivo_nombre,
                        exc,
                    )
                    fuentes_descartadas.append(archivo_nombre)
                    continue
                if texto.strip():
                    documento.fuentes_contexto.append(
                        FuenteContexto(
                            nombre_archivo=archivo_nombre,
                            tipo=tipo,
                            texto_extraido=texto,
                        )
                    )
                else:
                    fuentes_descartadas.append(archivo_nombre)

            repo.guardar(documento)

            # Evento "created" — documento ya tiene ID persistido
            yield _sse_event(
                "created",
                {
                    "documento_id": str(documento.id),
                    "total_secciones": len(documento.secciones),
                    "fuentes_extraidas": len(documento.fuentes_contexto),
                    "fuentes_descartadas": fuentes_descartadas,
                },
            )

            # 3. Si no hay LLM o no hay fuentes, terminamos sin sugerencias
            advertencias: list[str] = []
            if fuentes_descartadas:
                advertencias.append(
                    f"No se pudo leer texto útil de: {', '.join(fuentes_descartadas)}."
                )

            if llm is None and documento.fuentes_contexto:
                advertencias.append(
                    "Fuentes guardadas pero LLM no disponible — sin borradores automáticos."
                )

            secciones_prellenadas = 0
            if llm is not None and documento.fuentes_contexto:
                # 4. Pipeline LLM — usar callback para emitir SSE por sección
                queue: asyncio.Queue[EventoProgreso | None] = asyncio.Queue()

                async def on_progress(e: EventoProgreso) -> None:
                    await queue.put(e)

                uc_sugerencias = SugerenciasMultiFuente(llm)
                # Lanzar el pipeline LLM en background. Su callback va a
                # ir poniendo eventos en la queue mientras procesa.
                pipeline_task = asyncio.create_task(
                    uc_sugerencias.ejecutar_async(
                        documento,
                        on_progress=on_progress,
                    )
                )

                # Drenar la queue hasta que el pipeline termine
                while True:
                    if pipeline_task.done() and queue.empty():
                        break
                    try:
                        evento = await asyncio.wait_for(queue.get(), timeout=0.5)
                    except TimeoutError:
                        continue
                    yield _sse_event(
                        "progress",
                        {
                            "seccion_id": evento.seccion_id,
                            "seccion_nombre": evento.seccion_nombre,
                            "seccion_numero": evento.seccion_numero,
                            "completadas": evento.completadas,
                            "total": evento.total,
                            "estado": evento.estado,
                        },
                    )

                # Recuperar resultado final (puede haber lanzado excepción)
                resultado_sugerencias = await pipeline_task
                secciones_prellenadas = resultado_sugerencias.secciones_pobladas
                if resultado_sugerencias.secciones_pobladas > 0:
                    repo.guardar(documento)
                if resultado_sugerencias.hubo_errores:
                    advertencias.append(
                        f"Algunas secciones no se pudieron prellenar "
                        f"({len(resultado_sugerencias.errores)} error(es) al llamar al LLM)."
                    )

            # 5. Evento final con resumen + documento_id para que el frontend
            # navegue al dashboard
            yield _sse_event(
                "done",
                {
                    "documento_id": str(documento.id),
                    "secciones_prellenadas": secciones_prellenadas,
                    "advertencias": advertencias,
                    "llm_disponible": llm is not None,
                },
            )
        except Exception as exc:
            logger.exception("Stream falló: %s", exc)
            yield _sse_event("error", {"detail": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Algunos proxies (nginx) cierran conexiones largas si no hay traffic;
            # X-Accel-Buffering=no le dice a nginx que no bufferee.
            "X-Accel-Buffering": "no",
        },
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
