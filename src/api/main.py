"""DocuMente API — entry point.

Run dev:
    uvicorn src.api.main:app --reload --port 8000

Run prod:
    uvicorn src.api.main:app --port 8000 --workers 2

Swagger UI:   http://localhost:8000/docs
ReDoc:        http://localhost:8000/redoc
OpenAPI JSON: http://localhost:8000/openapi.json
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.errors import install_exception_handlers
from src.api.routers import (
    apendices,
    brechas,
    documentos,
    entrevista,
    exportar,
    health,
    importar,
    prophet,
    secciones,
    templates,
    versiones,
)

app = FastAPI(
    title="DocuMente API",
    description=(
        "API REST de DocuMente — sistema agéntico de documentación "
        "institucional para SMNYL. Expone los use cases del dominio "
        "(crear/importar documentos, entrevista LLM, gap analysis, "
        "export DOCX con marca SMNYL, gobernanza MRM, Prophet) sobre "
        "JSON tipado con OpenAPI auto-generado."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "DocuMente — SMNYL",
    },
)

# CORS abierto para desarrollo local — el frontend Next.js correrá en
# localhost:3000 contra esta API en localhost:8000. En prod se restringe
# al dominio del frontend (variable de entorno o hardcoded por env).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

install_exception_handlers(app)

# Registro de routers — el orden importa para los conflictos de paths
# (los más específicos primero, los más generales después).
app.include_router(health.router)
app.include_router(templates.router)
app.include_router(secciones.catalog_router)  # /catalogos/...
app.include_router(prophet.router)
app.include_router(importar.router)  # /documentos/importar (POST)
app.include_router(documentos.router)
app.include_router(secciones.router)
app.include_router(brechas.router)
app.include_router(exportar.router)
app.include_router(entrevista.router)
app.include_router(apendices.router)
app.include_router(versiones.router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    """Redirige implícitamente a /docs vía respuesta informativa."""
    return {
        "api": "documente",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }
