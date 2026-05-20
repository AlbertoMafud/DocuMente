"""Tests del password-gate temporal (`src/ui/components/auth_gate.py`).

Cobertura:
- Gate desactivado cuando env var no está set o vacía.
- Gate activo bloquea hasta password correcto.
- Password incorrecto NO desbloquea.
- Sesión desbloqueada se preserva entre `proteger_app()` calls.
- `is_unlocked()` siempre True si gate desactivado.
"""

from __future__ import annotations

from unittest.mock import patch

from src.ui.components import auth_gate


def test_gate_desactivado_si_env_var_no_existe(monkeypatch) -> None:
    monkeypatch.delenv("DOCUMENTE_GATE_PASSWORD", raising=False)
    assert auth_gate.gate_activo() is False
    assert auth_gate.is_unlocked() is True


def test_gate_desactivado_si_env_var_esta_vacia(monkeypatch) -> None:
    monkeypatch.setenv("DOCUMENTE_GATE_PASSWORD", "")
    assert auth_gate.gate_activo() is False
    assert auth_gate.is_unlocked() is True


def test_gate_desactivado_si_env_var_es_solo_whitespace(monkeypatch) -> None:
    monkeypatch.setenv("DOCUMENTE_GATE_PASSWORD", "   ")
    assert auth_gate.gate_activo() is False


def test_gate_activo_con_password_definida(monkeypatch) -> None:
    monkeypatch.setenv("DOCUMENTE_GATE_PASSWORD", "secreto123")
    assert auth_gate.gate_activo() is True


def test_proteger_app_pasa_directo_si_gate_desactivado(monkeypatch) -> None:
    monkeypatch.delenv("DOCUMENTE_GATE_PASSWORD", raising=False)
    with patch("src.ui.components.auth_gate._renderizar_form_gate") as mock_form:
        resultado = auth_gate.proteger_app()
    assert resultado is True
    mock_form.assert_not_called()


def test_proteger_app_renderiza_form_si_gate_activo_y_no_desbloqueado(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DOCUMENTE_GATE_PASSWORD", "secreto123")
    session: dict[str, object] = {}
    with (
        patch("src.ui.components.auth_gate.st.session_state", session),
        patch("src.ui.components.auth_gate._renderizar_form_gate") as mock_form,
    ):
        resultado = auth_gate.proteger_app()
    assert resultado is False
    mock_form.assert_called_once()


def test_proteger_app_pasa_si_sesion_ya_desbloqueada(monkeypatch) -> None:
    monkeypatch.setenv("DOCUMENTE_GATE_PASSWORD", "secreto123")
    session: dict[str, object] = {"_documente_gate_unlocked": True}
    with (
        patch("src.ui.components.auth_gate.st.session_state", session),
        patch("src.ui.components.auth_gate._renderizar_form_gate") as mock_form,
    ):
        resultado = auth_gate.proteger_app()
    assert resultado is True
    mock_form.assert_not_called()


def test_is_unlocked_falso_si_gate_activo_y_no_desbloqueado(monkeypatch) -> None:
    monkeypatch.setenv("DOCUMENTE_GATE_PASSWORD", "secreto123")
    session: dict[str, object] = {}
    with patch("src.ui.components.auth_gate.st.session_state", session):
        assert auth_gate.is_unlocked() is False


def test_is_unlocked_verdadero_si_gate_activo_pero_desbloqueado(monkeypatch) -> None:
    monkeypatch.setenv("DOCUMENTE_GATE_PASSWORD", "secreto123")
    session: dict[str, object] = {"_documente_gate_unlocked": True}
    with patch("src.ui.components.auth_gate.st.session_state", session):
        assert auth_gate.is_unlocked() is True


def test_render_banner_no_renderiza_si_gate_desactivado(monkeypatch) -> None:
    monkeypatch.delenv("DOCUMENTE_GATE_PASSWORD", raising=False)
    with patch("src.ui.components.auth_gate.st.markdown") as mock_md:
        auth_gate.render_banner_modo_gate()
    mock_md.assert_not_called()


def test_render_banner_renderiza_si_gate_activo(monkeypatch) -> None:
    monkeypatch.setenv("DOCUMENTE_GATE_PASSWORD", "secreto123")
    with patch("src.ui.components.auth_gate.st.markdown") as mock_md:
        auth_gate.render_banner_modo_gate()
    mock_md.assert_called_once()
    args, _kwargs = mock_md.call_args
    assert "acceso controlado" in args[0]
