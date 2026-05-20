from __future__ import annotations

import io
from typing import Any

import openpyxl

from src.core.usecases.detectar_modelos_prophet import (
    DetectarModelosProphet,
)


def _excel_con_modelos(filas: list[dict[str, Any]]) -> bytes:
    """Crea un Excel mínimo con la hoja Descripcion_General."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Descripcion_General"
    if filas:
        ws.append(list(filas[0].keys()))
        for row in filas:
            ws.append(list(row.values()))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_detecta_modelo_unico() -> None:
    xlsx = _excel_con_modelos(
        [{"Area": "Rentabilidad", "Proceso": "VNB", "Encargado": "Francisco Carmona"}]
    )
    uc = DetectarModelosProphet(llm=None)
    resultado = uc.ejecutar(xlsx)
    assert len(resultado.modelos) == 1
    assert resultado.modelos[0].nombre == "VNB"
    assert resultado.modelos[0].encargado == "Francisco Carmona"


def test_detecta_multiples_modelos() -> None:
    xlsx = _excel_con_modelos(
        [
            {"Proceso": "VNB", "Encargado": "Carmona"},
            {"Proceso": "IRR", "Encargado": "Cynthia"},
        ]
    )
    uc = DetectarModelosProphet(llm=None)
    resultado = uc.ejecutar(xlsx)
    assert len(resultado.modelos) == 2
    nombres = [m.nombre for m in resultado.modelos]
    assert "VNB" in nombres
    assert "IRR" in nombres


def test_excel_vacio_devuelve_lista_vacia() -> None:
    xlsx = _excel_con_modelos([])
    uc = DetectarModelosProphet(llm=None)
    resultado = uc.ejecutar(xlsx)
    assert resultado.modelos == []
    assert len(resultado.advertencias) > 0


def test_bytes_invalidos_devuelve_advertencia() -> None:
    uc = DetectarModelosProphet(llm=None)
    resultado = uc.ejecutar(b"esto no es un excel")
    assert resultado.modelos == []
    assert len(resultado.advertencias) > 0


def test_fila_idx_es_base_cero() -> None:
    xlsx = _excel_con_modelos(
        [
            {"Proceso": "VNB", "Encargado": "Carmona"},
            {"Proceso": "IRR", "Encargado": "Cynthia"},
        ]
    )
    uc = DetectarModelosProphet(llm=None)
    resultado = uc.ejecutar(xlsx)
    assert resultado.modelos[0].fila_idx == 0
    assert resultado.modelos[1].fila_idx == 1
