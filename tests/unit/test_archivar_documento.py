"""Tests del use case ArchivarDocumento + job de purga.

Cobertura:
- Archivar / desarchivar oculta y restaura del home.
- Mover a papelera retiene N días.
- Restaurar de papelera revierte.
- Eliminar permanente requiere admin (PermissionError si no).
- Job de purga elimina expirados (mock de fecha).
- Audit trail registra cada acción.
- Listados respetan visibilidad.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from src.core.models import Documento
from src.core.models.documento import MetadataModelo
from src.core.usecases.archivar_documento import (
    ArchivarDocumento,
    purgar_papelera_expirada,
)
from src.storage.repositories import DocumentoRepository


@pytest.fixture
def repo_aislado(monkeypatch, tmp_path: Path) -> DocumentoRepository:
    """Repositorio sobre BD SQLite efímera (file en tmp_path)."""
    db_file = tmp_path / "test_archivar.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    # Forzar re-init del engine lazy
    import src.storage.db as db_mod

    db_mod._engine = None
    db_mod._SessionLocal = None
    yield DocumentoRepository()
    db_mod._engine = None
    db_mod._SessionLocal = None


def _doc_nuevo(user_id: str = "alice") -> Documento:
    return Documento(
        user_id=user_id,
        metadata_modelo=MetadataModelo(nombre_modelo="Test", model_id="T-1"),
    )


def test_archivar_oculta_documento_del_listado_por_defecto(repo_aislado) -> None:
    doc = _doc_nuevo()
    repo_aislado.guardar(doc)

    ArchivarDocumento(repo_aislado).archivar(doc.id, actor="alice")

    activos = repo_aislado.listar_por_usuario("alice")
    assert len(activos) == 0
    archivados = repo_aislado.listar_por_usuario("alice", incluir_archivados=True)
    assert len(archivados) == 1


def test_archivar_registra_evento_de_audit(repo_aislado) -> None:
    doc = _doc_nuevo()
    repo_aislado.guardar(doc)
    ArchivarDocumento(repo_aislado).archivar(doc.id, actor="alice", razon="ya no aplica")

    actualizado = repo_aislado.obtener(doc.id)
    assert actualizado is not None
    eventos = [e for e in actualizado.audit_trail if e.tipo == "archivado"]
    assert len(eventos) == 1
    assert eventos[0].actor == "alice"
    assert eventos[0].metadata.get("razon") == "ya no aplica"


def test_archivar_es_idempotente(repo_aislado) -> None:
    doc = _doc_nuevo()
    repo_aislado.guardar(doc)
    uc = ArchivarDocumento(repo_aislado)
    uc.archivar(doc.id, actor="alice")
    uc.archivar(doc.id, actor="alice")  # segunda vez no crashea ni duplica eventos

    actualizado = repo_aislado.obtener(doc.id)
    assert actualizado is not None
    eventos = [e for e in actualizado.audit_trail if e.tipo == "archivado"]
    assert len(eventos) == 1


def test_desarchivar_revierte_estado(repo_aislado) -> None:
    doc = _doc_nuevo()
    repo_aislado.guardar(doc)
    uc = ArchivarDocumento(repo_aislado)
    uc.archivar(doc.id, actor="alice")
    uc.desarchivar(doc.id, actor="alice")

    activos = repo_aislado.listar_por_usuario("alice")
    assert len(activos) == 1


def test_enviar_a_papelera_solo_aparece_en_listado_papelera(repo_aislado) -> None:
    doc = _doc_nuevo()
    repo_aislado.guardar(doc)
    ArchivarDocumento(repo_aislado).enviar_a_papelera(doc.id, actor="alice")

    activos = repo_aislado.listar_por_usuario("alice")
    archivados = repo_aislado.listar_por_usuario("alice", incluir_archivados=True)
    papelera = repo_aislado.listar_por_usuario("alice", solo_papelera=True)
    assert len(activos) == 0
    assert len(archivados) == 0
    assert len(papelera) == 1


def test_restaurar_de_papelera_vuelve_a_activos(repo_aislado) -> None:
    doc = _doc_nuevo()
    repo_aislado.guardar(doc)
    uc = ArchivarDocumento(repo_aislado)
    uc.enviar_a_papelera(doc.id, actor="alice")
    uc.restaurar_de_papelera(doc.id, actor="alice")

    activos = repo_aislado.listar_por_usuario("alice")
    assert len(activos) == 1


def test_eliminar_permanente_no_admin_levanta_permission_error(repo_aislado) -> None:
    doc = _doc_nuevo()
    repo_aislado.guardar(doc)
    uc = ArchivarDocumento(repo_aislado)

    with pytest.raises(PermissionError, match="admin"):
        uc.eliminar_permanente(doc.id, actor="alice", es_admin=False)

    # El doc sigue existiendo (no se borró)
    assert repo_aislado.obtener(doc.id) is not None


def test_eliminar_permanente_admin_borra_de_bd(repo_aislado) -> None:
    doc = _doc_nuevo()
    repo_aislado.guardar(doc)
    uc = ArchivarDocumento(repo_aislado)

    uc.eliminar_permanente(doc.id, actor="admin1", es_admin=True)

    assert repo_aislado.obtener(doc.id) is None


def test_archivar_documento_inexistente_levanta_value_error(repo_aislado) -> None:
    uc = ArchivarDocumento(repo_aislado)
    with pytest.raises(ValueError, match="no encontrado"):
        uc.archivar(uuid4(), actor="alice")


def test_purgar_papelera_elimina_solo_los_expirados(repo_aislado) -> None:
    """Documentos con archivado_en > cutoff se purgan; los recientes se preservan."""
    doc_viejo = _doc_nuevo()
    doc_reciente = _doc_nuevo()
    repo_aislado.guardar(doc_viejo)
    repo_aislado.guardar(doc_reciente)
    uc = ArchivarDocumento(repo_aislado)
    uc.enviar_a_papelera(doc_viejo.id, actor="alice")
    uc.enviar_a_papelera(doc_reciente.id, actor="alice")

    # Forzar `archivado_en` antiguo en doc_viejo
    doc_v = repo_aislado.obtener(doc_viejo.id)
    assert doc_v is not None
    doc_v.archivado_en = datetime.now(UTC) - timedelta(days=45)
    repo_aislado.guardar(doc_v)

    eliminados = purgar_papelera_expirada(repo_aislado, dias_retencion=30)
    assert eliminados == 1
    assert repo_aislado.obtener(doc_viejo.id) is None
    assert repo_aislado.obtener(doc_reciente.id) is not None


def test_visibilidad_property_derivada() -> None:
    doc = _doc_nuevo()
    assert doc.visibilidad == "activo"
    doc.archivado = True
    assert doc.visibilidad == "archivado"
    doc.en_papelera = True
    assert doc.visibilidad == "papelera"  # papelera tiene precedencia
