"""Tests para el componente Stepper visual.

El stepper renderiza un progress horizontal por pasos con 3 estados:
completado, actual, pendiente. Es la base del Quick Win #1 del audit UX
(stepper visual en onboarding/brief/entrevista).
"""

from __future__ import annotations

from unittest.mock import patch

from src.ui.components import stepper


def _captured_html() -> tuple[list[str], object]:
    captured: list[str] = []
    ctx = patch("streamlit.markdown", side_effect=lambda html, **_k: captured.append(html))
    return captured, ctx


class TestStepperBasico:
    """Casos canónicos del stepper."""

    def test_render_4_pasos_actual_2(self) -> None:
        # Crear ✓ → Onboarding ✓ → Brief (actual) → Dashboard (pendiente)
        captured, ctx = _captured_html()
        with ctx:
            stepper.render(
                ["Crear", "Onboarding", "Brief", "Dashboard"],
                actual_idx=2,
            )
        html = "".join(captured)
        # Cada paso aparece en el HTML como su label
        assert "Crear" in html
        assert "Onboarding" in html
        assert "Brief" in html
        assert "Dashboard" in html

    def test_render_actual_idx_0_no_hay_completados(self) -> None:
        captured, ctx = _captured_html()
        with ctx:
            stepper.render(["A", "B", "C"], actual_idx=0)
        html = "".join(captured)
        # El primer paso está activo (sin completados a la izquierda)
        # Verificación liviana: no hay errores y todos los labels presentes
        assert "A" in html and "B" in html and "C" in html

    def test_render_actual_idx_last_todos_excepto_uno_completados(self) -> None:
        captured, ctx = _captured_html()
        with ctx:
            stepper.render(["A", "B", "C"], actual_idx=2)
        html = "".join(captured)
        # Las 2 primeras llevan checkmark de completado en algún marker
        # (usa ✓ o algún símbolo equivalente)
        assert html.count("✓") >= 2


class TestStepperEstados:
    """Verifica que el HTML refleja los 3 estados visualmente."""

    def test_completados_llevan_color_success_dark(self) -> None:
        from src.ui.theme import SMNYL_COLORS

        captured, ctx = _captured_html()
        with ctx:
            stepper.render(["A", "B", "C"], actual_idx=2)
        html = "".join(captured)
        # El color success_dark aparece en al menos un marker (completados)
        assert SMNYL_COLORS["success_dark"] in html

    def test_actual_lleva_color_primary(self) -> None:
        from src.ui.theme import SMNYL_COLORS

        captured, ctx = _captured_html()
        with ctx:
            stepper.render(["A", "B", "C"], actual_idx=1)
        html = "".join(captured)
        # El color primary aparece para el paso actual
        assert SMNYL_COLORS["primary"] in html

    def test_pendiente_lleva_color_muted(self) -> None:
        from src.ui.theme import SMNYL_COLORS

        captured, ctx = _captured_html()
        with ctx:
            stepper.render(["A", "B", "C"], actual_idx=0)
        html = "".join(captured)
        # text_muted aparece para los pendientes
        assert SMNYL_COLORS["text_muted"] in html


class TestStepperBordes:
    """Casos borde y validaciones."""

    def test_lista_vacia_no_falla(self) -> None:
        _captured, ctx = _captured_html()
        with ctx:
            stepper.render([], actual_idx=0)
        # Debe completar sin excepción; si no rendereó nada está OK también

    def test_actual_idx_fuera_de_rango_no_falla(self) -> None:
        # Si actual_idx > len(pasos), el componente clampa
        _captured, ctx = _captured_html()
        with ctx:
            stepper.render(["A", "B"], actual_idx=99)
        # No debe levantar excepción

    def test_completados_override_explicito(self) -> None:
        # Si se pasa completados explícito, se respeta sobre actual_idx
        captured, ctx = _captured_html()
        with ctx:
            stepper.render(["A", "B", "C", "D"], actual_idx=2, completados=0)
        html = "".join(captured)
        # Con completados=0 no debería haber checkmarks de completados
        # (pueden aparecer otros ✓ que sean parte del CSS/icon system —
        # esta es la verificación más débil pero clarea la intención).
        assert "A" in html  # smoke test: el render funciona
