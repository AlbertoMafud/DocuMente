"""Tests del use case CrearDocumentoEnBlanco."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.core.template_catalog import TEMPLATE_MODEL_DEVELOPMENT
from src.core.usecases.crear_documento import CrearDocumentoEnBlanco


def _construir_uc(repo: MagicMock) -> CrearDocumentoEnBlanco:
    return CrearDocumentoEnBlanco(repo=repo)


def test_crear_devuelve_documento_con_todas_las_secciones_del_catalogo() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    doc = uc.ejecutar(nombre_modelo="ESG Stochastic", model_id="MD-2026-001")

    assert len(doc.secciones) == len(TEMPLATE_MODEL_DEVELOPMENT)
    assert all(s.contenido is None for s in doc.secciones)


def test_crear_popula_metadata_minima() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    doc = uc.ejecutar(nombre_modelo="ESG Stochastic", model_id="MD-2026-001")

    assert doc.metadata_modelo.nombre_modelo == "ESG Stochastic"
    assert doc.metadata_modelo.model_id == "MD-2026-001"


def test_crear_estado_inicial_es_draft() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    doc = uc.ejecutar(nombre_modelo="X", model_id="Y")

    assert doc.estado == "draft"


def test_crear_archivo_origen_es_none() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    doc = uc.ejecutar(nombre_modelo="X", model_id="Y")

    assert doc.archivo_origen is None


def test_crear_registra_evento_documento_creado_en_audit_trail() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    doc = uc.ejecutar(nombre_modelo="ESG Stochastic", model_id="MD-2026-001")

    tipos = [e.tipo for e in doc.audit_trail]
    assert "documento_creado" in tipos
    evento = next(e for e in doc.audit_trail if e.tipo == "documento_creado")
    assert evento.actor == "default"


def test_crear_persiste_via_repository() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    doc = uc.ejecutar(nombre_modelo="X", model_id="Y")

    repo.guardar.assert_called_once_with(doc)


def test_crear_user_id_default() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    doc = uc.ejecutar(nombre_modelo="X", model_id="Y")

    assert doc.user_id == "default"


def test_crear_user_id_custom() -> None:
    repo = MagicMock()
    uc = _construir_uc(repo)

    doc = uc.ejecutar(nombre_modelo="X", model_id="Y", user_id="alberto")

    assert doc.user_id == "alberto"


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
