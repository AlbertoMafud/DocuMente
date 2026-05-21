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

import os

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

# CORS configurable por env var CORS_ORIGINS. Default "*" para dev local
# (Next.js en localhost:3000 contra API en localhost:8001). En EC2 prod
# se restringe via .env: ej. CORS_ORIGINS=https://documente.smnyl.local
# Múltiples orígenes separados por coma. Ver docs/HANDOFF_VIDAL.md §5.
_cors_raw = os.environ.get("CORS_ORIGINS", "*")
_allow_origins = (
    ["*"] if _cors_raw == "*" else [o.strip() for o in _cors_raw.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
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
