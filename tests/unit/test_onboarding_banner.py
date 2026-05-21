"""Tests del componente onboarding_banner."""

from __future__ import annotations

from unittest.mock import patch

from src.ui.components import onboarding_banner


def test_render_no_renderiza_si_no_hay_resultado() -> None:
    """Sin clave en session_state, el banner no debe hacer nada."""
    session: dict[str, object] = {}
    with (
        patch("src.ui.components.onboarding_banner.st.session_state", session),
        patch("src.ui.components.onboarding_banner.st.markdown") as mock_md,
        patch("src.ui.components.onboarding_banner.st.expander") as mock_exp,
    ):
        onboarding_banner.render()
    mock_md.assert_not_called()
    mock_exp.assert_not_called()


def test_render_renderiza_y_consume_resultado() -> None:
    """Tras renderizar, la key se borra del session_state (consumo único)."""
    session: dict[str, object] = {
        "onboarding_resultado": {
            "secciones_prellenadas": 4,
            "fuentes_extraidas": 2,
            "llm_disponible": True,
            "advertencias": [],
        }
    }
    with (
        patch("src.ui.components.onboarding_banner.st.session_state", session),
        patch("src.ui.components.onboarding_banner.st.markdown") as mock_md,
    ):
        onboarding_banner.render()
    assert "onboarding_resultado" not in session
    assert mock_md.called
    html = mock_md.call_args[0][0]
    assert "4 sección(es) pre-poblada(s)" in html
    assert "2 fuente(s) cargada(s)" in html


def test_render_brief_y_fuentes_se_suman() -> None:
    """Conteo total = prellenadas (multifuente) + aplicadas (brief)."""
    session: dict[str, object] = {
        "onboarding_resultado": {
            "secciones_prellenadas": 3,
            "fuentes_extraidas": 1,
            "secciones_brief_aplicadas": 5,
            "respuestas_brief_recibidas": 7,
            "llm_disponible": True,
        }
    }
    with (
        patch("src.ui.components.onboarding_banner.st.session_state", session),
        patch("src.ui.components.onboarding_banner.st.markdown") as mock_md,
    ):
        onboarding_banner.render()
    html = mock_md.call_args[0][0]
    assert "8 sección(es) pre-poblada(s)" in html
    # Mostrar desglose
    assert "3 de fuentes + 5 del brief" in html


def test_render_warning_si_llm_no_disponible() -> None:
    session: dict[str, object] = {
        "onboarding_resultado": {
            "secciones_prellenadas": 0,
            "fuentes_extraidas": 2,
            "llm_disponible": False,
            "advertencias": ["IA no disponible"],
        }
    }
    with (
        patch("src.ui.components.onboarding_banner.st.session_state", session),
        patch("src.ui.components.onboarding_banner.st.markdown") as mock_md,
        patch("src.ui.components.onboarding_banner.st.expander") as mock_exp,
    ):
        onboarding_banner.render()
    html = mock_md.call_args_list[0][0][0]
    assert "⚠️" in html
    mock_exp.assert_called_once()


def test_render_expander_para_advertencias_y_descartes() -> None:
    """Si hay advertencias o descartes, se abre el expander."""
    session: dict[str, object] = {
        "onboarding_resultado": {
            "secciones_prellenadas": 1,
            "fuentes_extraidas": 1,
            "llm_disponible": True,
            "advertencias": ["Algo falló"],
            "fuentes_descartadas": ["raro.bin"],
        }
    }
    with (
        patch("src.ui.components.onboarding_banner.st.session_state", session),
        patch("src.ui.components.onboarding_banner.st.markdown") as mock_md,
        patch("src.ui.components.onboarding_banner.st.expander") as mock_exp,
    ):
        # st.expander se usa como context manager — devolver MagicMock con __enter__/__exit__
        mock_exp.return_value.__enter__ = lambda _self: None
        mock_exp.return_value.__exit__ = lambda *_a: None
        onboarding_banner.render()
    assert mock_md.called
    mock_exp.assert_called_once()
