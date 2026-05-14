"""DocxWriterProphet — genera un .docx a partir de un Documento tipo 'prophet'.

Usa docxtpl (template-driven) para respetar la marca SMNYL definida en la
plantilla Word maestra. El writer solo construye el contexto Jinja2 y delega
el rendering al motor de docxtpl.
"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate

from src.core.models import Documento

_TEMPLATE_DEFAULT = (
    Path(__file__).parent.parent.parent / "docs" / "templates" / "prophet_model_doc_smnyl.docx"
)

# Mapeo: (id de sección en el Documento, clave en el contexto Jinja2)
_TABLA_MAP: list[tuple[str, str]] = [
    ("corridas_runs", "runs"),
    ("variables_criticas", "variables"),
    ("inputs_dependencias", "inputs"),
    ("responsables_roles", "responsables"),
    ("outputs_reportes", "outputs"),
    ("historial_cambios", "historial"),
    ("matriz_conocimiento", "skills_matrix"),
]


class DocxWriterProphet:
    """Convierte un Documento Prophet a bytes DOCX usando una plantilla Word."""

    def __init__(self, template_path: Path | None = None) -> None:
        self.template_path = template_path or _TEMPLATE_DEFAULT

    def render(self, documento: Documento) -> bytes:
        """Renderiza el documento y devuelve los bytes del .docx resultante.

        Raises:
            FileNotFoundError: Si la plantilla Word no existe en la ruta configurada.
        """
        if not self.template_path.exists():
            raise FileNotFoundError(
                f"Template Prophet no encontrado: {self.template_path}. "
                "Crea el archivo en Word siguiendo la guía del spec."
            )
        tpl = DocxTemplate(str(self.template_path))
        context = self._construir_contexto(documento)
        tpl.render(context)
        buf = BytesIO()
        tpl.save(buf)
        return buf.getvalue()

    def _construir_contexto(self, documento: Documento) -> dict[str, Any]:
        """Construye el diccionario de contexto Jinja2 para el template."""
        meta = documento.metadata_modelo
        ctx: dict[str, Any] = {
            "nombre_modelo": meta.nombre_modelo,
            "model_id": meta.model_id,
            "area": "",
            "proceso": "",
            "encargado_principal": "",
            "frecuencia_uso": "",
            "ruta_modelo": "",
            "tiempo_ejecucion": "",
            "objetivo": "",
            "supuestos": "",
            "componentes": "",
            "limitaciones": "",
        }

        # Sección 1: Identificación (campos estructurados)
        s_id = documento.seccion_por_id("identificacion")
        if s_id and s_id.contenido:
            try:
                data = json.loads(s_id.contenido)
                raw = data.get("contenido", "{}")
                campos = json.loads(raw) if isinstance(raw, str) else raw
                ctx["area"] = campos.get("Area", campos.get("area", ""))
                ctx["proceso"] = campos.get("Proceso", campos.get("proceso", ""))
                ctx["encargado_principal"] = campos.get(
                    "Encargado", campos.get("encargado", "")
                )
                ctx["frecuencia_uso"] = campos.get(
                    "Frecuencia de actualización", campos.get("frecuencia_uso", "")
                )
            except (json.JSONDecodeError, AttributeError):
                pass

        # Secciones de texto libre
        for seccion_id, ctx_key in [
            ("objetivo_alcance", "objetivo"),
            ("supuestos", "supuestos"),
            ("componentes_librerias", "componentes"),
            ("limitaciones_riesgos", "limitaciones"),
        ]:
            s = documento.seccion_por_id(seccion_id)
            if s and s.contenido:
                try:
                    data = json.loads(s.contenido)
                    ctx[ctx_key] = data.get("contenido", s.contenido)
                except json.JSONDecodeError:
                    ctx[ctx_key] = s.contenido

        # Secciones de tabla — devuelven lista de dicts (filas)
        for seccion_id, ctx_key in _TABLA_MAP:
            s = documento.seccion_por_id(seccion_id)
            if s and s.contenido:
                try:
                    data = json.loads(s.contenido)
                    ctx[ctx_key] = data.get("filas", []) if isinstance(data, dict) else data
                except json.JSONDecodeError:
                    ctx[ctx_key] = []
            else:
                ctx[ctx_key] = []

        return ctx
