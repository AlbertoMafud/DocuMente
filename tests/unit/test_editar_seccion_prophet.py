from __future__ import annotations

import json
import os

import pytest

from src.core.models import Documento
from src.core.models.documento import MetadataModelo
from src.core.template_catalog_prophet import construir_secciones_vacias_prophet
from src.storage.repositories import DocumentoRepository


@pytest.fixture()
def repo_con_doc_prophet(tmp_path):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path}/test.db"
    repo = DocumentoRepository()
    doc = Documento(
        tipo="prophet",
        metadata_modelo=MetadataModelo(nombre_modelo="VNB Test"),
        secciones=construir_secciones_vacias_prophet(),
    )
    repo.guardar(doc)
    yield repo, doc
    os.environ.pop("DATABASE_URL", None)


def test_guardar_tabla_serializa_a_json(repo_con_doc_prophet) -> None:
    repo, doc = repo_con_doc_prophet
    seccion = doc.seccion_por_id("corridas_runs")
    assert seccion is not None

    filas = [{"numero": "33", "detalle": "IL UDI", "es_alm": "No",
               "tiempo_ejecucion": "45 min", "corrida_precedente": "", "outputs_principales": "VNB", "responsable": "Carmona"}]
    contenido_json = json.dumps({"filas": filas, "advertencias": []})

    seccion.contenido = contenido_json
    seccion.completitud = "completa"
    repo.guardar(doc)

    doc_recuperado = repo.obtener(doc.id)
    assert doc_recuperado is not None
    s = doc_recuperado.seccion_por_id("corridas_runs")
    assert s is not None and s.contenido is not None
    data = json.loads(s.contenido)
    assert len(data["filas"]) == 1
    assert data["filas"][0]["numero"] == "33"


def test_guardar_texto_persiste_correctamente(repo_con_doc_prophet) -> None:
    repo, doc = repo_con_doc_prophet
    seccion = doc.seccion_por_id("supuestos")
    assert seccion is not None

    seccion.contenido = json.dumps({"contenido": "Mortalidad CNSF 2000. Lapsos del 5%.", "advertencias": []})
    seccion.completitud = "completa"
    repo.guardar(doc)

    doc_rec = repo.obtener(doc.id)
    s = doc_rec.seccion_por_id("supuestos")
    assert s is not None
    data = json.loads(s.contenido)
    assert "Mortalidad" in data["contenido"]


def test_seccion_vacia_completitud_vacia(repo_con_doc_prophet) -> None:
    _repo, doc = repo_con_doc_prophet
    seccion = doc.seccion_por_id("limitaciones_riesgos")
    assert seccion is not None
    assert seccion.completitud == "vacia"
    assert seccion.contenido is None
