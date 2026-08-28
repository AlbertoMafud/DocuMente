"""Smoke tests de la API del Template Studio.

Cubren el ciclo completo por HTTP: crear borrador → curar → lint → publicar
→ crear documento con el tipo nuevo → retirar. Sin LLM real (el endpoint
`extraer` con LLM ausente devuelve la estructura y una advertencia).
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _db_temporal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / f"test_studio_{uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.delenv("DOCUMENTE_GATE_PASSWORD", raising=False)
    monkeypatch.delenv("DOCUMENTE_ADMIN_TOKEN", raising=False)
    import src.storage.db as db_module

    db_module._engine = None  # type: ignore[attr-defined]
    db_module._SessionLocal = None  # type: ignore[attr-defined]


@pytest.fixture
def client() -> TestClient:
    from src.api.main import app

    return TestClient(app)


def _secciones_sanas() -> list[dict]:
    return [
        {
            "id": "1.objetivo",
            "numero": "1",
            "nombre": "Objetivo",
            "obligatoria": True,
            "intencion": "Qué logra el procedimiento y qué necesidad atiende.",
            "aliases": ["objetivo", "propósito"],
            "preguntas_guia": ["¿Qué problema resuelve este procedimiento?"],
        },
        {
            "id": "2.alcance",
            "numero": "2",
            "nombre": "Alcance",
            "obligatoria": False,
            "intencion": "Qué áreas y sistemas cubre, y qué queda fuera.",
            "aliases": ["alcance"],
            "preguntas_guia": ["¿Qué queda explícitamente fuera?"],
        },
    ]


def _crear(client: TestClient, nombre: str = "Ficha de Procedimiento") -> dict:
    r = client.post(
        "/studio/templates",
        json={"nombre": nombre, "descripcion": "Doc de prueba", "secciones": _secciones_sanas()},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_crear_template_devuelve_201(client: TestClient) -> None:
    t = _crear(client)
    assert t["estado"] == "borrador"
    assert t["slug"] == "ficha_de_procedimiento"
    assert len(t["secciones"]) == 2


def test_crear_con_slug_reservado_devuelve_400(client: TestClient) -> None:
    r = client.post(
        "/studio/templates",
        json={"nombre": "Intento", "slug": "prophet", "secciones": _secciones_sanas()},
    )
    assert r.status_code == 400
    assert "reservado" in r.json()["detail"]


def test_listar_y_filtrar_por_estado(client: TestClient) -> None:
    _crear(client)
    assert len(client.get("/studio/templates").json()) == 1
    assert client.get("/studio/templates", params={"estado": "publicado"}).json() == []


def test_obtener_inexistente_devuelve_404(client: TestClient) -> None:
    assert client.get(f"/studio/templates/{uuid4()}").status_code == 404


def test_actualizar_metadata(client: TestClient) -> None:
    t = _crear(client)
    r = client.patch(f"/studio/templates/{t['id']}", json={"area_duena": "Riesgos"})
    assert r.status_code == 200
    assert r.json()["area_duena"] == "Riesgos"
    assert r.json()["slug"] == t["slug"]  # el slug es identidad, no cambia


def test_actualizar_secciones_invalida_lint(client: TestClient) -> None:
    t = _crear(client)
    assert client.post(f"/studio/templates/{t['id']}/lint").status_code == 200
    r = client.put(
        f"/studio/templates/{t['id']}/secciones",
        json={"secciones": _secciones_sanas()[:1]},
    )
    assert r.status_code == 200
    assert r.json()["resultado_lint"] is None


def test_lint_reporta_errores_de_ai_readiness(client: TestClient) -> None:
    r = client.post(
        "/studio/templates",
        json={
            "nombre": "Template Malo",
            "secciones": [
                {
                    "id": "1.x",
                    "numero": "1",
                    "nombre": "Sin intención",
                    "obligatoria": True,
                }
            ],
        },
    )
    t = r.json()
    lint = client.post(f"/studio/templates/{t['id']}/lint").json()
    codigos = {h["codigo"] for h in lint["hallazgos"]}
    assert "L3" in codigos  # intención vacía
    assert "L4" in codigos  # obligatoria sin preguntas guía


def test_publicar_sin_lint_devuelve_400(client: TestClient) -> None:
    t = _crear(client)
    r = client.post(f"/studio/templates/{t['id']}/estado", json={"accion": "publicar"})
    assert r.status_code == 400
    assert "lint" in r.json()["detail"].lower()


def test_ciclo_completo_publicar_y_crear_documento(client: TestClient) -> None:
    """El test que importa: publicar un template lo vuelve usable de verdad."""
    t = _crear(client)
    client.post(f"/studio/templates/{t['id']}/lint")
    r = client.post(f"/studio/templates/{t['id']}/estado", json={"accion": "publicar"})
    assert r.status_code == 200
    assert r.json()["estado"] == "publicado"

    # Aparece en el listado de templates disponibles para crear documentos
    tipos = [x["tipo"] for x in client.get("/templates").json()]
    assert "ficha_de_procedimiento" in tipos
    assert "model_development" in tipos  # los congelados siguen ahí

    # Su catálogo se sirve por el endpoint genérico
    catalogo = client.get("/templates/ficha_de_procedimiento/catalogo").json()
    assert [s["id"] for s in catalogo] == ["1.objetivo", "2.alcance"]

    # Y se puede crear un documento con ese tipo
    doc = client.post(
        "/documentos",
        json={"nombre_modelo": "Alta de proveedores", "tipo": "ficha_de_procedimiento"},
    )
    assert doc.status_code == 201, doc.text
    creado = doc.json()
    assert creado["tipo"] == "ficha_de_procedimiento"
    assert [s["id"] for s in creado["secciones"]] == ["1.objetivo", "2.alcance"]


def test_crear_documento_con_tipo_inexistente_devuelve_404(client: TestClient) -> None:
    r = client.post("/documentos", json={"nombre_modelo": "X", "tipo": "no_existe"})
    assert r.status_code == 404


def test_retirar_no_rompe_documentos_existentes(client: TestClient) -> None:
    t = _crear(client)
    client.post(f"/studio/templates/{t['id']}/lint")
    client.post(f"/studio/templates/{t['id']}/estado", json={"accion": "publicar"})
    doc_id = client.post(
        "/documentos",
        json={"nombre_modelo": "Doc vivo", "tipo": "ficha_de_procedimiento"},
    ).json()["id"]

    assert (
        client.post(f"/studio/templates/{t['id']}/estado", json={"accion": "retirar"}).status_code
        == 200
    )
    # El documento sigue abriéndose: copió su estructura al nacer.
    doc = client.get(f"/documentos/{doc_id}")
    assert doc.status_code == 200
    assert len(doc.json()["secciones"]) == 2
    # Pero ya no se pueden crear documentos nuevos de ese tipo.
    assert (
        client.post(
            "/documentos", json={"nombre_modelo": "Otro", "tipo": "ficha_de_procedimiento"}
        ).status_code
        == 404
    )


def test_nueva_version_y_borrado(client: TestClient) -> None:
    t = _crear(client)
    client.post(f"/studio/templates/{t['id']}/lint")
    client.post(f"/studio/templates/{t['id']}/estado", json={"accion": "publicar"})

    v2 = client.post(f"/studio/templates/{t['id']}/nueva-version")
    assert v2.status_code == 201
    assert v2.json()["version"] == 2
    assert v2.json()["estado"] == "borrador"

    # El borrador se puede borrar; el publicado no.
    assert client.delete(f"/studio/templates/{v2.json()['id']}").status_code == 204
    assert client.delete(f"/studio/templates/{t['id']}").status_code == 400


def test_extraer_rechaza_archivo_no_docx(client: TestClient) -> None:
    r = client.post(
        "/studio/templates/extraer",
        files={"archivo": ("notas.txt", b"contenido", "text/plain")},
        data={"nombre": "X"},
    )
    assert r.status_code == 400


def test_admin_token_bloquea_cuando_esta_configurado(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DOCUMENTE_ADMIN_TOKEN", "secreto-admin")
    # Sin token: bloqueado
    assert (
        client.post("/studio/templates", json={"nombre": "X", "secciones": []}).status_code == 401
    )
    # Token incorrecto: prohibido
    r = client.post(
        "/studio/templates",
        json={"nombre": "X", "secciones": []},
        headers={"Authorization": "Bearer incorrecto"},
    )
    assert r.status_code == 403
    # Token correcto: pasa
    r = client.post(
        "/studio/templates",
        json={"nombre": "Con token", "secciones": _secciones_sanas()},
        headers={"Authorization": "Bearer secreto-admin"},
    )
    assert r.status_code == 201
    # Lectura sigue abierta a usuarios no admin
    assert client.get("/studio/templates").status_code == 200
