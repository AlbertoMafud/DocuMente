"""Tests de FilesystemStorage."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest

from src.storage.storage import FilesystemStorage


@pytest.fixture
def storage(tmp_path: Path) -> FilesystemStorage:
    return FilesystemStorage(tmp_path)


def test_filesystem_storage_crea_subdirs(storage: FilesystemStorage) -> None:
    assert (storage.base_dir / "uploads").exists()
    assert (storage.base_dir / "exports").exists()


def test_guardar_upload_y_leer_round_trip(storage: FilesystemStorage) -> None:
    data = b"contenido de prueba"
    file_id = storage.guardar_upload(BytesIO(data), "test.docx")
    assert storage.existe(file_id) is True
    assert storage.leer(file_id) == data


def test_guardar_upload_genera_id_unico(storage: FilesystemStorage) -> None:
    id1 = storage.guardar_upload(BytesIO(b"a"), "x.docx")
    id2 = storage.guardar_upload(BytesIO(b"b"), "x.docx")
    assert id1 != id2


def test_ruta_local_devuelve_path_correcto(storage: FilesystemStorage) -> None:
    file_id = storage.guardar_upload(BytesIO(b"data"), "y.docx")
    ruta = storage.ruta_local(file_id)
    assert ruta.exists()
    assert ruta.read_bytes() == b"data"


def test_existe_false_para_id_inventado(storage: FilesystemStorage) -> None:
    assert storage.existe("uploads/inexistente.docx") is False


def test_safe_name_remueve_chars_peligrosos(storage: FilesystemStorage) -> None:
    file_id = storage.guardar_upload(BytesIO(b"x"), "../../../etc/passwd")
    # No puede haber traversal: el path resultante vive bajo uploads/
    ruta = storage.ruta_local(file_id)
    assert "uploads" in str(ruta)
    assert ruta.exists()
