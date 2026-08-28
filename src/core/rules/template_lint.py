"""Lint de AI-readiness — capa determinística (checks L1-L9).

Lógica pura de dominio: sin BD, sin LLM, sin I/O. Automatiza lo verificable
de docs/TEMPLATE_AIREADY_RULES.md; el criterio de fondo sigue siendo humano
(curación) y la capa 2 (dry-run con LLM) vive en su propio use case.

Severidades (spec §8): los errores BLOQUEAN proponer/publicar; las
advertencias exigen aceptación explícita que queda en el audit trail.
"""

from __future__ import annotations

import re

from src.core.models.template_dinamico import (
    HallazgoLint,
    ResultadoLint,
    SeccionCatalogoDinamica,
)

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

_INTENCIONES_GENERICAS = (
    "descripcion de la seccion",
    "descripción de la sección",
    "seccion del documento",
    "sección del documento",
    "texto libre",
    "contenido de la seccion",
    "contenido de la sección",
)

_MIN_CHARS_INTENCION = 15


def lint_secciones(secciones: list[SeccionCatalogoDinamica]) -> ResultadoLint:
    """Corre los 9 checks determinísticos sobre un catálogo propuesto."""
    hallazgos: list[HallazgoLint] = []

    # L1 — ids únicos, formato slug estable, nunca vacíos.
    vistos: set[str] = set()
    for s in secciones:
        if not s.id.strip():
            hallazgos.append(
                HallazgoLint(
                    codigo="L1",
                    severidad="error",
                    seccion_id=s.numero or s.nombre,
                    mensaje=f"La sección '{s.nombre}' no tiene id.",
                )
            )
            continue
        if s.id in vistos:
            hallazgos.append(
                HallazgoLint(
                    codigo="L1",
                    severidad="error",
                    seccion_id=s.id,
                    mensaje=f"Id duplicado: '{s.id}' aparece en más de una sección.",
                )
            )
        vistos.add(s.id)
        if not _SLUG_RE.match(s.id):
            hallazgos.append(
                HallazgoLint(
                    codigo="L1",
                    severidad="error",
                    seccion_id=s.id,
                    mensaje=(
                        f"Id '{s.id}' no es un slug estable (minúsculas, dígitos, "
                        "'.', '_' o '-'; sin espacios ni mayúsculas)."
                    ),
                )
            )

    # L2 — numeración coherente: presente, sin duplicados, orden consistente.
    numeros = [s.numero.strip() for s in secciones]
    if any(not n for n in numeros):
        hallazgos.append(
            HallazgoLint(
                codigo="L2",
                severidad="error",
                mensaje="Hay secciones sin número jerárquico.",
            )
        )
    else:
        duplicados = {n for n in numeros if numeros.count(n) > 1}
        for n in sorted(duplicados):
            hallazgos.append(
                HallazgoLint(
                    codigo="L2",
                    severidad="error",
                    mensaje=f"Número de sección duplicado: '{n}'.",
                )
            )

        def _clave(numero: str) -> list[int]:
            partes = []
            for p in numero.split("."):
                try:
                    partes.append(int(p))
                except ValueError:
                    partes.append(0)
            return partes

        if numeros != sorted(numeros, key=_clave):
            hallazgos.append(
                HallazgoLint(
                    codigo="L2",
                    severidad="error",
                    mensaje="La numeración no está en orden ascendente respecto a la lista.",
                )
            )

    # L3 — intención no vacía en TODAS las secciones.
    for s in secciones:
        if not s.intencion.strip():
            hallazgos.append(
                HallazgoLint(
                    codigo="L3",
                    severidad="error",
                    seccion_id=s.id,
                    mensaje=f"La sección '{s.nombre}' no declara intención (R2).",
                )
            )

    # L4 — ≥1 pregunta guía en toda sección obligatoria.
    for s in secciones:
        if s.obligatoria and not [p for p in s.preguntas_guia if p.strip()]:
            hallazgos.append(
                HallazgoLint(
                    codigo="L4",
                    severidad="error",
                    seccion_id=s.id,
                    mensaje=f"'{s.nombre}' es obligatoria y no tiene preguntas guía (R3).",
                )
            )

    # L5 — aliases sin colisión entre secciones.
    alias_a_seccion: dict[str, str] = {}
    for s in secciones:
        for alias in s.aliases:
            clave = alias.strip().lower()
            if not clave:
                continue
            if clave in alias_a_seccion and alias_a_seccion[clave] != s.id:
                hallazgos.append(
                    HallazgoLint(
                        codigo="L5",
                        severidad="error",
                        seccion_id=s.id,
                        mensaje=(
                            f"Alias '{alias}' apunta a dos secciones "
                            f"('{alias_a_seccion[clave]}' y '{s.id}') — la importación "
                            "no sabría a cuál mapear (R4)."
                        ),
                    )
                )
            alias_a_seccion.setdefault(clave, s.id)

    # L6 — tipo_contenido tabla exige schema_tabla.
    for s in secciones:
        if s.tipo_contenido == "tabla" and not [c for c in s.schema_tabla if c.strip()]:
            hallazgos.append(
                HallazgoLint(
                    codigo="L6",
                    severidad="error",
                    seccion_id=s.id,
                    mensaje=f"'{s.nombre}' es tipo tabla pero no declara columnas (R6).",
                )
            )

    # L7 — intención sospechosamente corta o genérica (advertencia).
    for s in secciones:
        intencion = s.intencion.strip()
        if not intencion:
            continue  # ya es error L3
        if len(intencion) < _MIN_CHARS_INTENCION or intencion.lower() in _INTENCIONES_GENERICAS:
            hallazgos.append(
                HallazgoLint(
                    codigo="L7",
                    severidad="advertencia",
                    seccion_id=s.id,
                    mensaje=(
                        f"La intención de '{s.nombre}' se ve genérica o demasiado corta — "
                        "prueba R2: tapa el nombre y pregúntate si un experto sabría qué contarte."
                    ),
                )
            )

    # L8 — 0% o 100% de obligatorias (advertencia).
    if secciones:
        obligatorias = sum(1 for s in secciones if s.obligatoria)
        if obligatorias in (0, len(secciones)):
            hallazgos.append(
                HallazgoLint(
                    codigo="L8",
                    severidad="advertencia",
                    mensaje=(
                        f"{obligatorias} de {len(secciones)} secciones obligatorias — "
                        "huele a criterio no aplicado (R5)."
                    ),
                )
            )

    # L9 — sección sin aliases (advertencia).
    for s in secciones:
        if not [a for a in s.aliases if a.strip()]:
            hallazgos.append(
                HallazgoLint(
                    codigo="L9",
                    severidad="advertencia",
                    seccion_id=s.id,
                    mensaje=(
                        f"'{s.nombre}' no tiene aliases — la importación de documentos "
                        "existentes será frágil (R4)."
                    ),
                )
            )

    return ResultadoLint(hallazgos=hallazgos)
