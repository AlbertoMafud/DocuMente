"""Tests de la lógica de inferencia de destinos del header (breadcrumbs clickeables)."""

from __future__ import annotations

from unittest.mock import patch

from src.ui.components.header import _inferir_destinos


def test_breadcrumb_inicio_va_a_home() -> None:
    with patch("src.ui.components.header.st.session_state", {}):
        destinos = _inferir_destinos(["Inicio", "Importar"])
    assert destinos == ["home", None]


def test_ultimo_breadcrumb_no_es_clickeable() -> None:
    with patch("src.ui.components.header.st.session_state", {}):
        destinos = _inferir_destinos(["Inicio", "Importar"])
    assert destinos[-1] is None


def test_segundo_breadcrumb_va_a_dashboard_si_hay_doc_actual() -> None:
    """Caso típico: ['Inicio', 'modelo X', 'Sección Y'] con doc actual."""
    session = {"documento_actual_id": "abc-123"}
    with patch("src.ui.components.header.st.session_state", session):
        destinos = _inferir_destinos(["Inicio", "Modelo X", "Sección Y"])
    assert destinos == ["home", "dashboard", None]


def test_segundo_breadcrumb_no_va_a_dashboard_sin_doc_actual() -> None:
    """Sin doc actual en session, el segundo no es clickeable."""
    with patch("src.ui.components.header.st.session_state", {}):
        destinos = _inferir_destinos(["Inicio", "Algo", "Otra"])
    assert destinos == ["home", None, None]


def test_breadcrumb_solo_un_item_es_current() -> None:
    """Un solo breadcrumb = solo current, no clickeable."""
    with patch("src.ui.components.header.st.session_state", {}):
        destinos = _inferir_destinos(["Solo"])
    assert destinos == [None]


def test_dos_breadcrumbs_no_activan_dashboard_intermedio() -> None:
    """Con solo 2 niveles (Inicio + current), no hay intermedio para 'dashboard'."""
    session = {"documento_actual_id": "abc-123"}
    with patch("src.ui.components.header.st.session_state", session):
        destinos = _inferir_destinos(["Inicio", "Final"])
    assert destinos == ["home", None]


def test_home_minuscula_tambien_va_a_home() -> None:
    """La auto-inferencia es case-insensitive para 'inicio'/'home'."""
    with patch("src.ui.components.header.st.session_state", {}):
        destinos = _inferir_destinos(["home", "Sección"])
    assert destinos == ["home", None]
