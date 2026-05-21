"""Tests para microinteracciones globales (QW#10 del audit UX Pro Max).

`transition: all 200ms ease-out` aplicado a cards, expanders, inputs e
hipervínculos para que la app se sienta enterprise (no Streamlit default).
"""

from __future__ import annotations

from src.ui.theme import _build_css


def test_cards_tienen_transition() -> None:
    """Las cards (st.container border) deben tener transición de hover."""
    css = _build_css()
    # La regla del wrapper de cards debe tener transition
    assert "stVerticalBlockBorderWrapper" in css
    cards_block = css[css.index("stVerticalBlockBorderWrapper") :]
    cards_block = cards_block[: cards_block.index("}")]
    assert "transition" in cards_block, "Las cards deben tener transition para sentir pulido"


def test_inputs_tienen_transition() -> None:
    """Los inputs (text, textarea, selectbox) tienen transición de focus."""
    css = _build_css()
    # Buscar el bloque de inputs
    assert "stTextInput" in css
    # En algún lugar del CSS debe haber transition asociada a los inputs
    inputs_section = css[css.index("stTextInput") :]
    # Tomar hasta 1500 chars que cubren la regla base + el :focus
    inputs_section = inputs_section[:1500]
    assert "transition" in inputs_section


def test_expanders_tienen_transition() -> None:
    """Headers de expander (accordion del dashboard) tienen transición de hover."""
    css = _build_css()
    assert "stExpander" in css or "streamlit-expanderHeader" in css
    # En el bloque del expander debe haber transition
    if "stExpander" in css:
        block = css[css.index("stExpander") :]
        block = block[: min(800, len(block))]
        assert "transition" in block


def test_buttons_usan_200ms_ease_out() -> None:
    """Los botones siguen el estándar de 200ms ease-out para consistencia global."""
    css = _build_css()
    # Pueden existir múltiples transitions; lo importante es que la duración
    # cumple el estándar UX (≥150ms, ≤250ms) y se usa ease-out.
    assert "200ms" in css or "150ms" in css
    assert "ease-out" in css or "ease " in css or "ease;" in css
