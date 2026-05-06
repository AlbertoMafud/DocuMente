"""Storage interface + FilesystemStorage.

Abstracción que aísla el acceso a archivos del resto de la app. En MVP la
única implementación es `FilesystemStorage` (escribe a disco local). Al
migrar a EC2, se sustituye por `S3Storage` sin cambiar código de negocio.

Esto materializa el principio §1.3 de `docs/MIGRATION_TO_EC2.md`.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import IO, Protocol


class Storage(Protocol):
    """Interfaz para almacenamiento de archivos.

    Los IDs son strings opacos: en `FilesystemStorage` son rutas relativas;
    en `S3Storage` (post-MVP) serán keys de S3.
    """

    def guardar_upload(self, archivo: IO[bytes], nombre_original: str) -> str:
        """Guarda un archivo subido por el usuario y devuelve su ID interno."""
        ...

    def guardar_export(self, ruta_origen: Path, nombre_destino: str) -> str:
        """Mueve un archivo generado a la zona de exports y devuelve su ID."""
        ...

    def leer(self, file_id: str) -> bytes:
        """Lee el contenido completo del archivo con `file_id`."""
        ...

    def ruta_local(self, file_id: str) -> Path:
        """Devuelve un Path local accesible.

        En `FilesystemStorage` es la ruta directa.
        En `S3Storage` (post-MVP) será una descarga temporal a `/tmp`.
        """
        ...

    def existe(self, file_id: str) -> bool:
        """True si el archivo con `file_id` existe."""
        ...


class FilesystemStorage:
    """Implementación de `Storage` que vive en disco local.

    Estructura interna:
        base_dir/
        ├── uploads/
        │   └── {uuid}__nombre_original.docx
        └── exports/
            └── {uuid}__nombre_destino.docx
    """

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.uploads_dir = base_dir / "uploads"
        self.exports_dir = base_dir / "exports"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def _safe_name(self, nombre: str) -> str:
        """Sanitiza nombre de archivo: solo alfanuméricos, _ y -."""
        return "".join(c if c.isalnum() or c in "._- " else "_" for c in nombre).strip()

    def guardar_upload(self, archivo: IO[bytes], nombre_original: str) -> str:
        file_id = f"uploads/{uuid.uuid4().hex}__{self._safe_name(nombre_original)}"
        destino = self.base_dir / file_id
        with destino.open("wb") as out:
            shutil.copyfileobj(archivo, out)
        return file_id

    def guardar_export(self, ruta_origen: Path, nombre_destino: str) -> str:
        file_id = f"exports/{uuid.uuid4().hex}__{self._safe_name(nombre_destino)}"
        destino = self.base_dir / file_id
        shutil.copy2(ruta_origen, destino)
        return file_id

    def leer(self, file_id: str) -> bytes:
        return (self.base_dir / file_id).read_bytes()

    def ruta_local(self, file_id: str) -> Path:
        return self.base_dir / file_id

    def existe(self, file_id: str) -> bool:
        return (self.base_dir / file_id).exists()
