"""Configuración compartida de pytest para DocuMente."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Asegurar que `src` y la raíz del proyecto están en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Forzar que la BD apunte a un archivo de test (no la BD principal)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'data' / 'test.db'}")
