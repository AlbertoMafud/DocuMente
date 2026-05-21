"""Password-gate temporal para proteger la app mientras se integra Cognito real.

Mitigación de emergencia para el problema #8 (multi-tenant): bloquea el
acceso público a la app cuando se despliega en EC2 sin auth real todavía.
Se desactiva eliminando la env var `DOCUMENTE_GATE_PASSWORD`.

Comportamiento:
- Si `DOCUMENTE_GATE_PASSWORD` no está definida o está vacía → gate desactivado
  (modo local dev), `is_unlocked()` retorna True directo.
- Si está definida → el usuario debe ingresar el password correcto en la
  primera visita; tras un match exitoso, se marca la sesión como desbloqueada.

Este gate es una capa de defensa por contraseña compartida — NO sustituye
auth por usuario. Solo bloquea acceso público. Para multi-tenant real, ver
`src/ui/auth.py` (Fase A.1.c).
"""

from __future__ import annotations

import os

import streamlit as st

from src.ui.theme import SMNYL_COLORS

_SESSION_KEY = "_documente_gate_unlocked"
_ENV_VAR = "DOCUMENTE_GATE_PASSWORD"


def _password_configurado() -> str | None:
    """Devuelve el password del env si está definido y no vacío; None si no."""
    valor = os.environ.get(_ENV_VAR, "").strip()
    return valor or None


def gate_activo() -> bool:
    """True si el gate está activo (env var set y no vacía)."""
    return _password_configurado() is not None


def is_unlocked() -> bool:
    """True si la sesión actual está desbloqueada (o el gate no está activo)."""
    if not gate_activo():
        return True
    return bool(st.session_state.get(_SESSION_KEY, False))


def _renderizar_form_gate() -> None:
    """Renderiza la pantalla de password con marca SMNYL."""
    st.markdown(
        f"""
        <div style="
            max-width: 480px;
            margin: 4rem auto 2rem auto;
            padding: 2.5rem;
            background-color: {SMNYL_COLORS["bg"]};
            border: 1px solid {SMNYL_COLORS["border"]};
            border-radius: 12px;
            box-shadow: 0 12px 32px rgba(10, 60, 83, 0.12);
        ">
            <h1 style="
                font-family: var(--font-display);
                color: {SMNYL_COLORS["text"]};
                font-size: 1.75rem;
                margin-bottom: 0.5rem;
            ">DocuMente — acceso restringido</h1>
            <p style="
                color: {SMNYL_COLORS["text_muted"]};
                font-size: 0.95rem;
                margin-bottom: 1.5rem;
                line-height: 1.55;
            ">Esta app está en periodo de piloto controlado. Ingresa el
            password compartido para continuar.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    contenedor_form = st.container()
    with contenedor_form:
        _, col_form, _ = st.columns([1, 2, 1])
        with col_form:
            with st.form("documente_gate_form", clear_on_submit=False):
                password_input = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Ingresa el password compartido",
                    label_visibility="collapsed",
                )
                submit = st.form_submit_button(
                    "Entrar",
                    type="primary",
                    use_container_width=True,
                )

            if submit:
                esperado = _password_configurado()
                if esperado is not None and password_input == esperado:
                    st.session_state[_SESSION_KEY] = True
                    st.rerun()
                else:
                    st.error("Password incorrecto. Verifica con el equipo de DocuMente.")


def render_banner_modo_gate() -> None:
    """Banner pequeño que indica que el gate está activo.

    Se llama desde el header de las páginas para que sea obvio cuándo la app
    está en modo password-gate temporal vs auth real (post Cognito).
    """
    if not gate_activo():
        return
    st.markdown(
        f"""
        <div style="
            background-color: {SMNYL_COLORS["accent_soft"]};
            color: {SMNYL_COLORS["primary_dark"]};
            font-size: 0.8rem;
            padding: 4px 12px;
            border-radius: 4px;
            display: inline-block;
            margin-bottom: 8px;
            font-family: var(--font-body);
        ">Modo acceso controlado — autenticación temporal por password</div>
        """,
        unsafe_allow_html=True,
    )


def proteger_app() -> bool:
    """Llama al inicio del router en `app.py`.

    Devuelve True si la app debe continuar (gate desactivado o sesión
    desbloqueada). Devuelve False si se renderizó el form de password
    (en cuyo caso el caller debe retornar inmediatamente sin renderizar
    nada más).

    Patrón de uso en `app.py`::

        if not proteger_app():
            return
        # ... resto del router
    """
    if is_unlocked():
        return True
    _renderizar_form_gate()
    return False
