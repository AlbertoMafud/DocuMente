"""Router: operaciones sobre secciones de un documento.

Endpoints:
- GET    /documentos/{id}/secciones                   — listar secciones
- GET    /documentos/{id}/secciones/{sid}             — obtener una sección
- PUT    /documentos/{id}/secciones/{sid}             — editar contenido
- POST   /documentos/{id}/secciones/{sid}/omitir      — marcar como omitida con motivo
- POST   /documentos/{id}/secciones/{sid}/reactivar   — quitar omisión (vuelve a vacía)
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter

from src.api.auth import CurrentUser
from src.api.deps import DocRepoDep
from src.api.errors import not_found
from src.api.schemas import (
    EditarSeccionRequest,
    OkResponse,
    OmitirSeccionRequest,
    SeccionDTO,
)
from src.core.models import EventoAuditoria
from src.core.usecases import OmitirSeccion

router = APIRouter(prefix="/documentos/{documento_id}/secciones", tags=["secciones"])


@router.get("", response_model=list[SeccionDTO])
def listar_secciones(
    documento_id: UUID,
    repo: DocRepoDep,
    user: CurrentUser,
) -> list[SeccionDTO]:
    """Lista todas las secciones del documento (vacías y llenas)."""
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    return [SeccionDTO.from_domain(s) for s in doc.secciones]


@router.get("/{seccion_id}", response_model=SeccionDTO)
def obtener_seccion(
    documento_id: UUID,
    seccion_id: str,
    repo: DocRepoDep,
    user: CurrentUser,
) -> SeccionDTO:
    """Devuelve una sección específica del documento."""
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    seccion = doc.seccion_por_id(seccion_id)
    if seccion is None:
        raise not_found(f"Sección '{seccion_id}'")
    return SeccionDTO.from_domain(seccion)


@router.put("/{seccion_id}", response_model=SeccionDTO)
def editar_seccion(
    documento_id: UUID,
    seccion_id: str,
    payload: EditarSeccionRequest,
    repo: DocRepoDep,
    user: CurrentUser,
) -> SeccionDTO:
    """Reemplaza el contenido de una sección.

    La completitud se recalcula automáticamente:
    - vacío → "vacia"
    - <200 caracteres → "parcial"
    - ≥200 caracteres → "completa"

    Esta heurística replica la del reader/editor MRM. Para Prophet, la
    completitud se setea a "completa" ya que el contenido es JSON
    estructurado (no aplica la regla de longitud).
    """
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    seccion = doc.seccion_por_id(seccion_id)
    if seccion is None:
        raise not_found(f"Sección '{seccion_id}'")

    actor = payload.actor or user
    contenido_limpio = payload.contenido.strip()
    seccion.contenido = contenido_limpio if contenido_limpio else None

    if doc.tipo == "prophet":
        # Prophet: contenido siempre JSON, se considera completa cuando hay
        # cualquier payload no vacío.
        seccion.completitud = "completa" if contenido_limpio else "vacia"
    else:
        if not contenido_limpio:
            seccion.completitud = "vacia"
        elif len(contenido_limpio) < 200:
            seccion.completitud = "parcial"
        else:
            seccion.completitud = "completa"

    doc.registrar_evento(
        EventoAuditoria(
            timestamp=datetime.now(UTC),
            actor=actor,
            tipo="seccion_editada",
            descripcion=f"Sección '{seccion.numero} {seccion.nombre}' editada vía API.",
            seccion_id=seccion_id,
        )
    )
    repo.guardar(doc)
    return SeccionDTO.from_domain(seccion)


@router.post("/{seccion_id}/omitir", response_model=SeccionDTO)
def omitir_seccion(
    documento_id: UUID,
    seccion_id: str,
    payload: OmitirSeccionRequest,
    repo: DocRepoDep,
    user: CurrentUser,
) -> SeccionDTO:
    """Marca una sección como omitida con motivo justificado.

    Una sección omitida cuenta como "resuelta" para la state machine —
    permite avanzar a in_review sin tener que llenar contenido. El motivo
    queda registrado tanto en `seccion.motivo_omision` como en el
    audit_trail.
    """
    actor = payload.actor or user
    uc = OmitirSeccion(repo)
    uc.ejecutar(
        documento_id,
        seccion_id=seccion_id,
        motivo=payload.motivo,
        actor=actor,
    )
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    seccion = doc.seccion_por_id(seccion_id)
    if seccion is None:
        raise not_found(f"Sección '{seccion_id}'")
    return SeccionDTO.from_domain(seccion)


@router.post("/{seccion_id}/reactivar", response_model=SeccionDTO)
def reactivar_seccion(
    documento_id: UUID,
    seccion_id: str,
    repo: DocRepoDep,
    user: CurrentUser,
) -> SeccionDTO:
    """Quita la marca de omitida. Vuelve la sección a estado 'vacia'."""
    doc = repo.obtener(documento_id)
    if doc is None:
        raise not_found("Documento")
    seccion = doc.seccion_por_id(seccion_id)
    if seccion is None:
        raise not_found(f"Sección '{seccion_id}'")
    if seccion.completitud != "omitida":
        return SeccionDTO.from_domain(seccion)

    seccion.completitud = "vacia"
    seccion.motivo_omision = None
    doc.registrar_evento(
        EventoAuditoria(
            timestamp=datetime.now(UTC),
            actor=user,
            tipo="seccion_editada",
            descripcion=f"Sección '{seccion.numero}' reactivada (ya no omitida).",
            seccion_id=seccion_id,
        )
    )
    repo.guardar(doc)
    return SeccionDTO.from_domain(seccion)


# Endpoint convenience: lista de motivos válidos (catálogo UX para frontend)
catalog_router = APIRouter(prefix="/catalogos", tags=["catalogos"])


@catalog_router.get("/motivos-omision", response_model=list[str])
def motivos_omision_catalog(user: CurrentUser) -> list[str]:
    """Catálogo de motivos sugeridos para omitir secciones."""
    from src.core.usecases import MOTIVOS_OMISION

    return list(MOTIVOS_OMISION)


@catalog_router.get("/ok", response_model=OkResponse)
def catalog_health(user: CurrentUser) -> OkResponse:
    """Sanity check del catálogo (no se usa en prod)."""
    return OkResponse(mensaje="Catálogo disponible")
