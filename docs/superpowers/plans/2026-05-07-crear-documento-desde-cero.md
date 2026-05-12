# Crear documento desde cero — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Habilitar el flujo "crear documento desde cero" (sin importar `.docx` previo) en DocuMente, reutilizando el catálogo canónico de 32 secciones que ya existe.

**Architecture:** Se promueve a pública la función `_construir_secciones_iniciales()` del `DocxReader` (lleva al `template_catalog`), se crea un use case `CrearDocumentoEnBlanco` paralelo a `ImportarDocumento`, y se agrega una pantalla mínima de creación (form de 2 campos: nombre del modelo + model_id). Una vez creado el `Documento`, el flujo converge con el actual: onboarding → dashboard → entrevista → export.

**Tech Stack:** Python 3.11+, Pydantic v2, Streamlit, pytest, ruff, mypy.

---

## File Structure

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `src/core/template_catalog.py` | Modificar | Agregar función pública `construir_secciones_vacias()` que devuelve `list[Seccion]` desde el catálogo |
| `src/docs/reader.py` | Modificar | Reemplazar `_construir_secciones_iniciales()` por llamada a la función pública |
| `src/core/usecases/crear_documento.py` | Crear | Use case `CrearDocumentoEnBlanco` |
| `src/core/usecases/__init__.py` | Modificar | Exponer el nuevo use case |
| `src/ui/pages/crear_nuevo.py` | Crear | Pantalla de creación (form 2 campos) |
| `src/ui/pages/__init__.py` | Modificar | Registrar la nueva página |
| `app.py` | Modificar | Habilitar botón "Crear nuevo documento" + ruta `crear_nuevo` |
| `tests/unit/test_template_catalog.py` | Crear | Tests del builder público |
| `tests/unit/test_crear_documento.py` | Crear | Tests del use case |

---

## Task 1: Promover `construir_secciones_vacias()` al `template_catalog`

**Files:**
- Modify: `src/core/template_catalog.py` (agregar función al final del archivo)
- Modify: `src/docs/reader.py:92-104` (reemplazar función privada por import)
- Test: `tests/unit/test_template_catalog.py` (crear)

**Why:** El reader hoy tiene `_construir_secciones_iniciales()` privada. La necesitamos pública para que el use case nuevo la reuse. El reader la sigue usando — sin duplicación.

- [ ] **Step 1.1: Escribir el test del builder público**

Crear `tests/unit/test_template_catalog.py`:

```python
"""Tests del catálogo del template oficial NYL."""

from __future__ import annotations

from src.core.models import Seccion
from src.core.template_catalog import (
    TEMPLATE_MODEL_DEVELOPMENT,
    construir_secciones_vacias,
)


def test_construir_secciones_vacias_devuelve_una_por_entrada_del_catalogo() -> None:
    secciones = construir_secciones_vacias()
    assert len(secciones) == len(TEMPLATE_MODEL_DEVELOPMENT)


def test_construir_secciones_vacias_devuelve_lista_de_secciones() -> None:
    secciones = construir_secciones_vacias()
    assert all(isinstance(s, Seccion) for s in secciones)


def test_construir_secciones_vacias_preserva_intencion_y_preguntas() -> None:
    secciones = construir_secciones_vacias()
    cat_por_id = {c.id: c for c in TEMPLATE_MODEL_DEVELOPMENT}
    for seccion in secciones:
        cat = cat_por_id[seccion.id]
        assert seccion.nombre == cat.nombre
        assert seccion.numero == cat.numero
        assert seccion.obligatoria == cat.obligatoria
        assert seccion.intencion == cat.intencion
        assert seccion.preguntas_guia == list(cat.preguntas_guia)


def test_construir_secciones_vacias_devuelve_secciones_vacias() -> None:
    secciones = construir_secciones_vacias()
    for seccion in secciones:
        assert seccion.contenido is None
        assert seccion.completitud == "vacia"
        assert seccion.motivo_omision is None


def test_construir_secciones_vacias_devuelve_lista_independiente() -> None:
    """Cada llamada devuelve secciones nuevas — no comparte estado."""
    a = construir_secciones_vacias()
    b = construir_secciones_vacias()
    a[0].contenido = "test"
    assert b[0].contenido is None
```

- [ ] **Step 1.2: Correr el test para verificar que falla**

```powershell
pytest tests/unit/test_template_catalog.py -v
```

Expected: FAIL con `ImportError: cannot import name 'construir_secciones_vacias'`.

- [ ] **Step 1.3: Implementar la función pública en `template_catalog.py`**

Agregar al final de `src/core/template_catalog.py`:

```python
from src.core.models import Seccion


def construir_secciones_vacias() -> list[Seccion]:
    """Devuelve una `Seccion` vacía por cada entrada del catálogo.

    Usado por:
    - `DocxReader` al importar un .docx (las secciones detectadas se llenan al parsear).
    - `CrearDocumentoEnBlanco` al crear un doc desde cero (todas quedan vacías).

    Cada llamada devuelve secciones independientes — no comparte estado.
    """
    return [
        Seccion(
            id=cat.id,
            nombre=cat.nombre,
            numero=cat.numero,
            obligatoria=cat.obligatoria,
            intencion=cat.intencion,
            preguntas_guia=list(cat.preguntas_guia),
        )
        for cat in TEMPLATE_MODEL_DEVELOPMENT
    ]
```

- [ ] **Step 1.4: Correr el test y verificar que pasa**

```powershell
pytest tests/unit/test_template_catalog.py -v
```

Expected: 5 passed.

- [ ] **Step 1.5: Reemplazar la función privada en `reader.py`**

En `src/docs/reader.py`:

1. Eliminar la definición de `_construir_secciones_iniciales` (líneas 92-104).
2. Cambiar el import en líneas 25-28 para incluir la nueva función:

```python
from src.core.template_catalog import (
    TEMPLATE_MODEL_DEVELOPMENT,
    SeccionCatalogo,
    construir_secciones_vacias,
)
```

3. Cambiar la llamada en `leer()` (línea 124):

```python
        documento = Documento(
            user_id=user_id,
            archivo_origen=str(ruta),
            secciones=construir_secciones_vacias(),
        )
```

- [ ] **Step 1.6: Correr toda la batería para verificar que el reader sigue funcionando**

```powershell
pytest tests/ -v
```

Expected: 174 passed (baseline) + 5 nuevos = **179 passed**. Cero regresiones.

- [ ] **Step 1.7: Commit**

```powershell
git add src/core/template_catalog.py src/docs/reader.py tests/unit/test_template_catalog.py
git commit -m "refactor: promover construir_secciones_vacias() a template_catalog"
```

---

## Task 2: Use case `CrearDocumentoEnBlanco`

**Files:**
- Create: `src/core/usecases/crear_documento.py`
- Modify: `src/core/usecases/__init__.py`
- Test: `tests/unit/test_crear_documento.py`

**Why:** Encapsula la creación del `Documento` esqueleto: secciones desde el catálogo, metadata mínima poblada, audit event `documento_creado`, persistencia. Paralelo simétrico a `ImportarDocumento`.

- [ ] **Step 2.1: Escribir los tests del use case**

Crear `tests/unit/test_crear_documento.py`:

```python
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
```

- [ ] **Step 2.2: Correr los tests para verificar que fallan**

```powershell
pytest tests/unit/test_crear_documento.py -v
```

Expected: FAIL con `ImportError`.

- [ ] **Step 2.3: Implementar el use case**

Crear `src/core/usecases/crear_documento.py`:

```python
"""Use case: CrearDocumentoEnBlanco.

Crea un Documento esqueleto con las 32 secciones del template oficial NYL
todas vacías, metadata mínima, audit event 'documento_creado' y lo persiste.

Es el punto de entrada del flujo "desde cero" — paralelo a ImportarDocumento.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from src.core.models import Documento, EventoAuditoria
from src.core.models.documento import MetadataModelo
from src.core.template_catalog import construir_secciones_vacias
from src.storage.repositories import DocumentoRepository


@dataclass
class CrearDocumentoEnBlanco:
    """Use case que crea un documento esqueleto y lo persiste."""

    repo: DocumentoRepository

    def ejecutar(
        self,
        nombre_modelo: str,
        model_id: str,
        user_id: str = "default",
    ) -> Documento:
        nombre_clean = nombre_modelo.strip()
        model_id_clean = model_id.strip()
        if not nombre_clean:
            raise ValueError("nombre_modelo no puede estar vacío.")
        if not model_id_clean:
            raise ValueError("model_id no puede estar vacío.")

        documento = Documento(
            user_id=user_id,
            metadata_modelo=MetadataModelo(
                nombre_modelo=nombre_clean,
                model_id=model_id_clean,
            ),
            secciones=construir_secciones_vacias(),
        )
        documento.registrar_evento(
            EventoAuditoria(
                timestamp=datetime.now(UTC),
                actor=user_id,
                tipo="documento_creado",
                descripcion=f"Documento creado desde cero: {nombre_clean}",
                metadata={"model_id": model_id_clean},
            )
        )
        self.repo.guardar(documento)
        return documento
```

- [ ] **Step 2.4: Exponer en `src/core/usecases/__init__.py`**

Agregar en `src/core/usecases/__init__.py`:

```python
from src.core.usecases.crear_documento import CrearDocumentoEnBlanco
```

Y agregar `"CrearDocumentoEnBlanco"` al `__all__` (en orden alfabético).

- [ ] **Step 2.5: Correr los tests del use case**

```powershell
pytest tests/unit/test_crear_documento.py -v
```

Expected: 10 passed.

- [ ] **Step 2.6: Correr toda la batería para verificar cero regresiones**

```powershell
pytest tests/ -v
```

Expected: **189 passed** (179 + 10 nuevos).

- [ ] **Step 2.7: Commit**

```powershell
git add src/core/usecases/crear_documento.py src/core/usecases/__init__.py tests/unit/test_crear_documento.py
git commit -m "feat: agregar use case CrearDocumentoEnBlanco"
```

---

## Task 3: Pantalla UI `crear_nuevo.py`

**Files:**
- Create: `src/ui/pages/crear_nuevo.py`
- Modify: `src/ui/pages/__init__.py`

**Why:** Form mínimo (2 inputs) para que el usuario nombre el modelo antes de entrar al onboarding. Mantiene el look SMNYL del resto de la app (mismo header, paleta, tipografías).

- [ ] **Step 3.1: Implementar la página**

Crear `src/ui/pages/crear_nuevo.py`:

```python
"""Pantalla de creación de documento desde cero.

Renderiza:
- Header con breadcrumbs.
- Form con 2 campos: nombre del modelo + model_id.
- Al submit: crea el Documento esqueleto, lo persiste, y redirige a onboarding.
"""

from __future__ import annotations

import streamlit as st

from src.core.usecases import CrearDocumentoEnBlanco
from src.storage.repositories import DocumentoRepository
from src.ui.components import header
from src.ui.theme import SMNYL_COLORS


def _construir_use_case() -> CrearDocumentoEnBlanco:
    return CrearDocumentoEnBlanco(repo=DocumentoRepository())


def render() -> None:
    header.render(breadcrumbs=["Inicio", "Crear nuevo documento"])

    st.markdown(
        f"""
        <h1 style="font-family: var(--font-display); color: {SMNYL_COLORS["text"]};
            margin-bottom: 0.5rem;">Crear nuevo documento</h1>
        <p style="color: {SMNYL_COLORS["text_muted"]}; margin-bottom: 2rem;
            max-width: 720px;">
            Empezarás con la estructura completa del Model Development Template
            oficial de NYL — 32 secciones vacías. DocuMente te guiará para llenarlas
            con apoyo de Claude.
        </p>
        """,
        unsafe_allow_html=True,
    )

    with st.form("crear_documento", clear_on_submit=False):
        st.markdown("### Identificación del modelo")
        nombre = st.text_input(
            "Nombre del modelo *",
            help="Ej. 'ESG Stochastic Generator', 'Lapse Rate Model'.",
        )
        model_id = st.text_input(
            "Model ID *",
            help=(
                "Identificador institucional único. Si tu organización usa "
                "nomenclatura formal (ej. M07.P07.S03.006.D), úsala aquí."
            ),
        )
        st.caption("Ambos campos son obligatorios. Podrás ajustar el resto en el onboarding.")

        col_a, col_b, _ = st.columns([1, 1, 2])
        with col_a:
            submit = st.form_submit_button("Crear documento", type="primary", use_container_width=True)
        with col_b:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

    if cancelar:
        st.session_state["pagina"] = "home"
        st.rerun()

    if submit:
        if not nombre.strip() or not model_id.strip():
            st.error("Completa nombre del modelo y model ID antes de continuar.")
            return

        uc = _construir_use_case()
        try:
            doc = uc.ejecutar(nombre_modelo=nombre, model_id=model_id)
        except ValueError as e:
            st.error(f"No se pudo crear el documento: {e}")
            return

        st.session_state["documento_actual_id"] = str(doc.id)
        st.session_state["pagina"] = "onboarding"
        st.rerun()
```

- [ ] **Step 3.2: Registrar la página en `__init__.py`**

En `src/ui/pages/__init__.py`, agregar el import de `crear_nuevo` y al `__all__`:

```python
from src.ui.pages import (
    auditoria,
    crear_nuevo,
    dashboard,
    entrevista,
    importar,
    onboarding,
    vista_previa,
)

__all__ = [
    "auditoria",
    "crear_nuevo",
    "dashboard",
    "entrevista",
    "importar",
    "onboarding",
    "vista_previa",
]
```

(Verificar el formato exacto del `__init__.py` actual antes de editar — preservar su estilo.)

- [ ] **Step 3.3: Verificar que el módulo importa sin error**

```powershell
python -c "from src.ui.pages import crear_nuevo; print('OK')"
```

Expected: `OK`.

- [ ] **Step 3.4: Commit**

```powershell
git add src/ui/pages/crear_nuevo.py src/ui/pages/__init__.py
git commit -m "feat: pantalla de creación de documento desde cero"
```

---

## Task 4: Habilitar botón en home + routing

**Files:**
- Modify: `app.py:55-67` (botón disabled → enabled)
- Modify: `app.py:15-22` (import) y router en `main()`

**Why:** Conectar la nueva pantalla al flujo. El botón ya tiene el copy correcto ("Crear nuevo documento") y la disposición visual; solo falta quitar `disabled=True` y rutear.

- [ ] **Step 4.1: Habilitar el botón "Crear nuevo documento"**

En `app.py`, reemplazar las líneas 55-67 (el bloque `with col_a:` ... `with col_b:`):

Reemplazar:

```python
    col_a, col_b, _ = st.columns([1, 1, 2])
    with col_a:
        st.button(
            "Crear nuevo documento",
            type="primary",
            use_container_width=True,
            disabled=True,
            help="Disponible en Fase 2 (requiere motor de entrevista con Claude).",
        )
    with col_b:
        if st.button("Mejorar documento existente", use_container_width=True):
            st.session_state["pagina"] = "importar"
            st.rerun()
```

Por:

```python
    col_a, col_b, _ = st.columns([1, 1, 2])
    with col_a:
        if st.button(
            "Crear nuevo documento",
            type="primary",
            use_container_width=True,
            help="Empieza con las 32 secciones vacías del template oficial NYL.",
        ):
            st.session_state["pagina"] = "crear_nuevo"
            st.rerun()
    with col_b:
        if st.button("Mejorar documento existente", use_container_width=True):
            st.session_state["pagina"] = "importar"
            st.rerun()
```

- [ ] **Step 4.2: Agregar import y rama del router**

En `app.py`, modificar el import:

```python
from src.ui.pages import (
    auditoria,
    crear_nuevo,
    dashboard,
    entrevista,
    importar,
    onboarding,
    vista_previa,
)
```

Y agregar la rama en `main()`, justo después de la rama `"importar"`:

```python
    elif pagina == "crear_nuevo":
        crear_nuevo.render()
```

- [ ] **Step 4.3: Verificar que la app arranca sin errores de import**

```powershell
python -c "import app; print('OK')"
```

Expected: `OK`.

- [ ] **Step 4.4: Correr toda la batería de tests + ruff + mypy**

```powershell
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/
pytest tests/ -v
```

Expected: ruff clean, mypy clean, **189 passed**.

- [ ] **Step 4.5: Commit**

```powershell
git add app.py
git commit -m "feat: habilitar entrada 'crear documento desde cero' en home"
```

---

## Task 5: Validación end-to-end manual

**Files:**
- (Ninguno — es validación humana en navegador)

**Why:** El flujo nuevo toca múltiples capas (UI, use case, persistencia). Tests automáticos validan piezas; validación end-to-end confirma que el journey completo (crear → onboarding → dashboard → entrevista → exportar DOCX) sigue funcionando.

- [ ] **Step 5.1: Arrancar la app**

```powershell
streamlit run app.py
```

- [ ] **Step 5.2: Validar el flujo "desde cero" end-to-end**

Checklist:
- [ ] Click "Crear nuevo documento" en home → llega a la pantalla nueva.
- [ ] Submit con campos vacíos → muestra error claro, no crashea.
- [ ] Submit con nombre y model_id válidos → llega a `onboarding`.
- [ ] Onboarding se renderiza y permite saltar con "Llenar después" → llega a `dashboard`.
- [ ] Dashboard muestra las 32 secciones, todas en estado "vacía".
- [ ] La metadata muestra el nombre del modelo capturado.
- [ ] Click "Entrevistar" en una sección → entrevista funciona (asumiendo `ANTHROPIC_API_KEY` configurada).
- [ ] Click "Exportar DOCX" → genera y descarga (toleramos celdas vacías para tablas tabulares — es comportamiento correcto cuando no hay datos).
- [ ] Audit trail incluye `documento_creado` como primer evento.

- [ ] **Step 5.3: Validar que el flujo "importar" sigue funcionando (no-regresión)**

Checklist:
- [ ] Click "Mejorar documento existente" → flujo de importar sigue intacto.
- [ ] Subir un .docx real (`SMNYL/Ejemplos actuales/`) → secciones se detectan como antes.
- [ ] Audit trail muestra `documento_importado`.
- [ ] Exportar DOCX desde un doc importado sigue funcionando.

- [ ] **Step 5.4: Si todo pasa, actualizar `status.md`**

Agregar al `status.md` un bloque "Sesión 9" describiendo el feature. (No hacer commit del `status.md` aquí — eso lo decide Alberto al cierre de sesión.)

- [ ] **Step 5.5: Si todo pasa, commit final con tag de feature completado**

(Solo si Alberto confirma que el flujo end-to-end funcionó.)

```powershell
git log --oneline -5
```

Expected: ver los 4 commits anteriores en orden + la rama lista para PR/merge.

---

## Self-review checklist

- [x] **Spec coverage:** crear desde cero (Task 2), pantalla mínima 2 campos opción A (Task 3), botón enabled (Task 4), validación end-to-end (Task 5). El catálogo canónico ya existe — Task 1 solo lo expone.
- [x] **Sin placeholders:** todos los pasos tienen código completo, no "TODO", no "implement later".
- [x] **Consistencia de tipos:** `construir_secciones_vacias()` consistente entre Task 1 y Task 2; `CrearDocumentoEnBlanco` consistente entre Task 2 y Task 3.
- [x] **TDD:** cada task que escribe código tiene primero test, luego implementación.
- [x] **Commits frecuentes:** 4 commits a lo largo del plan + posible 5to al cierre.
- [x] **No-regresión:** `pytest tests/ -v` se corre tras cada task que modifica código existente.
- [x] **Capas respetadas:** UI → Use case → Dominio. `crear_nuevo.py` no toca `Documento` directamente; pasa por `CrearDocumentoEnBlanco`.

---

## Riesgos conocidos y mitigación

| Riesgo | Mitigación |
|---|---|
| El `__init__.py` de `src/core/usecases/` o `src/ui/pages/` tiene formato específico que no respeté | Step 2.4 y Step 3.2 dicen "verificar el formato exacto antes de editar" |
| Algún test existente depende de que `_construir_secciones_iniciales` siga siendo privada | Step 1.6 corre la batería completa; si algo se rompe, el test fallará y se ajusta |
| El onboarding asume que ya existe metadata del docx parseado | Verificado: `onboarding.py:22-39` solo necesita `documento_actual_id`; metadata se popula opcional. No se rompe. |
| `ANTHROPIC_API_KEY` no configurada → la entrevista falla en Step 5.2 | Aceptable — se documenta como bloqueo conocido, no impide validar el resto del flujo |

---

## Estimación

- Task 1: 30-45 min (refactor sencillo + tests).
- Task 2: 45-60 min (use case + tests).
- Task 3: 30-45 min (UI Streamlit).
- Task 4: 15-20 min (cambios menores en app.py).
- Task 5: 30-45 min (validación humana).

**Total: ~3-4 horas de trabajo concentrado.**
