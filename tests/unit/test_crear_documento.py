"""Tests del use case CrearDocumentoEnBlanco."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.core.template_catalog import TEMPLATE_MODEL_DEVELOPMENT
from src.core.usecases.crear_documento import (
    CrearDocumentoEnBlanco,
    ResultadoCrearDocumento,
)


def _construir_uc(repo: MagicMock) -> CrearDocumentoEnBlanco:
    return CrearDocumentoEnBlanco(repo=repo)


def test_crear_devuelve_resultado_con_documento_completo() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    resultado = uc.ejecutar(nombre_modelo="ESG Stochastic", model_id="MD-2026-001")

    assert isinstance(resultado, ResultadoCrearDocumento)
    doc = resultado.documento
    assert len(doc.secciones) == len(TEMPLATE_MODEL_DEVELOPMENT)
    assert all(s.contenido is None for s in doc.secciones)


def test_crear_popula_metadata_minima() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    resultado = uc.ejecutar(nombre_modelo="ESG Stochastic", model_id="MD-2026-001")

    doc = resultado.documento
    assert doc.metadata_modelo.nombre_modelo == "ESG Stochastic"
    assert doc.metadata_modelo.model_id == "MD-2026-001"


def test_crear_estado_inicial_es_draft() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    resultado = uc.ejecutar(nombre_modelo="X", model_id="Y")

    assert resultado.documento.estado == "draft"


def test_crear_archivo_origen_es_none() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    resultado = uc.ejecutar(nombre_modelo="X", model_id="Y")

    assert resultado.documento.archivo_origen is None


def test_crear_registra_evento_documento_creado_en_audit_trail() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    resultado = uc.ejecutar(nombre_modelo="ESG Stochastic", model_id="MD-2026-001")

    doc = resultado.documento
    tipos = [e.tipo for e in doc.audit_trail]
    assert "documento_creado" in tipos
    evento = next(e for e in doc.audit_trail if e.tipo == "documento_creado")
    assert evento.actor == "default"


def test_crear_persiste_via_repository() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    resultado = uc.ejecutar(nombre_modelo="X", model_id="Y")

    repo.guardar.assert_called_once_with(resultado.documento)


def test_crear_user_id_default() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    resultado = uc.ejecutar(nombre_modelo="X", model_id="Y")

    assert resultado.documento.user_id == "default"


def test_crear_user_id_custom() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    resultado = uc.ejecutar(nombre_modelo="X", model_id="Y", user_id="alberto")

    assert resultado.documento.user_id == "alberto"


def test_crear_rechaza_nombre_modelo_vacio() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    with pytest.raises(ValueError, match="nombre_modelo"):
        uc.ejecutar(nombre_modelo="   ", model_id="Y")


def test_crear_rechaza_model_id_vacio() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    with pytest.raises(ValueError, match="model_id"):
        uc.ejecutar(nombre_modelo="X", model_id="")


def test_crear_sin_fuentes_no_genera_sugerencias() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    resultado = uc.ejecutar(nombre_modelo="X", model_id="Y")

    assert resultado.sugerencias is None
    assert resultado.fuentes_extraidas == 0
    assert resultado.advertencias == []


def test_crear_con_fuentes_pero_sin_llm_avisa_pero_no_falla() -> None:
    """Si el usuario sube fuentes y no hay LLM, se cargan como contexto y se
    agrega una advertencia (no se pierde el material). El flujo sigue."""
    repo = MagicMock()
    uc = CrearDocumentoEnBlanco(repo=repo, llm=None)
    from io import BytesIO

    contenido_txt = b"Texto suficientemente largo para contar como fuente util."
    fuentes = [(BytesIO(contenido_txt), "notas.txt")]

    resultado = uc.ejecutar(
        nombre_modelo="X",
        model_id="Y",
        fuentes_adicionales=fuentes,
    )

    assert resultado.llm_disponible is False
    assert resultado.fuentes_extraidas == 1
    assert resultado.sugerencias is None
    assert any("asistente de IA no está disponible" in a for a in resultado.advertencias)


def test_crear_advertencia_si_fuente_falla_al_extraer() -> None:
    """Una fuente con extension no soportada se reporta como descartada."""
    repo = MagicMock()
    uc = _construir_uc(repo)
    from io import BytesIO

    fuentes = [(BytesIO(b"\x00\x01\x02 invalid"), "archivo.bin")]

    resultado = uc.ejecutar(
        nombre_modelo="X",
        model_id="Y",
        fuentes_adicionales=fuentes,
    )

    # Sin LLM y la fuente fallida → debe haber al menos una advertencia o descarte
    assert "archivo.bin" in resultado.fuentes_descartadas
