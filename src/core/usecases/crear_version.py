"""Use case CrearVersion — crea un snapshot inmutable del Documento.

Diseño:
- Se invoca desde `ExportarDocumento` opcionalmente (toggle UI) o desde
  el dashboard manualmente con un comentario.
- Genera v1, v2, … en orden monotónico por documento.
- Si el snapshot es idéntico a la última versión (mismo hash), NO crea
  duplicado — devuelve la versión existente. Evita inflar la BD si el
  usuario exporta múltiples veces sin editar nada.
- También registra evento de audit `version_creada`.

NOTA: las versiones son INMUTABLES. No hay método `actualizar`. Para
"deshacer", se restaura el snapshot al estado del documento actual
(otro use case futuro `RestaurarVersion`).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.core.models import Documento, EventoAuditoria, Version, calcular_hash
from src.storage.repositories import DocumentoRepository, VersionRepository

logger = logging.getLogger(__name__)

# Campos que NO entran en el hash de contenido — cambian sin reflejar
# ediciones materiales del documento (audit_trail crece con cada acción,
# actualizado_en se mueve con cada guardado, metricas_uso registra costo).
_CAMPOS_EXCLUIDOS_DE_HASH = {"audit_trail", "actualizado_en", "metricas_uso"}


@dataclass(frozen=True)
class ResultadoCrearVersion:
    """Resultado de la creación de versión."""

    version: Version
    es_duplicado: bool
    """True si el snapshot era idéntico a la versión previa (no se duplicó)."""


class CrearVersion:
    """Use case: serializa el documento actual y crea una Version persistida."""

    def __init__(
        self,
        doc_repo: DocumentoRepository,
        version_repo: VersionRepository,
    ) -> None:
        self.doc_repo = doc_repo
        self.version_repo = version_repo

    def ejecutar(
        self,
        documento: Documento,
        *,
        comentario: str = "",
        actor: str = "default",
    ) -> ResultadoCrearVersion:
        # snapshot_json: serialización COMPLETA del documento (incluye audit_trail).
        snapshot_json = documento.model_dump_json()
        # hash_contenido: serialización SIN campos volátiles, para detectar
        # idempotencia real (si solo cambió el audit_trail o el timestamp,
        # el hash queda igual y no se duplica la versión).
        snapshot_material = documento.model_dump_json(
            exclude=_CAMPOS_EXCLUIDOS_DE_HASH,  # type: ignore[arg-type]
        )
        hash_actual = calcular_hash(snapshot_material)

        # Idempotencia: si la última versión tiene el mismo hash, no duplicar.
        ultima = self.version_repo.ultima_version(documento.id)
        if ultima is not None and ultima.hash_contenido == hash_actual:
            logger.info(
                "Versión idempotente: documento %s ya tiene v%d con mismo hash. Skip.",
                documento.id,
                ultima.numero,
            )
            return ResultadoCrearVersion(version=ultima, es_duplicado=True)

        numero = self.version_repo.proximo_numero(documento.id)
        version = Version(
            documento_id=documento.id,
            numero=numero,
            snapshot_json=snapshot_json,
            hash_contenido=hash_actual,
            comentario=comentario,
        )
        self.version_repo.crear(version)

        # Audit event en el documento (no en la versión, que es inmutable).
        documento.registrar_evento(
            EventoAuditoria(
                actor=actor,
                tipo="version_creada",
                descripcion=(
                    f"Versión v{numero} creada" + (f": {comentario}" if comentario else ".")
                ),
                metadata={
                    "version_id": str(version.id),
                    "version_numero": str(numero),
                    "hash": hash_actual[:12],  # primeros 12 chars, suficiente para audit
                },
            )
        )
        self.doc_repo.guardar(documento)

        return ResultadoCrearVersion(version=version, es_duplicado=False)
