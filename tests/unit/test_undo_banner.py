"""Tests para el banner Deshacer post archivar/papelera (QW#6).

Streamlit's `st.toast` no permite botones, así que la "Undo" pattern
de Gmail se implementa como un banner persistente arriba de la home
con CTA Deshacer + Cerrar.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


class _StreamlitState(dict):
    """Sustituto mínimo de `st.session_state` que se comporta como dict + attribute."""

    def __getattr__(self, item: str):  # noqa: D401
        try:
            return self[item]
        except KeyError as e:
            raise AttributeError(item) from e

    def __setattr__(self, key: str, value: object) -> None:
        self[key] = value


@pytest.fixture
def fake_session_state(monkeypatch: pytest.MonkeyPatch) -> _StreamlitState:
    import streamlit as st

    state = _StreamlitState()
    monkeypatch.setattr(st, "session_state", state)
    return state


class TestSetUndoVisibilidad:
    """`_set_undo_visibilidad` deposita la acción reversible en session_state."""

    def test_archivar_guarda_tipo_y_doc_id(self, fake_session_state: _StreamlitState) -> None:
        from app import _set_undo_visibilidad

        doc_id = uuid4()
        _set_undo_visibilidad(tipo="archivar", doc_id=doc_id, nombre="Modelo X")
        assert fake_session_state["undo_visibilidad"]["tipo"] == "archivar"
        assert fake_session_state["undo_visibilidad"]["doc_id"] == str(doc_id)
        assert fake_session_state["undo_visibilidad"]["nombre"] == "Modelo X"

    def test_papelera_guarda_tipo_papelera(self, fake_session_state: _StreamlitState) -> None:
        from app import _set_undo_visibilidad

        _set_undo_visibilidad(tipo="papelera", doc_id=uuid4(), nombre="Modelo Y")
        assert fake_session_state["undo_visibilidad"]["tipo"] == "papelera"


class TestRenderUndoBanner:
    """`_render_undo_banner` renderiza el banner solo si hay una acción pendiente."""

    def test_sin_accion_no_renderiza_nada(self, fake_session_state: _StreamlitState) -> None:
        from app import _render_undo_banner

        captured: list[str] = []
        with (
            patch("streamlit.markdown", side_effect=lambda h, **_: captured.append(h)),
            patch("streamlit.columns") as cols_mock,
            patch("streamlit.button") as btn_mock,
        ):
            _render_undo_banner(MagicMock(), "default")
        # Si no hay undo_action, no se debe haber llamado markdown ni columns
        assert captured == []
        cols_mock.assert_not_called()
        btn_mock.assert_not_called()

    def test_con_accion_renderiza_nombre_y_botones(
        self, fake_session_state: _StreamlitState
    ) -> None:
        from app import _render_undo_banner

        fake_session_state["undo_visibilidad"] = {
            "tipo": "archivar",
            "doc_id": str(uuid4()),
            "nombre": "Modelo VNB GMM",
        }
        captured: list[str] = []

        class _StubCol:
            def __enter__(self):  # type: ignore[no-untyped-def]
                return self

            def __exit__(self, *args):  # type: ignore[no-untyped-def]
                return False

        with (
            patch("streamlit.markdown", side_effect=lambda h, **_: captured.append(h)),
            patch("streamlit.columns", return_value=(_StubCol(), _StubCol(), _StubCol())),
            patch("streamlit.button", return_value=False),
        ):
            _render_undo_banner(MagicMock(), "default")
        html = "".join(captured)
        # El nombre del doc debe aparecer en el banner
        assert "Modelo VNB GMM" in html
        # Y debe describir la acción (archivado)
        assert "archivado" in html.lower()

    def test_papelera_muestra_mensaje_papelera(
        self, fake_session_state: _StreamlitState
    ) -> None:
        from app import _render_undo_banner

        fake_session_state["undo_visibilidad"] = {
            "tipo": "papelera",
            "doc_id": str(uuid4()),
            "nombre": "Modelo Z",
        }
        captured: list[str] = []

        class _StubCol:
            def __enter__(self):  # type: ignore[no-untyped-def]
                return self

            def __exit__(self, *args):  # type: ignore[no-untyped-def]
                return False

        with (
            patch("streamlit.markdown", side_effect=lambda h, **_: captured.append(h)),
            patch("streamlit.columns", return_value=(_StubCol(), _StubCol(), _StubCol())),
            patch("streamlit.button", return_value=False),
        ):
            _render_undo_banner(MagicMock(), "default")
        html = "".join(captured).lower()
        assert "papelera" in html
        assert "modelo z" in html
