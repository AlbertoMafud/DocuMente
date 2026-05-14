"""Tests del componente back_button."""

from __future__ import annotations

from unittest.mock import patch

from src.ui.components import back_button


def test_render_no_clickeado_no_cambia_pagina() -> None:
    """Si el usuario no hace click, no se debe modificar la página actual."""
    session = {"pagina": "importar"}
    with (
        patch("src.ui.components.back_button.st.button", return_value=False),
        patch("src.ui.components.back_button.st.session_state", session),
        patch("src.ui.components.back_button.st.rerun") as mock_rerun,
    ):
        clicked = back_button.render(destino="home")

    assert clicked is False
    assert session["pagina"] == "importar"
    mock_rerun.assert_not_called()


def test_render_clickeado_cambia_pagina_y_dispara_rerun() -> None:
    """Click → session_state['pagina'] = destino + rerun."""
    session = {"pagina": "importar"}
    with (
        patch("src.ui.components.back_button.st.button", return_value=True),
        patch("src.ui.components.back_button.st.session_state", session),
        patch("src.ui.components.back_button.st.rerun") as mock_rerun,
    ):
        clicked = back_button.render(destino="home")

    assert clicked is True
    assert session["pagina"] == "home"
    mock_rerun.assert_called_once()


def test_render_destino_personalizado() -> None:
    """`destino` controla exactamente a qué página redirige."""
    session = {"pagina": "auditoria"}
    with (
        patch("src.ui.components.back_button.st.button", return_value=True),
        patch("src.ui.components.back_button.st.session_state", session),
        patch("src.ui.components.back_button.st.rerun"),
    ):
        back_button.render(destino="dashboard")

    assert session["pagina"] == "dashboard"


def test_render_genera_key_automatica_si_no_se_pasa() -> None:
    """Sin `key` explícito, se genera uno a partir de destino+etiqueta para
    evitar colisión cuando hay múltiples back buttons en la misma pantalla."""
    with (
        patch("src.ui.components.back_button.st.button", return_value=False) as mock_button,
        patch("src.ui.components.back_button.st.session_state", {}),
    ):
        back_button.render(destino="home", etiqueta="← Volver")

    _, kwargs = mock_button.call_args
    assert "key" in kwargs
    assert kwargs["key"]  # no vacío


def test_render_key_explicito_se_respeta() -> None:
    """Si el caller pasa `key`, se usa tal cual (sin sufijo automático)."""
    with (
        patch("src.ui.components.back_button.st.button", return_value=False) as mock_button,
        patch("src.ui.components.back_button.st.session_state", {}),
    ):
        back_button.render(destino="home", key="mi_back_custom")

    _, kwargs = mock_button.call_args
    assert kwargs["key"] == "mi_back_custom"
