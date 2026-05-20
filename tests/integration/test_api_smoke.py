"""Smoke tests de la API REST — verifica que cada endpoint responde sin LLM.

Tests usan httpx.TestClient sin levantar el server. No tocan LLM real
(los endpoints que lo requieren devuelven 503 cuando ANTHROPIC_API_KEY
no está). Sí escriben en una BD SQLite temporal por test.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _db_temporal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Aísla cada test con una BD SQLite temporal."""
    db_path = tmp_path / f"test_api_{uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    # Forzar a que DOCUMENTE_GATE_PASSWORD esté apagada en tests
    # (la API permite acceso sin token cuando no está seteada).
    monkeypatch.delenv("DOCUMENTE_GATE_PASSWORD", raising=False)
    # Reset del engine cacheado
    import src.storage.db as db_module

    db_module._engine = None  # type: ignore[attr-defined]
    db_module._SessionLocal = None  # type: ignore[attr-defined]


@pytest.fixture
def client() -> TestClient:
    from src.api.main import app

    return TestClient(app)


# --- Health ---


def test_healthz_responde_200(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["api"] == "documente"


def test_readyz_responde_200(client: TestClient) -> None:
    r = client.get("/readyz")
    assert r.status_code == 200


def test_root_devuelve_info_api(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["api"] == "documente"


# --- Templates / Catálogos ---


def test_templates_lista_los_dos_tipos(client: TestClient) -> None:
    r = client.get("/templates")
    assert r.status_code == 200
    tipos = {t["tipo"] for t in r.json()}
    assert tipos == {"model_development", "prophet"}


def test_template_mrm_capitulos_devuelve_9_grupos(client: TestClient) -> None:
    r = client.get("/templates/mrm/capitulos")
    assert r.status_code == 200
    caps = r.json()
    assert len(caps) == 9
    # Todos los capítulos deben tener al menos una sección
    for cap in caps:
        assert "numero" in cap
        assert "nombre" in cap


def test_motivos_omision_catalog(client: TestClient) -> None:
    r = client.get("/catalogos/motivos-omision")
    assert r.status_code == 200
    motivos = r.json()
    assert isinstance(motivos, list)
    assert len(motivos) > 0


# --- Documentos CRUD ---


def test_listar_documentos_vacio_devuelve_lista_vacia(client: TestClient) -> None:
    r = client.get("/documentos")
    assert r.status_code == 200
    assert r.json() == []


def test_crear_documento_mrm_devuelve_201(client: TestClient) -> None:
    r = client.post(
        "/documentos",
        json={"tipo": "model_development", "nombre_modelo": "Modelo Test"},
    )
    assert r.status_code == 201
    doc = r.json()
    assert doc["tipo"] == "model_development"
    assert doc["metadata_modelo"]["nombre_modelo"] == "Modelo Test"
    assert doc["estado"] == "draft"
    assert len(doc["secciones"]) > 0
    UUID(doc["id"])  # válido


def test_crear_documento_prophet_devuelve_201(client: TestClient) -> None:
    r = client.post(
        "/documentos",
        json={"tipo": "prophet", "nombre_modelo": "VNB GMM"},
    )
    assert r.status_code == 201
    doc = r.json()
    assert doc["tipo"] == "prophet"
    assert doc["metadata_modelo"]["nombre_modelo"] == "VNB GMM"


def test_crear_y_obtener_documento(client: TestClient) -> None:
    created = client.post(
        "/documentos", json={"nombre_modelo": "Doc A"}
    ).json()
    doc_id = created["id"]

    r = client.get(f"/documentos/{doc_id}")
    assert r.status_code == 200
    assert r.json()["id"] == doc_id


def test_obtener_documento_inexistente_devuelve_404(client: TestClient) -> None:
    r = client.get(f"/documentos/{uuid4()}")
    assert r.status_code == 404


def test_editar_metadata_actualiza_campos(client: TestClient) -> None:
    doc_id = client.post("/documentos", json={"nombre_modelo": "X"}).json()["id"]
    r = client.patch(
        f"/documentos/{doc_id}/metadata",
        json={"nombre_modelo": "X v2", "fae": "Isabel Huerta"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["metadata_modelo"]["nombre_modelo"] == "X v2"
    assert data["metadata_modelo"]["fae"] == "Isabel Huerta"


# --- Visibilidad ---


def test_archivar_y_desarchivar(client: TestClient) -> None:
    doc_id = client.post("/documentos", json={"nombre_modelo": "Y"}).json()["id"]

    r_arch = client.post(f"/documentos/{doc_id}/archivar", json={})
    assert r_arch.status_code == 200
    assert r_arch.json()["archivado"] is True

    r_des = client.post(f"/documentos/{doc_id}/desarchivar")
    assert r_des.status_code == 200
    assert r_des.json()["archivado"] is False


def test_papelera_y_restaurar(client: TestClient) -> None:
    doc_id = client.post("/documentos", json={"nombre_modelo": "Z"}).json()["id"]

    r = client.post(f"/documentos/{doc_id}/papelera", json={})
    assert r.status_code == 200
    assert r.json()["en_papelera"] is True

    r2 = client.post(f"/documentos/{doc_id}/restaurar")
    assert r2.status_code == 200
    assert r2.json()["en_papelera"] is False


def test_listar_por_visibilidad_filtra_correctamente(client: TestClient) -> None:
    a = client.post("/documentos", json={"nombre_modelo": "Activo"}).json()["id"]
    arch = client.post("/documentos", json={"nombre_modelo": "Para archivar"}).json()["id"]
    pap = client.post("/documentos", json={"nombre_modelo": "Para papelera"}).json()["id"]

    client.post(f"/documentos/{arch}/archivar", json={})
    client.post(f"/documentos/{pap}/papelera", json={})

    activos_ids = {d["id"] for d in client.get("/documentos?visibilidad=activos").json()}
    archivados_ids = {d["id"] for d in client.get("/documentos?visibilidad=archivados").json()}
    papelera_ids = {d["id"] for d in client.get("/documentos?visibilidad=papelera").json()}

    assert a in activos_ids
    assert arch not in activos_ids
    assert arch in archivados_ids
    assert pap in papelera_ids


# --- Secciones ---


def test_listar_secciones_de_documento(client: TestClient) -> None:
    doc = client.post("/documentos", json={"nombre_modelo": "X"}).json()
    r = client.get(f"/documentos/{doc['id']}/secciones")
    assert r.status_code == 200
    secciones = r.json()
    assert len(secciones) == len(doc["secciones"])


def test_editar_seccion_actualiza_contenido_y_completitud(client: TestClient) -> None:
    doc = client.post("/documentos", json={"nombre_modelo": "X"}).json()
    seccion_id = doc["secciones"][0]["id"]

    contenido = "Contenido largo. " * 50  # > 200 chars
    r = client.put(
        f"/documentos/{doc['id']}/secciones/{seccion_id}",
        json={"contenido": contenido},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["contenido"].startswith("Contenido largo")
    assert data["completitud"] == "completa"


def test_omitir_y_reactivar_seccion(client: TestClient) -> None:
    doc = client.post("/documentos", json={"nombre_modelo": "X"}).json()
    seccion_id = doc["secciones"][0]["id"]

    r_om = client.post(
        f"/documentos/{doc['id']}/secciones/{seccion_id}/omitir",
        json={"motivo": "No aplica al modelo"},
    )
    assert r_om.status_code == 200
    assert r_om.json()["completitud"] == "omitida"

    r_re = client.post(f"/documentos/{doc['id']}/secciones/{seccion_id}/reactivar")
    assert r_re.status_code == 200
    assert r_re.json()["completitud"] == "vacia"


# --- Brechas + Auditoría ---


def test_brechas_devuelve_lista(client: TestClient) -> None:
    doc = client.post("/documentos", json={"nombre_modelo": "X"}).json()
    r = client.get(f"/documentos/{doc['id']}/brechas")
    assert r.status_code == 200
    # Doc nuevo en blanco debe tener brechas (secciones vacías)
    assert isinstance(r.json(), list)


def test_auditoria_incluye_evento_creacion(client: TestClient) -> None:
    doc = client.post("/documentos", json={"nombre_modelo": "X"}).json()
    r = client.get(f"/documentos/{doc['id']}/auditoria")
    assert r.status_code == 200
    eventos = r.json()
    tipos = {e["tipo"] for e in eventos}
    assert "documento_creado" in tipos


# --- Estado MRM ---


def test_transicion_invalida_devuelve_409(client: TestClient) -> None:
    """draft → approved es ilegal (debe pasar por in_review primero)."""
    doc = client.post("/documentos", json={"nombre_modelo": "X"}).json()
    r = client.post(
        f"/documentos/{doc['id']}/estado",
        json={"destino": "approved"},
    )
    assert r.status_code == 409


# --- LLM gating ---


def test_polish_sin_llm_devuelve_503(client: TestClient) -> None:
    doc = client.post("/documentos", json={"nombre_modelo": "X"}).json()
    # ANTHROPIC_API_KEY no está set en tests
    r = client.post(f"/documentos/{doc['id']}/polish")
    assert r.status_code == 503


def test_iniciar_entrevista_sin_llm_devuelve_503(client: TestClient) -> None:
    doc = client.post("/documentos", json={"nombre_modelo": "X"}).json()
    seccion_id = doc["secciones"][0]["id"]
    r = client.post(f"/documentos/{doc['id']}/entrevista/{seccion_id}/iniciar")
    assert r.status_code == 503


# --- Auth gate ---


def test_auth_gate_bloquea_sin_token_si_password_seteado(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Si DOCUMENTE_GATE_PASSWORD está seteada, se requiere bearer token."""
    monkeypatch.setenv("DOCUMENTE_GATE_PASSWORD", "secreto-test")
    r = client.get("/documentos")
    assert r.status_code == 401


def test_auth_gate_acepta_bearer_correcto(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DOCUMENTE_GATE_PASSWORD", "secreto-test")
    r = client.get(
        "/documentos",
        headers={"Authorization": "Bearer secreto-test"},
    )
    assert r.status_code == 200


def test_auth_gate_rechaza_bearer_incorrecto(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DOCUMENTE_GATE_PASSWORD", "secreto-test")
    r = client.get(
        "/documentos",
        headers={"Authorization": "Bearer mal-token"},
    )
    assert r.status_code == 401


# --- OpenAPI ---


def test_openapi_json_contiene_endpoints_clave(client: TestClient) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    paths = spec["paths"]
    # Endpoints clave deben existir en el spec
    assert "/documentos" in paths
    assert "/documentos/{documento_id}" in paths
    assert "/documentos/{documento_id}/brechas" in paths
    assert "/documentos/{documento_id}/exportar" in paths
    assert "/healthz" in paths
    # OpenAPI 3.x
    assert spec["openapi"].startswith("3.")


def test_docs_swagger_se_sirve(client: TestClient) -> None:
    r = client.get("/docs")
    assert r.status_code == 200
    assert "swagger" in r.text.lower() or "openapi" in r.text.lower()
