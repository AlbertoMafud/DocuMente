"""DocuMente API — capa REST sobre los use cases del dominio.

Esta capa es la fachada HTTP/JSON que el frontend Next.js consumirá.
No contiene lógica de negocio — solo orquesta DTOs ↔ use cases.

Entry point: `src.api.main:app` (FastAPI instance).
Run dev: `uvicorn src.api.main:app --reload --port 8000`.
"""
