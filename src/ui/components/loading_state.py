"""LoadingState — wrappers de spinner con mensaje contextual obligatorio.

Cumple el principio UX §3 de `UX_PRINCIPLES.md`: cualquier acción larga
muestra spinner con mensaje contextual específico, nunca genérico.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import streamlit as st


@contextmanager
def claude_pensando(accion: str = "Claude está pensando") -> Iterator[None]:
    """Spinner para llamadas al LLM. Mensaje contextual y específico."""
    with st.spinner(f"{accion}…"):
        yield


@contextmanager
def generando_borrador() -> Iterator[None]:
    with st.spinner("Generando borrador profesional con Claude — esto toma 10-25s…"):
        yield
