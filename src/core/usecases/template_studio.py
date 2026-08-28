"""Use cases del Template Studio: ciclo de vida del template dinámico.

Fase 1 (admin): crear borrador → curar secciones → lint → publicar directo.
Fase 2 agrega proponer/devolver (los estados ya existen aquí; la state
machine formal con razones legibles llega en la sesión S-F — estas
validaciones cubren lo que Fase 1 necesita sin bloquearla).

Reglas duras que estos use cases garantizan (spec §5, §8):
- Publicar exige lint SIN errores (advertencias requieren aceptación explícita).
- Publicar retira automáticamente la versión publicada anterior del mismo slug.
- Un template publicado no se edita: se crea nueva versión (copia a borrador).
- Todo genera EventoAuditoria en el audit_trail del template.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from src.core.models import EventoAuditoria
from src.core.models.template_dinamico import (
    SeccionCatalogoDinamica,
    TemplateDinamico,
)
from src.core.rules.template_lint import lint_secciones
from src.core.template_registry import TIPOS_CODIGO
from src.storage.repositories import TemplateDinamicoRepository

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")


class StudioError(ValueError):
    """Error de negocio del Studio, con mensaje mostrable al usuario."""


def _evento(actor: str, tipo: str, descripcion: str, **metadata: str) -> EventoAuditoria:
    return EventoAuditoria(
        timestamp=datetime.now(UTC),
        actor=actor,
        tipo=tipo,  # type: ignore[arg-type]
        descripcion=descripcion,
        metadata=metadata,
    )


def _slugificar(nombre: str) -> str:
    slug = nombre.strip().lower()
    slug = re.sub(r"[áàä]", "a", slug)
    slug = re.sub(r"[éèë]", "e", slug)
    slug = re.sub(r"[íìï]", "i", slug)
    slug = re.sub(r"[óòö]", "o", slug)
    slug = re.sub(r"[úùü]", "u", slug)
    slug = slug.replace("ñ", "n")
    slug = re.sub(r"[^a-z0-9]+", "_", slug).strip("_")
    return slug or "template"


@dataclass
class CrearTemplateBorrador:
    """Crea el borrador inicial (paso 3→4: propuesta curada → borrador persistido)."""

    repo: TemplateDinamicoRepository

    def ejecutar(
        self,
        *,
        nombre: str,
        descripcion: str = "",
        area_duena: str = "",
        secciones: list[SeccionCatalogoDinamica],
        creado_por: str = "default",
        archivo_origen: str | None = None,
        slug: str | None = None,
    ) -> TemplateDinamico:
        nombre_clean = nombre.strip()
        if not nombre_clean:
            raise StudioError("El nombre del template no puede estar vacío.")
        slug_final = (slug or _slugificar(nombre_clean)).strip()
        if not _SLUG_RE.match(slug_final):
            raise StudioError(f"Slug inválido: '{slug_final}' (minúsculas, dígitos y guión bajo).")
        if slug_final in TIPOS_CODIGO:
            raise StudioError(
                f"'{slug_final}' está reservado para un template institucional congelado."
            )

        template = TemplateDinamico(
            slug=slug_final,
            nombre=nombre_clean,
            descripcion=descripcion.strip(),
            area_duena=area_duena.strip(),
            secciones=secciones,
            creado_por=creado_por,
            archivo_origen=archivo_origen,
        )
        template.registrar_evento(
            _evento(creado_por, "template_creado", f"Template '{nombre_clean}' creado en el Studio")
        )
        if archivo_origen:
            template.registrar_evento(
                _evento(
                    creado_por,
                    "template_extraido",
                    f"Estructura extraída de '{archivo_origen}'",
                    archivo=archivo_origen,
                )
            )
        if secciones:
            template.registrar_evento(
                _evento(
                    creado_por,
                    "catalogo_propuesto_llm",
                    f"Catálogo inicial con {len(secciones)} sección(es)",
                    n_secciones=str(len(secciones)),
                )
            )
        self.repo.guardar(template)
        return template


@dataclass
class ActualizarSeccionesTemplate:
    """Reemplaza el catálogo curado completo (paso 4 del wizard)."""

    repo: TemplateDinamicoRepository

    def ejecutar(
        self,
        template_id: UUID,
        secciones: list[SeccionCatalogoDinamica],
        actor: str = "default",
    ) -> TemplateDinamico:
        template = self.repo.obtener(template_id)
        if template is None:
            raise StudioError("El template no existe.")
        if template.estado not in ("borrador", "propuesto"):
            raise StudioError(
                f"Un template en estado '{template.estado}' no se edita — crea una nueva versión."
            )
        template.secciones = secciones
        # El lint previo queda obsoleto al cambiar el catálogo.
        template.resultado_lint = None
        template.registrar_evento(
            _evento(
                actor,
                "seccion_catalogo_editada",
                f"Catálogo actualizado ({len(secciones)} secciones)",
                n_secciones=str(len(secciones)),
            )
        )
        self.repo.guardar(template)
        return template


@dataclass
class CorrerLintTemplate:
    """Corre la capa determinística del lint y persiste el resultado."""

    repo: TemplateDinamicoRepository

    def ejecutar(self, template_id: UUID, actor: str = "default") -> TemplateDinamico:
        template = self.repo.obtener(template_id)
        if template is None:
            raise StudioError("El template no existe.")
        resultado = lint_secciones(template.secciones)
        template.resultado_lint = resultado
        template.registrar_evento(
            _evento(
                actor,
                "lint_ejecutado",
                f"Lint: {len(resultado.errores)} error(es), "
                f"{len(resultado.advertencias)} advertencia(s)",
                errores=str(len(resultado.errores)),
                advertencias=str(len(resultado.advertencias)),
            )
        )
        self.repo.guardar(template)
        return template


@dataclass
class PublicarTemplate:
    """Publica un borrador/propuesto (Fase 1: autoridad directa del admin).

    Exige lint vigente y sin errores. Si hay advertencias, exige
    `aceptar_advertencias=True` — la aceptación queda en el audit trail.
    Retira automáticamente la versión publicada anterior del mismo slug.
    """

    repo: TemplateDinamicoRepository

    def ejecutar(
        self,
        template_id: UUID,
        actor: str = "default",
        *,
        aceptar_advertencias: bool = False,
    ) -> TemplateDinamico:
        template = self.repo.obtener(template_id)
        if template is None:
            raise StudioError("El template no existe.")
        if template.estado not in ("borrador", "propuesto"):
            raise StudioError(f"No se puede publicar desde el estado '{template.estado}'.")
        if template.resultado_lint is None:
            raise StudioError("Corre el lint de AI-readiness antes de publicar.")
        if not template.resultado_lint.aprobado:
            raise StudioError(
                f"El lint tiene {len(template.resultado_lint.errores)} error(es) "
                "bloqueante(s) — corrígelos antes de publicar."
            )
        if template.resultado_lint.advertencias and not aceptar_advertencias:
            raise StudioError(
                f"El lint tiene {len(template.resultado_lint.advertencias)} "
                "advertencia(s) — acéptalas explícitamente para publicar."
            )

        if template.resultado_lint.advertencias and aceptar_advertencias:
            template.registrar_evento(
                _evento(
                    actor,
                    "advertencias_aceptadas",
                    f"{len(template.resultado_lint.advertencias)} advertencia(s) "
                    "de lint aceptadas al publicar",
                )
            )

        # Retirar la versión publicada anterior del mismo slug (spec §5).
        anterior = self.repo.obtener_publicado_por_slug(template.slug)
        if anterior is not None and anterior.id != template.id:
            anterior.estado = "retirado"
            anterior.registrar_evento(
                _evento(
                    actor,
                    "template_retirado",
                    f"Retirado automáticamente al publicarse v{template.version}",
                    version_sucesora=str(template.version),
                )
            )
            self.repo.guardar(anterior)

        template.estado = "publicado"
        template.registrar_evento(
            _evento(actor, "template_publicado", f"Publicado v{template.version}")
        )
        self.repo.guardar(template)
        return template


@dataclass
class RetirarTemplate:
    """Retira un template publicado: deja de servir para crear documentos nuevos."""

    repo: TemplateDinamicoRepository

    def ejecutar(self, template_id: UUID, actor: str = "default") -> TemplateDinamico:
        template = self.repo.obtener(template_id)
        if template is None:
            raise StudioError("El template no existe.")
        if template.estado != "publicado":
            raise StudioError(f"Solo se retira un template publicado (está '{template.estado}').")
        template.estado = "retirado"
        template.registrar_evento(_evento(actor, "template_retirado", "Retirado por el admin"))
        self.repo.guardar(template)
        return template


@dataclass
class CrearNuevaVersionTemplate:
    """Copia un template publicado/retirado a un borrador v+1 editable."""

    repo: TemplateDinamicoRepository

    def ejecutar(self, template_id: UUID, actor: str = "default") -> TemplateDinamico:
        origen = self.repo.obtener(template_id)
        if origen is None:
            raise StudioError("El template no existe.")
        if origen.estado not in ("publicado", "retirado"):
            raise StudioError(
                "Solo se versiona un template publicado o retirado — un borrador se edita directo."
            )
        nueva = TemplateDinamico(
            slug=origen.slug,
            nombre=origen.nombre,
            descripcion=origen.descripcion,
            area_duena=origen.area_duena,
            version=origen.version + 1,
            secciones=[s.model_copy(deep=True) for s in origen.secciones],
            creado_por=actor,
            archivo_origen=origen.archivo_origen,
        )
        nueva.registrar_evento(
            _evento(
                actor,
                "nueva_version_creada",
                f"Borrador v{nueva.version} creado desde v{origen.version}",
                version_origen=str(origen.version),
            )
        )
        self.repo.guardar(nueva)
        return nueva


@dataclass
class BorrarTemplateBorrador:
    """Borra un template SOLO en estado borrador (spec §11)."""

    repo: TemplateDinamicoRepository

    def ejecutar(self, template_id: UUID) -> None:
        template = self.repo.obtener(template_id)
        if template is None:
            raise StudioError("El template no existe.")
        if template.estado != "borrador":
            raise StudioError("Solo se borran borradores — publica/retira siguen su ciclo.")
        self.repo.borrar(template_id)
