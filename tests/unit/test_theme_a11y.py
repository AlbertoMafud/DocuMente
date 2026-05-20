"""Tests para los 5 fixes de accesibilidad WCAG 2.1 AA.

Cubre:
- Tokens dark (`success_dark`, `warning_dark`, `info_dark`) en `theme.py`.
- Cálculo de contrast ratio sRGB y verificación AA (≥4.5:1) para texto sobre blanco.
- Uso de los tokens dark como color de texto en `gap_badge`, `seccion_card`, `timeline`.

Referencia: docs/superpowers/specs/2026-05-19-accessibility-audit.md §1.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from src.core.models import EventoAuditoria, Seccion
from src.ui.components import gap_badge, seccion_card, timeline
from src.ui.theme import SMNYL_COLORS


def _luminance(hex_color: str) -> float:
    """Calcula relative luminance sRGB según WCAG 2.1."""
    hex_clean = hex_color.lstrip("#")
    r, g, b = (int(hex_clean[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def _channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def _contrast_ratio(fg: str, bg: str) -> float:
    """Ratio de contraste entre dos colores hex según WCAG 2.1."""
    l1 = _luminance(fg)
    l2 = _luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# --- Tokens existen ---


class TestTokensDarkExisten:
    """Los 3 tokens dark deben existir en SMNYL_COLORS."""

    def test_success_dark_existe(self) -> None:
        assert "success_dark" in SMNYL_COLORS

    def test_warning_dark_existe(self) -> None:
        assert "warning_dark" in SMNYL_COLORS

    def test_info_dark_existe(self) -> None:
        assert "info_dark" in SMNYL_COLORS


# --- Valores hex correctos (del manual SMNYL paleta dark) ---


class TestValoresHexCorrectos:
    """Los hex de los tokens dark vienen del manual SMNYL paleta dark."""

    def test_success_dark_es_dark_pine(self) -> None:
        # Dark Pine del manual SMNYL
        assert SMNYL_COLORS["success_dark"].lower() == "#264640"

    def test_warning_dark_es_dark_sunset(self) -> None:
        # Dark Sunset del manual SMNYL
        assert SMNYL_COLORS["warning_dark"].lower() == "#544235"

    def test_info_dark_es_dark_rain(self) -> None:
        # Dark Rain — coincide con primary_dark
        assert SMNYL_COLORS["info_dark"].lower() == "#0a385e"


# --- WCAG AA (≥4.5:1 vs blanco para texto normal) ---


class TestContrasteAA:
    """Cada token dark debe pasar WCAG 2.1 AA como texto sobre blanco (≥4.5:1)."""

    def test_success_dark_pasa_aa(self) -> None:
        ratio = _contrast_ratio(SMNYL_COLORS["success_dark"], "#ffffff")
        assert ratio >= 4.5, f"success_dark contrast ratio {ratio:.2f}:1 < 4.5"

    def test_warning_dark_pasa_aa(self) -> None:
        ratio = _contrast_ratio(SMNYL_COLORS["warning_dark"], "#ffffff")
        assert ratio >= 4.5, f"warning_dark contrast ratio {ratio:.2f}:1 < 4.5"

    def test_info_dark_pasa_aa(self) -> None:
        ratio = _contrast_ratio(SMNYL_COLORS["info_dark"], "#ffffff")
        assert ratio >= 4.5, f"info_dark contrast ratio {ratio:.2f}:1 < 4.5"

    def test_warning_dark_pasa_aa_sobre_warning_soft(self) -> None:
        # gap_badge "media" usa color sobre warning_soft (#fdf4ee)
        ratio = _contrast_ratio(SMNYL_COLORS["warning_dark"], "#fdf4ee")
        assert ratio >= 4.5, f"warning_dark sobre warning_soft {ratio:.2f}:1 < 4.5"

    def test_info_dark_pasa_aa_sobre_info_soft(self) -> None:
        # gap_badge "baja" usa color sobre info_soft (#eef6fb)
        ratio = _contrast_ratio(SMNYL_COLORS["info_dark"], "#eef6fb")
        assert ratio >= 4.5, f"info_dark sobre info_soft {ratio:.2f}:1 < 4.5"


# --- CSS expone los tokens dark como variables ---


class TestCssExponeTokensDark:
    """El CSS inyectado en `:root` debe declarar las CSS variables dark."""

    def test_css_declara_variables_dark(self) -> None:
        from src.ui.theme import _build_css

        css = _build_css()
        assert "--color-success-dark:" in css
        assert "--color-warning-dark:" in css
        assert "--color-info-dark:" in css


# --- gap_badge usa _dark como color de texto ---


class TestGapBadgeUsaDark:
    """`media` y `baja` deben usar las variantes dark para el color de texto."""

    def test_severidad_media_usa_warning_dark_como_texto(self) -> None:
        html_captured: list[str] = []
        with patch("streamlit.markdown", side_effect=lambda html, **_k: html_captured.append(html)):
            gap_badge.render("media")
        html = html_captured[0]
        assert f"color: {SMNYL_COLORS['warning_dark']}" in html
        assert SMNYL_COLORS["warning"] not in re.findall(r"color:\s*([^;]+);", html)[0]

    def test_severidad_baja_usa_info_dark_como_texto(self) -> None:
        html_captured: list[str] = []
        with patch("streamlit.markdown", side_effect=lambda html, **_k: html_captured.append(html)):
            gap_badge.render("baja")
        html = html_captured[0]
        assert f"color: {SMNYL_COLORS['info_dark']}" in html

    def test_severidad_alta_sigue_usando_danger(self) -> None:
        # danger ya pasa AA (7.21:1) — no se cambia
        html_captured: list[str] = []
        with patch("streamlit.markdown", side_effect=lambda html, **_k: html_captured.append(html)):
            gap_badge.render("alta")
        html = html_captured[0]
        assert f"color: {SMNYL_COLORS['danger']}" in html


# --- seccion_card usa _dark como color de texto del label ---


def _seccion(completitud: str) -> Seccion:
    return Seccion(
        id="1.1.background",
        numero="1.1",
        nombre="Background del modelo",
        contenido="contenido demo",
        completitud=completitud,  # type: ignore[arg-type]
        obligatoria=True,
    )


class TestSeccionCardUsaDark:
    """El texto del label (Completa/Parcial) usa el variant dark."""

    def test_completa_label_usa_success_dark(self) -> None:
        captured: list[str] = []

        class _StubCtx:
            def __enter__(self):  # type: ignore[no-untyped-def]
                return self

            def __exit__(self, *args):  # type: ignore[no-untyped-def]
                return False

        with (
            patch("streamlit.markdown", side_effect=lambda html, **_k: captured.append(html)),
            patch("streamlit.container", return_value=_StubCtx()),
        ):
            seccion_card.render(_seccion("completa"))
        html = "".join(captured)
        # El label "Completa" debe llevar success_dark como color
        assert f"color: {SMNYL_COLORS['success_dark']}" in html

    def test_parcial_label_usa_warning_dark(self) -> None:
        captured: list[str] = []

        class _StubCtx:
            def __enter__(self):  # type: ignore[no-untyped-def]
                return self

            def __exit__(self, *args):  # type: ignore[no-untyped-def]
                return False

        with (
            patch("streamlit.markdown", side_effect=lambda html, **_k: captured.append(html)),
            patch("streamlit.container", return_value=_StubCtx()),
        ):
            seccion_card.render(_seccion("parcial"))
        html = "".join(captured)
        assert f"color: {SMNYL_COLORS['warning_dark']}" in html

    def test_vacia_label_sigue_usando_danger(self) -> None:
        # danger ya pasa AA, no se cambia
        captured: list[str] = []

        class _StubCtx:
            def __enter__(self):  # type: ignore[no-untyped-def]
                return self

            def __exit__(self, *args):  # type: ignore[no-untyped-def]
                return False

        with (
            patch("streamlit.markdown", side_effect=lambda html, **_k: captured.append(html)),
            patch("streamlit.container", return_value=_StubCtx()),
        ):
            seccion_card.render(_seccion("vacia"))
        html = "".join(captured)
        assert f"color: {SMNYL_COLORS['danger']}" in html

    def test_completa_dot_usa_success_original(self) -> None:
        # El dot (background) puede mantener el color original (3:1 OK para UI)
        captured: list[str] = []

        class _StubCtx:
            def __enter__(self):  # type: ignore[no-untyped-def]
                return self

            def __exit__(self, *args):  # type: ignore[no-untyped-def]
                return False

        with (
            patch("streamlit.markdown", side_effect=lambda html, **_k: captured.append(html)),
            patch("streamlit.container", return_value=_StubCtx()),
        ):
            seccion_card.render(_seccion("completa"))
        html = "".join(captured)
        # El background del dot pequeño usa el color original (success)
        assert f"background: {SMNYL_COLORS['success']}" in html


# --- timeline usa _dark como color del label de tipo ---


def _evento(tipo: str) -> EventoAuditoria:
    return EventoAuditoria(
        tipo=tipo,  # type: ignore[arg-type]
        timestamp=datetime.now(UTC),
        actor="alberto@smnyl.com",
        descripcion="Acción de prueba para el timeline.",
    )


class TestTimelineUsaDark:
    """Eventos con success/warning/info usan _dark como color de TEXTO del tipo."""

    def test_seccion_editada_texto_usa_success_dark(self) -> None:
        captured: list[str] = []
        with patch("streamlit.markdown", side_effect=lambda html, **_k: captured.append(html)):
            timeline.render([_evento("seccion_editada")])
        html = "".join(captured)
        assert f"color:{SMNYL_COLORS['success_dark']}" in html.replace(" ", "")

    def test_exportado_texto_usa_info_dark(self) -> None:
        captured: list[str] = []
        with patch("streamlit.markdown", side_effect=lambda html, **_k: captured.append(html)):
            timeline.render([_evento("exportado")])
        html = "".join(captured)
        assert f"color:{SMNYL_COLORS['info_dark']}" in html.replace(" ", "")

    def test_signoff_reviewer_texto_usa_warning_dark(self) -> None:
        captured: list[str] = []
        with patch("streamlit.markdown", side_effect=lambda html, **_k: captured.append(html)):
            timeline.render([_evento("signoff_reviewer")])
        html = "".join(captured)
        assert f"color:{SMNYL_COLORS['warning_dark']}" in html.replace(" ", "")

    def test_marcador_dot_mantiene_color_original(self) -> None:
        # El dot del marker (background) puede mantener el color original (UI component, 3:1)
        captured: list[str] = []
        with patch("streamlit.markdown", side_effect=lambda html, **_k: captured.append(html)):
            timeline.render([_evento("seccion_editada")])
        html = "".join(captured)
        # El marcador usa el color success (no dark) como background
        assert f"background:{SMNYL_COLORS['success']}" in html.replace(" ", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
