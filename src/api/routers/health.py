"""Health check + info de la API.

`/healthz` es el endpoint canónico para load balancers (k8s/ALB). No
requiere auth — debe responder rápido y sin tocar BD ni LLM.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = "ok"
    api: str = "documente"
    version: str = "0.1.0"


@router.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    """Liveness probe — siempre devuelve 200 mientras el proceso esté arriba."""
    return HealthResponse()


@router.get("/readyz", response_model=HealthResponse)
def readyz() -> HealthResponse:
    """Readiness probe — extiende healthz con check de dependencias críticas.

    En F1 es equivalente a healthz; cuando agreguemos checks reales (DB,
    LLM client) este endpoint los validará antes de devolver 200.
    """
    return HealthResponse()
