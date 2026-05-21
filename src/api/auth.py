"""Auth simple para la API: Bearer token reutilizando DOCUMENTE_GATE_PASSWORD.

Si la env var no está definida, la auth queda desactivada (modo dev local).
Mismo patrón que `src/ui/components/auth_gate.py` para consistency.

Pre-Cognito: este token es compartido (no per-user). Cuando se migre a
Cognito real (Fase A.1.c), este módulo se reemplaza con verificación de
JWT desde el ALB header.
"""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_security = HTTPBearer(auto_error=False)


def _expected_token() -> str | None:
    """Lee la password compartida del env. None si auth desactivada."""
    raw = os.environ.get("DOCUMENTE_GATE_PASSWORD", "").strip()
    return raw or None


def require_auth(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_security)],
) -> str:
    """Valida el bearer token contra DOCUMENTE_GATE_PASSWORD.

    Si la env var no está definida (modo dev), permite acceso anónimo y
    devuelve "default" como user_id. En modo prod (env var seteada), exige
    bearer token correcto.
    """
    expected = _expected_token()
    if expected is None:
        # Auth desactivada — modo dev local
        return "default"
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if creds.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return "default"


CurrentUser = Annotated[str, Depends(require_auth)]
