"""MemoriaModelo: hechos transversales del modelo que persisten entre secciones.

Resuelve el problema reportado en la prueba: Claude repetía conceptos básicos
(plataforma, frecuencia, rutas) en cada sección. Ahora esos hechos se capturan
una sola vez (vía onboarding) o se extraen automáticamente (vía
KnowledgeExtractor con Haiku) y se inyectan en el prompt de cada nueva
entrevista como "Hechos ya conocidos del modelo (no preguntes por estos)".
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class MemoriaModelo(BaseModel):
    """Hechos transversales conocidos del modelo, persistidos por documento."""

    model_config = ConfigDict(str_strip_whitespace=True)

    # Hechos estructurados con keys conocidas. Vacío = no capturado.
    plataforma: str = ""
    """Ej. 'Prophet', 'GGY Axis', 'R + AWS'."""
    lenguaje_codigo: str = ""
    """Ej. 'R', 'Python', 'SQL'."""
    frecuencia_corridas: str = ""
    """Ej. 'mensual', 'trimestral', 'ad-hoc por solicitud'."""
    esg_usado: str = ""
    """Ej. 'AAA scenario set 2024', 'ESG corporativo NYL'."""
    rutas_principales: list[str] = Field(default_factory=list)
    """Ej. ['/data/inputs/MPs/', '/aws/s3/bucket-prophet/...']."""
    owner_responsable: str = ""
    """Nombre del Model Owner (puede ya estar en metadata, redundante por seguridad)."""
    fae_responsable: str = ""
    dependencias_upstream: list[str] = Field(default_factory=list)
    """Modelos upstream cuyos outputs alimentan este modelo."""
    dependencias_downstream: list[str] = Field(default_factory=list)
    """Modelos downstream que consumen los outputs de este."""

    # Hechos libres que no encajaron en ninguna key estructurada.
    hechos_libres: list[str] = Field(default_factory=list)

    # Trazabilidad
    actualizada_en: datetime = Field(default_factory=lambda: datetime.now(UTC))
    fuente_ultima_actualizacion: str = ""
    """Ej. 'onboarding', 'extraccion:4.4.assumptions', 'edicion_manual'."""

    @property
    def esta_vacia(self) -> bool:
        """True si no hay ningún hecho capturado (suprime la inyección en prompts)."""
        return (
            not self.plataforma
            and not self.lenguaje_codigo
            and not self.frecuencia_corridas
            and not self.esg_usado
            and not self.rutas_principales
            and not self.owner_responsable
            and not self.fae_responsable
            and not self.dependencias_upstream
            and not self.dependencias_downstream
            and not self.hechos_libres
        )

    def renderizar_para_prompt(self) -> str:
        """Renderiza la memoria como bloque markdown para inyectar en prompts.

        Si está vacía devuelve string vacío para no agregar ruido al prompt.
        """
        if self.esta_vacia:
            return ""

        lineas: list[str] = ["## HECHOS YA CONOCIDOS DEL MODELO (no preguntes por estos)\n"]
        if self.plataforma:
            lineas.append(f"- **Plataforma:** {self.plataforma}")
        if self.lenguaje_codigo:
            lineas.append(f"- **Lenguaje / código:** {self.lenguaje_codigo}")
        if self.frecuencia_corridas:
            lineas.append(f"- **Frecuencia de corridas:** {self.frecuencia_corridas}")
        if self.esg_usado:
            lineas.append(f"- **Generador de escenarios económicos (ESG):** {self.esg_usado}")
        if self.rutas_principales:
            lineas.append("- **Rutas principales:**")
            for r in self.rutas_principales:
                lineas.append(f"  - `{r}`")
        if self.owner_responsable:
            lineas.append(f"- **Model Owner:** {self.owner_responsable}")
        if self.fae_responsable:
            lineas.append(f"- **FAE:** {self.fae_responsable}")
        if self.dependencias_upstream:
            lineas.append(f"- **Dependencias upstream:** {', '.join(self.dependencias_upstream)}")
        if self.dependencias_downstream:
            lineas.append(
                f"- **Dependencias downstream:** {', '.join(self.dependencias_downstream)}"
            )
        if self.hechos_libres:
            lineas.append("- **Otros hechos conocidos:**")
            for h in self.hechos_libres:
                lineas.append(f"  - {h}")
        return "\n".join(lineas)

    def actualizar_desde_dict(self, hechos_nuevos: dict[str, object], fuente: str) -> bool:
        """Hace merge de hechos nuevos en la memoria. Devuelve True si hubo cambios."""
        cambios = False
        scalars = {
            "plataforma": "plataforma",
            "lenguaje_codigo": "lenguaje_codigo",
            "frecuencia_corridas": "frecuencia_corridas",
            "esg_usado": "esg_usado",
            "owner_responsable": "owner_responsable",
            "fae_responsable": "fae_responsable",
        }
        for key, attr in scalars.items():
            valor = hechos_nuevos.get(key)
            if isinstance(valor, str) and valor and not getattr(self, attr):
                setattr(self, attr, valor)
                cambios = True

        for key in ("rutas_principales", "dependencias_upstream", "dependencias_downstream"):
            nuevos = hechos_nuevos.get(key)
            if isinstance(nuevos, list):
                actuales = getattr(self, key)
                for item in nuevos:
                    if isinstance(item, str) and item and item not in actuales:
                        actuales.append(item)
                        cambios = True

        libres = hechos_nuevos.get("hechos_libres")
        if isinstance(libres, list):
            for item in libres:
                if isinstance(item, str) and item and item not in self.hechos_libres:
                    self.hechos_libres.append(item)
                    cambios = True

        if cambios:
            self.actualizada_en = datetime.now(UTC)
            self.fuente_ultima_actualizacion = fuente
        return cambios
