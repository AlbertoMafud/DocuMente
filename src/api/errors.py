"""Mapeo de excepciones del dominio a HTTPException.

Centraliza la traducción para que los routers solo lancen excepciones
naturales del dominio (ej. ValueError, FileNotFoundError, TransicionRechazada)
y aquí las convertimos en respuestas HTTP apropiadas.
"""

from __future__ import annotations

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.core.usecases import TransicionRechazada


def install_exception_handlers(app):  # type: ignore[no-untyped-def]
    """Registra handlers globales en la FastAPI app."""

    @app.exception_handler(ValueError)
    async def _value_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc), "type": "value_error"},
        )

    @app.exception_handler(FileNotFoundError)
    async def _file_not_found(request: Request, exc: FileNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "type": "file_not_found"},
        )

    @app.exception_handler(TransicionRechazada)
    async def _transicion_rechazada(
        request: Request, exc: TransicionRechazada
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": str(exc),
                "type": "transicion_rechazada",
                "razones": list(getattr(exc, "razones", [])),
            },
        )

    @app.exception_handler(PermissionError)
    async def _permission(request: Request, exc: PermissionError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc), "type": "permission_denied"},
        )


def not_found(entidad: str) -> HTTPException:
    """Helper: lanza 404 con mensaje consistente."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{entidad} no encontrado",
    )
