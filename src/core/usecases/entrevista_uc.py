"""Use cases de entrevista.

Capas que orquestan `InterviewEngine` + `Drafter` + persistencia:

- `IniciarEntrevista`: arranca chat sobre una sección.
- `ResponderPregunta`: procesa turno del usuario, persiste estado.
- `CerrarSeccion`: si Claude marcó cerrada, dispara Drafter y guarda borrador.
- `ContinuarEntrevista`: retoma una entrevista en progreso (auto-guardado).
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from uuid import UUID

from src.core.models import EstadoEntrevista
from src.core.usecases.drafter import Drafter
from src.core.usecases.interview_engine import InterviewEngine
from src.core.usecases.knowledge_extractor import KnowledgeExtractor
from src.storage.repositories import (
    DocumentoRepository,
    EstadoEntrevistaRepository,
)


@dataclass
class TurnoEntrevista:
    """Resultado de un turno de la entrevista."""

    estado: EstadoEntrevista
    respuesta_claude: str
    seccion_cerrada: bool
    borrador: str | None = None
    """Si la sección se cerró y el borrador fue suficiente, va aquí."""


class IniciarEntrevista:
    """Arranca o reanuda una entrevista sobre una sección."""

    def __init__(
        self,
        engine: InterviewEngine,
        doc_repo: DocumentoRepository,
        estado_repo: EstadoEntrevistaRepository,
    ) -> None:
        self.engine = engine
        self.doc_repo = doc_repo
        self.estado_repo = estado_repo

    def ejecutar(self, documento_id: UUID, seccion_id: str) -> TurnoEntrevista:
        documento = self.doc_repo.obtener(documento_id)
        if documento is None:
            raise ValueError(f"Documento {documento_id} no encontrado.")
        seccion = documento.seccion_por_id(seccion_id)
        if seccion is None:
            raise ValueError(f"Sección '{seccion_id}' no existe en el documento.")

        # Si ya hay estado en progreso, lo retomamos.
        existente = self.estado_repo.obtener(str(documento_id), seccion_id)
        if existente is not None and existente.mensajes:
            ultima = next(
                (m.contenido for m in reversed(existente.mensajes) if m.rol == "assistant"),
                "",
            )
            return TurnoEntrevista(
                estado=existente,
                respuesta_claude=ultima,
                seccion_cerrada=existente.cerrada,
            )

        # Sin estado previo → arranque fresco
        estado, primera_pregunta = self.engine.iniciar(documento, seccion)
        self.estado_repo.guardar(estado)
        self.doc_repo.guardar(documento)
        return TurnoEntrevista(
            estado=estado,
            respuesta_claude=primera_pregunta,
            seccion_cerrada=False,
        )


class ResponderPregunta:
    """Procesa un turno del usuario, persiste estado, dispara cierre si aplica."""

    def __init__(
        self,
        engine: InterviewEngine,
        drafter: Drafter,
        doc_repo: DocumentoRepository,
        estado_repo: EstadoEntrevistaRepository,
        extractor: KnowledgeExtractor | None = None,
    ) -> None:
        self.engine = engine
        self.drafter = drafter
        self.doc_repo = doc_repo
        self.estado_repo = estado_repo
        self.extractor = extractor

    def ejecutar(
        self,
        documento_id: UUID,
        seccion_id: str,
        respuesta_usuario: str,
    ) -> TurnoEntrevista:
        documento = self.doc_repo.obtener(documento_id)
        if documento is None:
            raise ValueError(f"Documento {documento_id} no encontrado.")
        seccion = documento.seccion_por_id(seccion_id)
        if seccion is None:
            raise ValueError(f"Sección '{seccion_id}' no existe.")
        estado = self.estado_repo.obtener(str(documento_id), seccion_id)
        if estado is None:
            raise ValueError(
                f"No hay entrevista activa para la sección '{seccion_id}'. "
                "Llama a IniciarEntrevista primero."
            )

        estado, respuesta_claude, cerrada = self.engine.responder(
            documento, seccion, estado, respuesta_usuario
        )

        borrador: str | None = None
        if cerrada:
            texto, suficiente = self.drafter.redactar(documento, seccion, estado)
            if suficiente:
                borrador = texto
                # Extraer hechos transversales nuevos para alimentar la memoria
                # del modelo. Best-effort: un fallo no rompe el flujo principal.
                if self.extractor is not None:
                    with contextlib.suppress(Exception):
                        self.extractor.extraer_y_actualizar(documento, seccion, estado)
            else:
                # Reabrimos la entrevista — material insuficiente.
                estado.cerrada = False

        # Persistir todo
        self.estado_repo.guardar(estado)
        self.doc_repo.guardar(documento)

        return TurnoEntrevista(
            estado=estado,
            respuesta_claude=respuesta_claude,
            seccion_cerrada=cerrada and borrador is not None,
            borrador=borrador,
        )
