"""Tests para el componente `continue_hero` y su helper de tiempo relativo.

Resuelve Quick Win #2 del audit UX Pro Max ("Continúa donde te quedaste"):
hero prominente cuando hay docs activos.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from src.ui.components import continue_hero


class TestTiempoRelativo:
    """`continue_hero.formato_relativo(dt)` devuelve un string en español
    como 'hace 2 horas', 'hace 1 día', 'hace 3 meses'."""

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def test_segundos_recientes(self) -> None:
        ts = self._now() - timedelta(seconds=20)
        assert "hace" in continue_hero.formato_relativo(ts).lower()
        # Para menos de 1 minuto devuelve "hace unos segundos" o similar
        out = continue_hero.formato_relativo(ts)
        assert "segundo" in out or "moment" in out

    def test_minutos(self) -> None:
        ts = self._now() - timedelta(minutes=5)
        out = continue_hero.formato_relativo(ts)
        assert "minuto" in out

    def test_una_hora_en_singular(self) -> None:
        ts = self._now() - timedelta(hours=1, minutes=2)
        out = continue_hero.formato_relativo(ts)
        assert "hora" in out
        # 1 hora — singular
        assert "1 hora" in out or "una hora" in out.lower()

    def test_varias_horas_plural(self) -> None:
        ts = self._now() - timedelta(hours=3)
        out = continue_hero.formato_relativo(ts)
        assert "horas" in out

    def test_un_dia(self) -> None:
        ts = self._now() - timedelta(days=1, hours=2)
        out = continue_hero.formato_relativo(ts)
        assert "día" in out

    def test_varios_dias(self) -> None:
        ts = self._now() - timedelta(days=5)
        out = continue_hero.formato_relativo(ts)
        assert "días" in out

    def test_un_mes(self) -> None:
        ts = self._now() - timedelta(days=45)
        out = continue_hero.formato_relativo(ts)
        assert "mes" in out

    def test_varios_meses(self) -> None:
        ts = self._now() - timedelta(days=120)
        out = continue_hero.formato_relativo(ts)
        assert "mes" in out


class TestContinueHeroRender:
    """`continue_hero.render(doc)` produce HTML con el nombre + porcentaje +
    tiempo relativo. Devuelve True si el usuario clickeó 'Continuar'."""

    def _doc_fake(
        self,
        *,
        nombre: str = "Modelo VNB GMM",
        pct: float = 0.65,
        actualizado: datetime | None = None,
        estado: str = "draft",
        doc_id: str = "abcd1234",
    ):
        from types import SimpleNamespace

        if actualizado is None:
            actualizado = datetime.now(UTC) - timedelta(hours=2)
        return SimpleNamespace(
            id=doc_id,
            metadata_modelo=SimpleNamespace(nombre_modelo=nombre),
            porcentaje_completitud=pct,
            actualizado_en=actualizado,
            estado=estado,
        )

    def test_render_muestra_nombre_modelo(self) -> None:
        captured: list[str] = []
        with (
            patch("streamlit.markdown", side_effect=lambda h, **_: captured.append(h)),
            patch("streamlit.button", return_value=False),
        ):
            continue_hero.render(self._doc_fake())
        html = "".join(captured)
        assert "Modelo VNB GMM" in html

    def test_render_muestra_porcentaje(self) -> None:
        captured: list[str] = []
        with (
            patch("streamlit.markdown", side_effect=lambda h, **_: captured.append(h)),
            patch("streamlit.button", return_value=False),
        ):
            continue_hero.render(self._doc_fake(pct=0.42))
        html = "".join(captured)
        assert "42" in html and "%" in html

    def test_render_muestra_tiempo_relativo(self) -> None:
        captured: list[str] = []
        ts = datetime.now(UTC) - timedelta(hours=3)
        with (
            patch("streamlit.markdown", side_effect=lambda h, **_: captured.append(h)),
            patch("streamlit.button", return_value=False),
        ):
            continue_hero.render(self._doc_fake(actualizado=ts))
        html = "".join(captured)
        assert "horas" in html

    def test_render_devuelve_true_si_click_continuar(self) -> None:
        with patch("streamlit.markdown"), patch("streamlit.button", return_value=True):
            resultado = continue_hero.render(self._doc_fake())
        assert resultado is True

    def test_render_devuelve_false_si_no_hay_click(self) -> None:
        with patch("streamlit.markdown"), patch("streamlit.button", return_value=False):
            resultado = continue_hero.render(self._doc_fake())
        assert resultado is False
