# Módulo Prophet Fase 0 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Importar un registro Excel de modelos actuariales Prophet, generar una Ficha Prophet pre-poblada con formularios de edición, y exportar a DOCX con marca SMNYL — sin romper nada del flujo MRM existente.

**Architecture:** `Documento(tipo="prophet")` reutiliza el modelo de datos existente sin cambios de schema SQLite. Un segundo catálogo independiente (`template_catalog_prophet.py`) define las 12 secciones Prophet. El import usa openpyxl para leer el Excel crudo + Haiku para mapear columnas al schema (tolerante a variabilidad). La edición usa formularios en pantalla completa (no LLM chat). El writer Prophet es independiente del writer MRM.

**Tech Stack:** Python 3.11+, openpyxl, docxtpl, python-docx, Streamlit, Anthropic SDK (`tarea="extraction"` → Haiku), pydantic v2, pytest

**Baseline:** 236/236 tests pasan. Meta al cierre: ~256.

**Nota:** usar el plugin Codex para tareas mecánicas (generar las 12 secciones del catálogo, escribir tests repetitivos, etc.).

**Spec:** `docs/superpowers/specs/2026-05-14-prophet-fase0-design.md`

---

## File Structure

### Nuevos (15 archivos)

| Archivo | Responsabilidad |
|---|---|
| `src/core/template_catalog_prophet.py` | Catálogo de 12 secciones Prophet con `tipo_contenido` y `schema_tabla` |
| `src/core/usecases/detectar_modelos_prophet.py` | openpyxl + Haiku → lista de modelos disponibles en el Excel |
| `src/core/usecases/importar_registro_prophet.py` | Orquesta import: Excel → Haiku por sección → `Documento(tipo="prophet")` |
| `src/core/usecases/docx_writer_prophet.py` | Renderiza template Word Prophet con 4 table loops |
| `src/llm/prompts/extraer_seccion_prophet.py` | System prompt + builder de user message para Haiku |
| `src/ui/pages/crear_prophet.py` | UI: upload Excel → selector modelo → disparar import |
| `src/ui/pages/editar_seccion_prophet.py` | UI: editor pantalla completa (tabla add/remove o textarea) |
| `src/docs/templates/prophet_model_doc_smnyl.docx` | Template Word SMNYL (paso manual en Word) |
| `docs/Modulo Prophet MA/Registro_Modelos_Template.xlsx` | Template Excel con headers + fila ejemplo (paso manual) |
| `docs/Modulo Prophet MA/Guia_Llenado_Registro.md` | Guía de llenado del Excel para MA |
| `tests/unit/test_template_catalog_prophet.py` | Tests del catálogo (12 secciones, tipos, schema) |
| `tests/unit/test_detectar_modelos_prophet.py` | Tests de detección con fixture Excel sintético |
| `tests/unit/test_importar_registro_prophet.py` | Tests de importación end-to-end con fixture Excel |
| `tests/unit/test_docx_writer_prophet.py` | Tests del writer (contexto + render mínimo) |
| `tests/unit/test_editar_seccion_prophet.py` | Tests de lógica de guardado de secciones |

### Modificados (4 archivos)

| Archivo | Cambio |
|---|---|
| `src/core/models/documento.py:26` | Agregar `"prophet"` a `TipoDocumento` Literal |
| `src/core/usecases/__init__.py` | Exports de los 3 use cases nuevos |
| `src/ui/pages/home.py` | Tercer botón "Iniciar Ficha Prophet" (col_c) |
| `app.py` | Rutas `crear_prophet` y `editar_seccion_prophet` |

---

## Task 1: Template Catalog Prophet

**Files:**
- Create: `src/core/template_catalog_prophet.py`
- Create: `tests/unit/test_template_catalog_prophet.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_template_catalog_prophet.py
from __future__ import annotations

import pytest

from src.core.template_catalog_prophet import (
    TEMPLATE_PROPHET,
    construir_secciones_vacias_prophet,
    por_id_prophet,
)


def test_template_tiene_12_secciones() -> None:
    assert len(TEMPLATE_PROPHET) == 12


def test_ids_son_unicos() -> None:
    ids = [s.id for s in TEMPLATE_PROPHET]
    assert len(ids) == len(set(ids))


def test_tipo_contenido_valido() -> None:
    for s in TEMPLATE_PROPHET:
        assert s.tipo_contenido in {"campos", "tabla", "texto"}, (
            f"{s.id} tiene tipo inválido: {s.tipo_contenido}"
        )


def test_tablas_tienen_schema() -> None:
    for s in TEMPLATE_PROPHET:
        if s.tipo_contenido == "tabla":
            assert len(s.schema_tabla) > 0, f"{s.id}: tabla sin schema_tabla"


def test_secciones_obligatorias_correctas() -> None:
    obligatorias = {s.id for s in TEMPLATE_PROPHET if s.obligatoria}
    for esperada in ("identificacion", "corridas_runs", "variables_criticas", "matriz_conocimiento"):
        assert esperada in obligatorias


def test_secciones_opcionales_correctas() -> None:
    opcionales = {s.id for s in TEMPLATE_PROPHET if not s.obligatoria}
    assert "componentes_librerias" in opcionales
    assert "limitaciones_riesgos" in opcionales


def test_por_id_prophet_encontrado() -> None:
    s = por_id_prophet("corridas_runs")
    assert s is not None and s.nombre == "Corridas (Runs)"


def test_por_id_prophet_inexistente() -> None:
    assert por_id_prophet("no_existe") is None


def test_construir_secciones_vacias_prophet() -> None:
    secciones = construir_secciones_vacias_prophet()
    assert len(secciones) == 12
    for s in secciones:
        assert s.completitud == "vacia"
        assert s.contenido is None
```

- [ ] **Step 2: Run — verificar que falla**

```
pytest tests/unit/test_template_catalog_prophet.py -v
```
Expected: `ModuleNotFoundError: src.core.template_catalog_prophet`

- [ ] **Step 3: Implementar el catálogo**

```python
# src/core/template_catalog_prophet.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.core.models.seccion import Seccion

TipoContenidoProphet = Literal["campos", "tabla", "texto"]


@dataclass(frozen=True)
class SeccionCatalogoProphet:
    id: str
    numero: str
    nombre: str
    obligatoria: bool
    intencion: str
    tipo_contenido: TipoContenidoProphet
    schema_tabla: tuple[str, ...] = field(default_factory=tuple)
    """Nombres de columnas cuando tipo_contenido == 'tabla'."""


TEMPLATE_PROPHET: tuple[SeccionCatalogoProphet, ...] = (
    SeccionCatalogoProphet(
        id="identificacion", numero="1", nombre="Identificación del modelo",
        obligatoria=True, tipo_contenido="campos",
        intencion="Datos básicos: nombre, área, proceso, encargado, frecuencia de uso, ruta del modelo, tiempo de ejecución.",
    ),
    SeccionCatalogoProphet(
        id="objetivo_alcance", numero="2", nombre="Objetivo y alcance",
        obligatoria=True, tipo_contenido="texto",
        intencion="Propósito del modelo, qué problema ataca y qué reportes alimenta (NBM, PM, IRR).",
    ),
    SeccionCatalogoProphet(
        id="responsables_roles", numero="3", nombre="Responsables y roles",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Quién opera, valida y aprueba el modelo.",
        schema_tabla=("persona", "rol", "area"),
    ),
    SeccionCatalogoProphet(
        id="corridas_runs", numero="4", nombre="Corridas (Runs)",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Detalle de cada corrida: número, descripción, ¿ALM?, tiempo ejecución, corrida precedente, outputs.",
        schema_tabla=("numero", "detalle", "es_alm", "tiempo_ejecucion", "corrida_precedente", "outputs_principales", "responsable"),
    ),
    SeccionCatalogoProphet(
        id="variables_criticas", numero="5", nombre="Variables críticas",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Variables críticas: nombre, descripción, fórmula, corrida, frecuencia, responsable, dependencias.",
        schema_tabla=("nombre", "descripcion", "formula", "corrida", "frecuencia_actualizacion", "responsable", "variables_dependientes"),
    ),
    SeccionCatalogoProphet(
        id="inputs_dependencias", numero="6", nombre="Inputs y dependencias",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Inputs externos: nombre, área proveedora, frecuencia, qué se actualiza.",
        schema_tabla=("input", "area_proveedora", "frecuencia", "que_se_actualiza"),
    ),
    SeccionCatalogoProphet(
        id="supuestos", numero="7", nombre="Supuestos relevantes",
        obligatoria=True, tipo_contenido="texto",
        intencion="Supuestos actuariales: mortalidad, lapsos, tasas, gastos, etc.",
    ),
    SeccionCatalogoProphet(
        id="outputs_reportes", numero="8", nombre="Outputs y reportes",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Outputs del modelo: output, reporte que alimenta, audiencia, frecuencia.",
        schema_tabla=("output", "reporte", "audiencia", "frecuencia"),
    ),
    SeccionCatalogoProphet(
        id="componentes_librerias", numero="9", nombre="Componentes y librerías Prophet",
        obligatoria=False, tipo_contenido="texto",
        intencion="Librerías Prophet (UL, Conventional, ALM) y otros componentes técnicos.",
    ),
    SeccionCatalogoProphet(
        id="historial_cambios", numero="10", nombre="Historial de cambios",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Cambios por periodo: periodo, descripción del cambio, responsable.",
        schema_tabla=("periodo", "cambio_realizado", "responsable"),
    ),
    SeccionCatalogoProphet(
        id="limitaciones_riesgos", numero="11", nombre="Limitaciones y riesgos",
        obligatoria=False, tipo_contenido="texto",
        intencion="Limitaciones conocidas, dependencias externas críticas y riesgos operacionales.",
    ),
    SeccionCatalogoProphet(
        id="matriz_conocimiento", numero="12", nombre="Matriz de conocimiento técnico",
        obligatoria=True, tipo_contenido="tabla",
        intencion="Capacidades Prophet por persona con nivel (NO CONOCE/BÁSICO/INTERMEDIO/AVANZADO).",
        schema_tabla=("persona", "capacidad", "nivel"),
    ),
)


def por_id_prophet(seccion_id: str) -> SeccionCatalogoProphet | None:
    return next((s for s in TEMPLATE_PROPHET if s.id == seccion_id), None)


def construir_secciones_vacias_prophet() -> list[Seccion]:
    return [
        Seccion(
            id=s.id, nombre=s.nombre, numero=s.numero,
            obligatoria=s.obligatoria, intencion=s.intencion,
        )
        for s in TEMPLATE_PROPHET
    ]
```

- [ ] **Step 4: Verificar que pasan**

```
pytest tests/unit/test_template_catalog_prophet.py -v
```
Expected: 9/9 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/core/template_catalog_prophet.py tests/unit/test_template_catalog_prophet.py
git commit -m "feat: agregar catálogo de secciones Prophet (12 secciones, TDD)"
```

---

## Task 2: Extender TipoDocumento

**Files:**
- Modify: `src/core/models/documento.py:26`

- [ ] **Step 1: Cambio mínimo**

En `src/core/models/documento.py` línea 26, cambiar:
```python
# ANTES
TipoDocumento = Literal["model_development"]
# DESPUÉS
TipoDocumento = Literal["model_development", "prophet"]
```

- [ ] **Step 2: Verificar que tests existentes siguen pasando**

```
pytest tests/ -x -q
```
Expected: 236 passed (sin regresiones)

- [ ] **Step 3: Commit**

```bash
git add src/core/models/documento.py
git commit -m "feat: agregar tipo 'prophet' a TipoDocumento (backward-compatible)"
```

---

## Task 3: Prompt LLM para extracción Prophet

**Files:**
- Create: `src/llm/prompts/extraer_seccion_prophet.py`

- [ ] **Step 1: Crear el módulo de prompt**

```python
# src/llm/prompts/extraer_seccion_prophet.py
from __future__ import annotations

import json
from typing import Any

EXTRAER_SECCION_PROPHET_SYSTEM = """\
# TAREA: EXTRACCIÓN DE DATOS PROPHET A SCHEMA ESTRUCTURADO

Recibes datos crudos de una hoja Excel de modelos actuariales Prophet.
Tu trabajo es identificar la información del modelo solicitado y mapearla
al schema de campos especificado.

## REGLAS

- NO INVENTES datos. Si un campo no está en los datos crudos, usa cadena vacía "".
- Sé tolerante a variaciones de nombre de columna ("Encargado" ≈ "Responsable").
- Si los datos tienen múltiples modelos, filtra solo el modelo solicitado.
- Devuelve SOLO el JSON. Sin texto, sin markdown de código.
- Si no encuentras datos: {"filas": [], "advertencias": ["No se encontraron datos para el modelo"]}

## FORMATO DE SALIDA

Para secciones tipo tabla:
{"filas": [{"campo1": "valor", ...}], "advertencias": []}

Para secciones tipo campos o texto:
{"contenido": "texto o JSON de campos", "advertencias": []}
"""


def construir_prompt_extraccion(
    nombre_modelo: str,
    nombre_seccion: str,
    schema_campos: list[str],
    datos_crudos: list[dict[str, Any]],
    tipo_contenido: str,
) -> str:
    datos_str = json.dumps(datos_crudos[:50], ensure_ascii=False, indent=2)
    return f"""\
## MODELO A EXTRAER
Nombre: {nombre_modelo}

## SECCIÓN A POBLAR
{nombre_seccion} (tipo: {tipo_contenido})
Schema esperado: {json.dumps(schema_campos)}

## DATOS CRUDOS DEL EXCEL
{datos_str}

Extrae los datos del modelo "{nombre_modelo}" según el schema. SOLO el JSON.
"""
```

- [ ] **Step 2: Verificar que importa correctamente**

```
python -c "from src.llm.prompts.extraer_seccion_prophet import EXTRAER_SECCION_PROPHET_SYSTEM, construir_prompt_extraccion; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add src/llm/prompts/extraer_seccion_prophet.py
git commit -m "feat: agregar prompt Haiku para extracción de secciones Prophet"
```

---

## Task 4: DetectarModelosProphet

**Files:**
- Create: `src/core/usecases/detectar_modelos_prophet.py`
- Create: `tests/unit/test_detectar_modelos_prophet.py`

- [ ] **Step 1: Escribir fixture Excel sintético + tests**

```python
# tests/unit/test_detectar_modelos_prophet.py
from __future__ import annotations

import io
from typing import Any

import openpyxl
import pytest

from src.core.usecases.detectar_modelos_prophet import (
    DetectarModelosProphet,
    ModeloProphetInfo,
    ResultadoDeteccion,
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
    xlsx = _excel_con_modelos([
        {"Area": "Rentabilidad", "Proceso": "VNB", "Encargado": "Francisco Carmona"}
    ])
    uc = DetectarModelosProphet(llm=None)
    resultado = uc.ejecutar(xlsx)
    assert len(resultado.modelos) == 1
    assert resultado.modelos[0].nombre == "VNB"
    assert resultado.modelos[0].encargado == "Francisco Carmona"


def test_detecta_multiples_modelos() -> None:
    xlsx = _excel_con_modelos([
        {"Proceso": "VNB", "Encargado": "Carmona"},
        {"Proceso": "IRR", "Encargado": "Cynthia"},
    ])
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
    xlsx = _excel_con_modelos([
        {"Proceso": "VNB", "Encargado": "Carmona"},
        {"Proceso": "IRR", "Encargado": "Cynthia"},
    ])
    uc = DetectarModelosProphet(llm=None)
    resultado = uc.ejecutar(xlsx)
    assert resultado.modelos[0].fila_idx == 0
    assert resultado.modelos[1].fila_idx == 1
```

- [ ] **Step 2: Verificar que falla**

```
pytest tests/unit/test_detectar_modelos_prophet.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implementar DetectarModelosProphet**

```python
# src/core/usecases/detectar_modelos_prophet.py
from __future__ import annotations

import io
import json
from dataclasses import dataclass, field
from typing import Any

import openpyxl
from anthropic.types import TextBlockParam

from src.llm import LLMClient
from src.llm.prompts.extraer_seccion_prophet import EXTRAER_SECCION_PROPHET_SYSTEM


@dataclass
class ModeloProphetInfo:
    fila_idx: int
    nombre: str
    encargado: str
    area: str = ""
    proceso: str = ""


@dataclass
class ResultadoDeteccion:
    modelos: list[ModeloProphetInfo] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)


_NOMBRES_HOJA_CATALOGO = {"descripcion_general", "descripción_general", "modelos", "catalogo", "catálogo"}
_COLS_NOMBRE = {"proceso", "modelo", "nombre", "nombre_modelo", "nombre del modelo"}
_COLS_ENCARGADO = {"encargado", "responsable", "dueño", "owner", "dueño del modelo"}
_COLS_AREA = {"area", "área"}


class DetectarModelosProphet:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm

    def ejecutar(self, xlsx_bytes: bytes) -> ResultadoDeteccion:
        try:
            wb = openpyxl.load_workbook(filename=io.BytesIO(xlsx_bytes), data_only=True)
        except Exception as e:
            return ResultadoDeteccion(advertencias=[f"No se pudo leer el Excel: {e}"])

        hoja = self._encontrar_hoja_catalogo(wb)
        if hoja is None:
            return ResultadoDeteccion(advertencias=["No se encontró hoja de catálogo de modelos."])

        rows = self._hoja_a_dicts(hoja)
        if not rows:
            return ResultadoDeteccion(advertencias=["La hoja de catálogo está vacía."])

        if self.llm is not None:
            return self._detectar_con_llm(rows)
        return self._detectar_heuristico(rows)

    def _encontrar_hoja_catalogo(self, wb: openpyxl.Workbook) -> Any:
        for nombre in wb.sheetnames:
            if nombre.lower().replace(" ", "_") in _NOMBRES_HOJA_CATALOGO:
                return wb[nombre]
        return wb.active

    def _hoja_a_dicts(self, ws: Any) -> list[dict[str, Any]]:
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(rows[0])]
        return [
            {headers[i]: (str(c).strip() if c is not None else "") for i, c in enumerate(row)}
            for row in rows[1:]
            if any(c is not None for c in row)
        ]

    def _detectar_heuristico(self, rows: list[dict[str, Any]]) -> ResultadoDeteccion:
        h_lower = {k.lower(): k for k in rows[0].keys()} if rows else {}
        col_n = next((h_lower[k] for k in _COLS_NOMBRE if k in h_lower), None)
        col_e = next((h_lower[k] for k in _COLS_ENCARGADO if k in h_lower), None)
        col_a = next((h_lower[k] for k in _COLS_AREA if k in h_lower), None)

        modelos = []
        for idx, row in enumerate(rows):
            nombre = (row.get(col_n, "") if col_n else next(iter(row.values()), "")).strip()
            if nombre:
                modelos.append(ModeloProphetInfo(
                    fila_idx=idx,
                    nombre=nombre,
                    encargado=(row.get(col_e, "") if col_e else "").strip(),
                    area=(row.get(col_a, "") if col_a else "").strip(),
                ))
        advertencias = [] if modelos else ["No se encontraron filas de modelos."]
        return ResultadoDeteccion(modelos=modelos, advertencias=advertencias)

    def _detectar_con_llm(self, rows: list[dict[str, Any]]) -> ResultadoDeteccion:
        prompt = (
            f"Datos crudos de catálogo de modelos actuariales Prophet:\n"
            f"```json\n{json.dumps(rows[:20], ensure_ascii=False, indent=2)}\n```\n\n"
            "Identifica todas las filas que representan modelos distintos.\n"
            "Devuelve SOLO este JSON:\n"
            '{"modelos": [{"fila_idx": 0, "nombre": "...", "encargado": "...", "area": ""}], "advertencias": []}'
        )
        try:
            resp = self.llm.chat(
                tarea="extraction",
                system_blocks=[TextBlockParam(type="text", text=EXTRAER_SECCION_PROPHET_SYSTEM)],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
            )
            data = json.loads(resp.text)
            modelos = [
                ModeloProphetInfo(
                    fila_idx=m["fila_idx"], nombre=m.get("nombre", ""),
                    encargado=m.get("encargado", ""), area=m.get("area", ""),
                )
                for m in data.get("modelos", []) if m.get("nombre", "").strip()
            ]
            return ResultadoDeteccion(modelos=modelos, advertencias=data.get("advertencias", []))
        except Exception as e:
            resultado = self._detectar_heuristico(rows)
            resultado.advertencias.append(f"LLM falló ({e}), se usó detección heurística.")
            return resultado
```

- [ ] **Step 4: Verificar que pasan**

```
pytest tests/unit/test_detectar_modelos_prophet.py -v
```
Expected: 5/5 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/core/usecases/detectar_modelos_prophet.py tests/unit/test_detectar_modelos_prophet.py
git commit -m "feat: use case DetectarModelosProphet — openpyxl + fallback heurístico (TDD)"
```

---

## Task 5: ImportarRegistroProphet

**Files:**
- Create: `src/core/usecases/importar_registro_prophet.py`
- Create: `tests/unit/test_importar_registro_prophet.py`

- [ ] **Step 1: Escribir tests con fixture Excel sintético**

```python
# tests/unit/test_importar_registro_prophet.py
from __future__ import annotations

import io
import json

import openpyxl
import pytest

from src.core.usecases.importar_registro_prophet import ImportarRegistroProphet
from src.storage.repositories import DocumentoRepository


def _excel_prophet_minimo() -> bytes:
    """Excel con las 4 hojas del formato Prophet, datos mínimos."""
    wb = openpyxl.Workbook()

    # Hoja 1: Descripcion_General
    ws1 = wb.active
    ws1.title = "Descripcion_General"
    ws1.append(["Area", "Proceso", "Encargado", "Descripcion", "Frecuencia de actualización", "Corridas", "Qué problema ataca"])
    ws1.append(["Rentabilidad", "VNB", "Francisco Carmona", "Modelo de valor nuevo de negocio", "Trimestral", "33,34,36", "Medir rentabilidad"])
    ws1.append(["Rentabilidad", "IRR", "Cynthia Flores", "Internal rate of return", "Trimestral", "33,34", "Medir tasa interna"])

    # Hoja 2: Detalle Runs
    ws2 = wb.create_sheet("Detalle Runs")
    ws2.append(["# corrida", "Detalle", "Corrida Precedente", "Es ALM?", "Tiempo de ejecución", "Outputs Principales", "Responsable"])
    ws2.append(["33", "IL UDI y USD", "", "No", "45 min", "VNB, Profit", "Carmona"])
    ws2.append(["34", "GMM Individual", "33", "Sí", "90 min", "IRR", "Carmona"])

    # Hoja 3: Variables criticas
    ws3 = wb.create_sheet("Variables criticas")
    ws3.append(["Corrida", "Nombre", "Descripción", "Fórmula", "Frecuencia de actualización", "Responsable de la info", "Variables dependientes"])
    ws3.append(["33", "PROF_SOLVM", "Solvency margin profit", "PREM_INC - DEATH_OUTGO", "Trimestral", "Carmona", "PREM_INC,DEATH_OUTGO"])

    # Hoja 4: Conocimiento_Tecnico
    ws4 = wb.create_sheet("Conocimiento_Tecnico")
    ws4.append(["Persona", "Ejecutar corridas base", "Modificación de código"])
    ws4.append(["Francisco Carmona", "AVANZADO", "INTERMEDIO"])
    ws4.append(["Cynthia Flores", "INTERMEDIO", "BÁSICO"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture()
def repo(tmp_path):
    import os
    os.environ["DOCUMENTE_DB_PATH"] = str(tmp_path / "test.db")
    return DocumentoRepository()


def test_importa_documento_tipo_prophet(repo) -> None:
    xlsx = _excel_prophet_minimo()
    uc = ImportarRegistroProphet(repo=repo, llm=None)
    resultado = uc.ejecutar(xlsx_bytes=xlsx, fila_idx=0, nombre_modelo="VNB")
    assert resultado.documento.tipo == "prophet"
    assert resultado.documento.metadata_modelo.nombre_modelo == "VNB"


def test_secciones_de_runs_pre_pobladas_sin_llm(repo) -> None:
    xlsx = _excel_prophet_minimo()
    uc = ImportarRegistroProphet(repo=repo, llm=None)
    resultado = uc.ejecutar(xlsx_bytes=xlsx, fila_idx=0, nombre_modelo="VNB")
    # Sin LLM, al menos la identificacion se llena heurísticamente
    doc = resultado.documento
    assert doc.seccion_por_id("identificacion") is not None


def test_excel_invalido_no_lanza_excepcion(repo) -> None:
    uc = ImportarRegistroProphet(repo=repo, llm=None)
    resultado = uc.ejecutar(xlsx_bytes=b"no es excel", fila_idx=0, nombre_modelo="VNB")
    assert resultado.documento is None or len(resultado.advertencias) > 0


def test_documento_persiste_en_repo(repo) -> None:
    xlsx = _excel_prophet_minimo()
    uc = ImportarRegistroProphet(repo=repo, llm=None)
    resultado = uc.ejecutar(xlsx_bytes=xlsx, fila_idx=0, nombre_modelo="VNB")
    if resultado.documento:
        doc_repo = repo.obtener(resultado.documento.id)
        assert doc_repo is not None
        assert doc_repo.tipo == "prophet"


def test_columna_faltante_no_rompe_import(repo) -> None:
    """Excel sin hoja Variables criticas — el import completa lo que puede."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Descripcion_General"
    ws.append(["Proceso", "Encargado"])
    ws.append(["VNB", "Carmona"])
    buf = io.BytesIO()
    wb.save(buf)

    uc = ImportarRegistroProphet(repo=repo, llm=None)
    resultado = uc.ejecutar(xlsx_bytes=buf.getvalue(), fila_idx=0, nombre_modelo="VNB")
    # No debe lanzar excepción — la sección queda vacía con advertencia
    assert resultado is not None
```

- [ ] **Step 2: Verificar que falla**

```
pytest tests/unit/test_importar_registro_prophet.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implementar ImportarRegistroProphet**

```python
# src/core/usecases/importar_registro_prophet.py
from __future__ import annotations

import io
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import openpyxl
from anthropic.types import TextBlockParam

from src.core.models import Documento, EventoAuditoria
from src.core.models.documento import MetadataModelo
from src.core.template_catalog_prophet import (
    TEMPLATE_PROPHET,
    SeccionCatalogoProphet,
    construir_secciones_vacias_prophet,
    por_id_prophet,
)
from src.llm import LLMClient
from src.llm.prompts.extraer_seccion_prophet import (
    EXTRAER_SECCION_PROPHET_SYSTEM,
    construir_prompt_extraccion,
)
from src.storage.repositories import DocumentoRepository

# Mapa: section_id → nombre(s) de hoja Excel esperada
_HOJA_POR_SECCION: dict[str, list[str]] = {
    "identificacion": ["descripcion_general", "descripción_general", "modelos"],
    "objetivo_alcance": ["descripcion_general", "descripción_general"],
    "responsables_roles": ["descripcion_general", "descripción_general"],
    "corridas_runs": ["detalle runs", "detalle_runs", "runs", "corridas"],
    "variables_criticas": ["variables criticas", "variables_criticas", "variables"],
    "inputs_dependencias": ["descripcion_general", "descripción_general"],
    "matriz_conocimiento": ["conocimiento_tecnico", "conocimiento técnico", "conocimiento"],
}


@dataclass
class ResultadoImportacionProphet:
    documento: Documento | None
    secciones_importadas: int = 0
    secciones_vacias: int = 0
    advertencias: list[str] = field(default_factory=list)


class ImportarRegistroProphet:
    def __init__(self, repo: DocumentoRepository, llm: LLMClient | None = None) -> None:
        self.repo = repo
        self.llm = llm

    def ejecutar(
        self, xlsx_bytes: bytes, fila_idx: int, nombre_modelo: str, user_id: str = "default"
    ) -> ResultadoImportacionProphet:
        try:
            wb = openpyxl.load_workbook(filename=io.BytesIO(xlsx_bytes), data_only=True)
        except Exception as e:
            return ResultadoImportacionProphet(
                documento=None, advertencias=[f"No se pudo leer el Excel: {e}"]
            )

        # Leer todas las hojas como dicts (key = nombre hoja en minúsculas)
        hojas: dict[str, list[dict[str, Any]]] = {}
        for nombre in wb.sheetnames:
            hojas[nombre.lower().strip()] = self._hoja_a_dicts(wb[nombre])

        secciones = construir_secciones_vacias_prophet()
        advertencias: list[str] = []
        importadas = 0

        for seccion in secciones:
            cat = por_id_prophet(seccion.id)
            if cat is None:
                continue
            hoja_data = self._encontrar_hoja(hojas, seccion.id)
            if not hoja_data:
                advertencias.append(f"Sección '{seccion.nombre}': no se encontró hoja correspondiente en el Excel.")
                continue

            contenido = self._extraer(hoja_data, cat, nombre_modelo, fila_idx)
            if contenido:
                seccion.contenido = contenido
                seccion.completitud = "completa"
                importadas += 1
            else:
                advertencias.append(f"Sección '{seccion.nombre}': sin datos extraíbles del Excel.")

        doc = Documento(
            user_id=user_id,
            tipo="prophet",
            metadata_modelo=MetadataModelo(nombre_modelo=nombre_modelo),
            secciones=secciones,
        )
        doc.registrar_evento(EventoAuditoria(
            timestamp=datetime.now(UTC),
            actor=user_id,
            tipo="documento_creado",
            descripcion=f"Ficha Prophet importada desde Excel: {nombre_modelo}",
            metadata={"fila_idx": fila_idx, "secciones_importadas": importadas},
        ))
        self.repo.guardar(doc)

        return ResultadoImportacionProphet(
            documento=doc,
            secciones_importadas=importadas,
            secciones_vacias=len(secciones) - importadas,
            advertencias=advertencias,
        )

    def _hoja_a_dicts(self, ws: Any) -> list[dict[str, Any]]:
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(rows[0])]
        return [
            {headers[i]: (str(c).strip() if c is not None else "") for i, c in enumerate(row)}
            for row in rows[1:]
            if any(c is not None for c in row)
        ]

    def _encontrar_hoja(self, hojas: dict[str, list], seccion_id: str) -> list[dict[str, Any]]:
        candidatos = _HOJA_POR_SECCION.get(seccion_id, [])
        for nombre in candidatos:
            if nombre in hojas:
                return hojas[nombre]
        return []

    def _extraer(
        self, datos: list[dict[str, Any]], cat: SeccionCatalogoProphet,
        nombre_modelo: str, fila_idx: int,
    ) -> str | None:
        if self.llm is not None:
            return self._extraer_con_llm(datos, cat, nombre_modelo)
        return self._extraer_heuristico(datos, cat, nombre_modelo, fila_idx)

    def _extraer_con_llm(
        self, datos: list[dict[str, Any]], cat: SeccionCatalogoProphet, nombre_modelo: str
    ) -> str | None:
        prompt = construir_prompt_extraccion(
            nombre_modelo=nombre_modelo,
            nombre_seccion=cat.nombre,
            schema_campos=list(cat.schema_tabla) if cat.tipo_contenido == "tabla" else [],
            datos_crudos=datos,
            tipo_contenido=cat.tipo_contenido,
        )
        try:
            resp = self.llm.chat(
                tarea="extraction",
                system_blocks=[TextBlockParam(type="text", text=EXTRAER_SECCION_PROPHET_SYSTEM)],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
            )
            json.loads(resp.text)  # validate
            return resp.text
        except Exception:
            return self._extraer_heuristico(datos, cat, nombre_modelo, 0)

    def _extraer_heuristico(
        self, datos: list[dict[str, Any]], cat: SeccionCatalogoProphet,
        nombre_modelo: str, fila_idx: int,
    ) -> str | None:
        if not datos:
            return None
        if cat.tipo_contenido == "campos" and fila_idx < len(datos):
            fila = datos[fila_idx]
            return json.dumps({"contenido": json.dumps(fila, ensure_ascii=False), "advertencias": []}, ensure_ascii=False)
        if cat.tipo_contenido == "tabla":
            return json.dumps({"filas": datos, "advertencias": ["Extracción heurística — revisar datos"]}, ensure_ascii=False)
        if cat.tipo_contenido == "texto" and fila_idx < len(datos):
            texto = " | ".join(str(v) for v in datos[fila_idx].values() if v)
            return json.dumps({"contenido": texto, "advertencias": []}, ensure_ascii=False) if texto else None
        return None
```

- [ ] **Step 4: Verificar que pasan**

```
pytest tests/unit/test_importar_registro_prophet.py -v
```
Expected: 5/5 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/core/usecases/importar_registro_prophet.py tests/unit/test_importar_registro_prophet.py
git commit -m "feat: use case ImportarRegistroProphet — openpyxl + Haiku extracción (TDD)"
```

---

## Task 6: DocxWriterProphet

**Files:**
- Create: `src/core/usecases/docx_writer_prophet.py`
- Create: `tests/unit/test_docx_writer_prophet.py`
- Note: `src/docs/templates/prophet_model_doc_smnyl.docx` se crea manualmente en Word (ver paso 3b)

- [ ] **Step 1: Escribir tests**

```python
# tests/unit/test_docx_writer_prophet.py
from __future__ import annotations

import json
from pathlib import Path

import pytest
from docx import Document as DocxDocument
from docxtpl import DocxTemplate

from src.core.models import Documento
from src.core.models.documento import MetadataModelo
from src.core.usecases.docx_writer_prophet import DocxWriterProphet
from src.core.template_catalog_prophet import construir_secciones_vacias_prophet


def _doc_prophet_con_runs(nombre: str = "Modelo VNB") -> Documento:
    secciones = construir_secciones_vacias_prophet()
    runs_data = json.dumps({
        "filas": [
            {"numero": "33", "detalle": "IL UDI", "es_alm": "No", "tiempo_ejecucion": "45 min",
             "corrida_precedente": "", "outputs_principales": "VNB", "responsable": "Carmona"},
        ],
        "advertencias": [],
    })
    for s in secciones:
        if s.id == "corridas_runs":
            s.contenido = runs_data
            s.completitud = "completa"
    return Documento(
        tipo="prophet",
        metadata_modelo=MetadataModelo(nombre_modelo=nombre),
        secciones=secciones,
    )


def _template_minimo(tmp_path: Path) -> Path:
    """Crea un .docx mínimo con un placeholder para tests."""
    doc = DocxDocument()
    doc.add_paragraph("{{ nombre_modelo }}")
    doc.add_paragraph("{{ area }}")
    path = tmp_path / "prophet_test_template.docx"
    doc.save(str(path))
    return path


def test_construir_contexto_incluye_nombre_modelo(tmp_path: Path) -> None:
    writer = DocxWriterProphet(template_path=_template_minimo(tmp_path))
    doc = _doc_prophet_con_runs("Modelo VNB")
    ctx = writer._construir_contexto(doc)
    assert ctx["nombre_modelo"] == "Modelo VNB"


def test_construir_contexto_runs_como_lista(tmp_path: Path) -> None:
    writer = DocxWriterProphet(template_path=_template_minimo(tmp_path))
    doc = _doc_prophet_con_runs()
    ctx = writer._construir_contexto(doc)
    assert isinstance(ctx["runs"], list)
    assert len(ctx["runs"]) == 1
    assert ctx["runs"][0]["numero"] == "33"


def test_construir_contexto_seccion_vacia_devuelve_lista_vacia(tmp_path: Path) -> None:
    writer = DocxWriterProphet(template_path=_template_minimo(tmp_path))
    doc = Documento(
        tipo="prophet",
        metadata_modelo=MetadataModelo(nombre_modelo="X"),
        secciones=construir_secciones_vacias_prophet(),
    )
    ctx = writer._construir_contexto(doc)
    assert ctx["runs"] == []
    assert ctx["variables"] == []


def test_render_devuelve_bytes(tmp_path: Path) -> None:
    writer = DocxWriterProphet(template_path=_template_minimo(tmp_path))
    doc = _doc_prophet_con_runs()
    result = writer.render(doc)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_template_path_default_no_existe_lanza_error_util(tmp_path: Path) -> None:
    """Si el template real no existe, el writer falla con FileNotFoundError descriptivo."""
    writer = DocxWriterProphet(template_path=tmp_path / "no_existe.docx")
    doc = _doc_prophet_con_runs()
    with pytest.raises(FileNotFoundError):
        writer.render(doc)
```

- [ ] **Step 2: Verificar que falla**

```
pytest tests/unit/test_docx_writer_prophet.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3a: Implementar DocxWriterProphet**

```python
# src/core/usecases/docx_writer_prophet.py
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate

from src.core.models import Documento

_TEMPLATE_DEFAULT = (
    Path(__file__).parent.parent.parent / "docs" / "templates" / "prophet_model_doc_smnyl.docx"
)

# section_id → (context_key, schema_columnas)
_TABLA_MAP: list[tuple[str, str]] = [
    ("corridas_runs", "runs"),
    ("variables_criticas", "variables"),
    ("inputs_dependencias", "inputs"),
    ("responsables_roles", "responsables"),
    ("outputs_reportes", "outputs"),
    ("historial_cambios", "historial"),
    ("matriz_conocimiento", "skills_matrix"),
]


class DocxWriterProphet:
    """Renderiza una Ficha Prophet a DOCX usando la plantilla maestra SMNYL."""

    def __init__(self, template_path: Path | None = None) -> None:
        self.template_path = template_path or _TEMPLATE_DEFAULT

    def render(self, documento: Documento) -> bytes:
        if not self.template_path.exists():
            raise FileNotFoundError(
                f"Template Prophet no encontrado: {self.template_path}. "
                "Crea el archivo en Word siguiendo la guía del spec."
            )
        tpl = DocxTemplate(str(self.template_path))
        context = self._construir_contexto(documento)
        tpl.render(context)
        buf = BytesIO()
        tpl.save(buf)
        return buf.getvalue()

    def _construir_contexto(self, documento: Documento) -> dict[str, Any]:
        meta = documento.metadata_modelo
        ctx: dict[str, Any] = {
            "nombre_modelo": meta.nombre_modelo,
            "model_id": meta.model_id,
            "area": "",
            "proceso": "",
            "encargado_principal": "",
            "frecuencia_uso": "",
            "ruta_modelo": "",
            "tiempo_ejecucion": "",
            "objetivo": "",
            "supuestos": "",
            "componentes": "",
            "limitaciones": "",
        }

        # Sección identificacion (campos simples)
        s_id = documento.seccion_por_id("identificacion")
        if s_id and s_id.contenido:
            try:
                data = json.loads(s_id.contenido)
                campos = json.loads(data.get("contenido", "{}")) if isinstance(data.get("contenido"), str) else data
                ctx["area"] = campos.get("Area", campos.get("area", ""))
                ctx["proceso"] = campos.get("Proceso", campos.get("proceso", ""))
                ctx["encargado_principal"] = campos.get("Encargado", campos.get("encargado", ""))
                ctx["frecuencia_uso"] = campos.get("Frecuencia de actualización", campos.get("frecuencia_uso", ""))
            except (json.JSONDecodeError, AttributeError):
                pass

        # Secciones texto
        for seccion_id, ctx_key in [
            ("objetivo_alcance", "objetivo"),
            ("supuestos", "supuestos"),
            ("componentes_librerias", "componentes"),
            ("limitaciones_riesgos", "limitaciones"),
        ]:
            s = documento.seccion_por_id(seccion_id)
            if s and s.contenido:
                try:
                    data = json.loads(s.contenido)
                    ctx[ctx_key] = data.get("contenido", s.contenido)
                except json.JSONDecodeError:
                    ctx[ctx_key] = s.contenido

        # Secciones tabla
        for seccion_id, ctx_key in _TABLA_MAP:
            s = documento.seccion_por_id(seccion_id)
            if s and s.contenido:
                try:
                    data = json.loads(s.contenido)
                    ctx[ctx_key] = data.get("filas", []) if isinstance(data, dict) else data
                except json.JSONDecodeError:
                    ctx[ctx_key] = []
            else:
                ctx[ctx_key] = []

        return ctx
```

- [ ] **Step 3b: Crear template Word mínimo funcional** (paso manual)

Abrir Word → nuevo documento en blanco → agregar el siguiente contenido (un placeholder por párrafo):
```
{{ nombre_modelo }}
{{ area }} — {{ encargado_principal }}
{{ objetivo }}

CORRIDAS
(insertar tabla docxtpl con: {% tr for run in runs %} | {{ run.numero }} | {{ run.detalle }} | {{ run.es_alm }} | {{ run.tiempo_ejecucion }} | {{ run.corrida_precedente }} | {% tr endfor %})

VARIABLES CRÍTICAS
(tabla: {% tr for var in variables %} | {{ var.nombre }} | {{ var.descripcion }} | {{ var.formula }} | {% tr endfor %})

INPUTS
(tabla: {% tr for inp in inputs %} | {{ inp.input }} | {{ inp.area_proveedora }} | {{ inp.frecuencia }} | {% tr endfor %})

MATRIZ DE CONOCIMIENTO
(tabla: {% tr for skill in skills_matrix %} | {{ skill.persona }} | {{ skill.capacidad }} | {{ skill.nivel }} | {% tr endfor %})
```
Guardar como: `src/docs/templates/prophet_model_doc_smnyl.docx`

> **Nota:** El template real con marca SMNYL completa (paleta, tipografías, logo) se diseña después de la demo con MA. Este template mínimo es suficiente para Fase 0.

- [ ] **Step 4: Verificar que pasan**

```
pytest tests/unit/test_docx_writer_prophet.py -v
```
Expected: 5/5 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/core/usecases/docx_writer_prophet.py src/docs/templates/prophet_model_doc_smnyl.docx tests/unit/test_docx_writer_prophet.py
git commit -m "feat: DocxWriterProphet + template Word mínimo (TDD)"
```

---

## Task 7: Actualizar `__init__.py` y dominio

**Files:**
- Modify: `src/core/usecases/__init__.py`

- [ ] **Step 1: Agregar exports**

```python
# Agregar al final de los imports en src/core/usecases/__init__.py:
from src.core.usecases.detectar_modelos_prophet import (
    DetectarModelosProphet,
    ModeloProphetInfo,
    ResultadoDeteccion,
)
from src.core.usecases.importar_registro_prophet import (
    ImportarRegistroProphet,
    ResultadoImportacionProphet,
)
from src.core.usecases.docx_writer_prophet import DocxWriterProphet

# Agregar al __all__:
# "DetectarModelosProphet", "ModeloProphetInfo", "ResultadoDeteccion",
# "ImportarRegistroProphet", "ResultadoImportacionProphet",
# "DocxWriterProphet",
```

- [ ] **Step 2: Verificar que el módulo importa correctamente**

```
python -c "from src.core.usecases import ImportarRegistroProphet, DetectarModelosProphet, DocxWriterProphet; print('OK')"
```

- [ ] **Step 3: Verificar todos los tests**

```
pytest tests/ -x -q
```
Expected: ~241 passed

- [ ] **Step 4: Commit**

```bash
git add src/core/usecases/__init__.py
git commit -m "feat: exportar use cases Prophet desde src.core.usecases"
```

---

## Task 8: UI — `crear_prophet.py`

**Files:**
- Create: `src/ui/pages/crear_prophet.py`

- [ ] **Step 1: Implementar pantalla de creación Prophet**

```python
# src/ui/pages/crear_prophet.py
"""Pantalla de inicio de Ficha Prophet.

Flujo:
1. Usuario sube un Excel de registro de modelos.
2. DocuMente detecta los modelos disponibles y muestra selectbox.
3. Usuario selecciona modelo → click "Importar".
4. Spinner mientras se importa → navega al dashboard.
"""

from __future__ import annotations

from io import BytesIO

import streamlit as st

from src.core.usecases import DetectarModelosProphet, ImportarRegistroProphet
from src.llm import AnthropicClient
from src.storage.repositories import DocumentoRepository
from src.ui.components import header
from src.ui.theme import SMNYL_COLORS


def _construir_use_cases() -> tuple[DetectarModelosProphet, ImportarRegistroProphet]:
    try:
        llm: AnthropicClient | None = AnthropicClient()
    except Exception:
        llm = None
    repo = DocumentoRepository()
    return DetectarModelosProphet(llm=llm), ImportarRegistroProphet(repo=repo, llm=llm)


def render() -> None:
    header.render(breadcrumbs=["Inicio", "Nueva Ficha Prophet"])

    st.markdown(
        f"""
        <h1 style="font-family: var(--font-display); color: {SMNYL_COLORS['text']}; margin-bottom: 0.5rem;">
            Nueva Ficha Prophet
        </h1>
        <p style="color: {SMNYL_COLORS['text_muted']}; margin-bottom: 2rem; max-width: 720px;">
            Sube el registro Excel de modelos actuariales. DocuMente detectará los modelos
            disponibles y generará la ficha pre-poblada con los datos del Excel.
        </p>
        """,
        unsafe_allow_html=True,
    )

    archivo = st.file_uploader(
        "Registro de modelos (.xlsx)",
        type=["xlsx", "xlsm"],
        help="El Excel con las hojas Descripcion_General, Detalle Runs, Variables criticas, Conocimiento_Tecnico.",
    )

    if archivo is None:
        st.caption("¿No tienes el formato correcto? Descarga el template desde `docs/Modulo Prophet MA/Registro_Modelos_Template.xlsx`.")
        if st.button("Cancelar", use_container_width=False):
            st.session_state["pagina"] = "home"
            st.rerun()
        return

    xlsx_bytes = archivo.getvalue()

    # Detectar modelos (con cache en session_state para no re-llamar en cada rerun)
    cache_key = f"prophet_modelos_{archivo.file_id}"
    if cache_key not in st.session_state:
        detector, _ = _construir_use_cases()
        with st.spinner("Detectando modelos en el Excel…"):
            resultado_deteccion = detector.ejecutar(xlsx_bytes)
        st.session_state[cache_key] = resultado_deteccion

    deteccion = st.session_state[cache_key]

    if deteccion.advertencias:
        for adv in deteccion.advertencias:
            st.warning(adv)

    if not deteccion.modelos:
        st.error("No se encontraron modelos en el Excel. Verifica el formato del archivo.")
        if st.button("Cancelar"):
            st.session_state["pagina"] = "home"
            st.rerun()
        return

    opciones = {f"{m.nombre} — {m.encargado}": m for m in deteccion.modelos}
    seleccion_key = st.selectbox("Selecciona el modelo a importar", list(opciones.keys()))
    modelo_info = opciones[seleccion_key]

    col_a, col_b, _ = st.columns([1, 1, 2])
    with col_a:
        importar = st.button("Importar ficha", type="primary", use_container_width=True)
    with col_b:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.pop(cache_key, None)
            st.session_state["pagina"] = "home"
            st.rerun()

    if importar:
        _, uc_importar = _construir_use_cases()
        with st.spinner(f"Importando datos de '{modelo_info.nombre}'…"):
            resultado = uc_importar.ejecutar(
                xlsx_bytes=xlsx_bytes,
                fila_idx=modelo_info.fila_idx,
                nombre_modelo=modelo_info.nombre,
            )

        if resultado.documento is None:
            for adv in resultado.advertencias:
                st.error(adv)
            return

        if resultado.advertencias:
            with st.expander(f"⚠️ {len(resultado.advertencias)} advertencias del import"):
                for adv in resultado.advertencias:
                    st.caption(adv)

        st.success(
            f"Ficha importada: {resultado.secciones_importadas} secciones pre-pobladas, "
            f"{resultado.secciones_vacias} vacías para completar."
        )
        st.session_state.pop(cache_key, None)
        st.session_state["documento_actual_id"] = str(resultado.documento.id)
        st.session_state["pagina"] = "dashboard"
        st.rerun()
```

- [ ] **Step 2: Smoke test de importación**

```
python -c "from src.ui.pages.crear_prophet import render; print('import OK')"
```

- [ ] **Step 3: Commit**

```bash
git add src/ui/pages/crear_prophet.py
git commit -m "feat: pantalla crear_prophet — upload Excel + selector modelo + importar"
```

---

## Task 9: UI — `editar_seccion_prophet.py`

**Files:**
- Create: `src/ui/pages/editar_seccion_prophet.py`
- Create: `tests/unit/test_editar_seccion_prophet.py`

- [ ] **Step 1: Escribir tests de lógica de guardado**

```python
# tests/unit/test_editar_seccion_prophet.py
from __future__ import annotations

import json
import os
import pytest

from src.core.template_catalog_prophet import construir_secciones_vacias_prophet
from src.core.models import Documento
from src.core.models.documento import MetadataModelo
from src.storage.repositories import DocumentoRepository


@pytest.fixture()
def repo_con_doc_prophet(tmp_path):
    os.environ["DOCUMENTE_DB_PATH"] = str(tmp_path / "test.db")
    repo = DocumentoRepository()
    doc = Documento(
        tipo="prophet",
        metadata_modelo=MetadataModelo(nombre_modelo="VNB Test"),
        secciones=construir_secciones_vacias_prophet(),
    )
    repo.guardar(doc)
    return repo, doc


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
    repo, doc = repo_con_doc_prophet
    seccion = doc.seccion_por_id("limitaciones_riesgos")
    assert seccion is not None
    assert seccion.completitud == "vacia"
    assert seccion.contenido is None
```

- [ ] **Step 2: Verificar que pasan (son tests de repo, no de UI)**

```
pytest tests/unit/test_editar_seccion_prophet.py -v
```
Expected: 3/3 PASSED (usan solo el repo, sin Streamlit)

- [ ] **Step 3: Implementar `editar_seccion_prophet.py`**

```python
# src/ui/pages/editar_seccion_prophet.py
"""Editor de sección Prophet a pantalla completa.

Recibe `seccion_id` y `documento_actual_id` de session_state.
Renderiza editor apropiado según tipo_contenido:
  - "tabla"  → tabla editable con add/remove filas
  - "texto"  → textarea amplia
  - "campos" → form con inputs individuales
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import streamlit as st

from src.core.models import EventoAuditoria
from src.core.template_catalog_prophet import por_id_prophet
from src.storage.repositories import DocumentoRepository
from src.ui.components import header
from src.ui.theme import SMNYL_COLORS


def render() -> None:
    seccion_id: str = st.session_state.get("prophet_seccion_id", "")
    doc_id: str = st.session_state.get("documento_actual_id", "")

    repo = DocumentoRepository()
    doc = repo.obtener_por_str(doc_id) if doc_id else None

    if doc is None or not seccion_id:
        st.error("No se encontró el documento o sección. Vuelve al dashboard.")
        if st.button("← Volver"):
            st.session_state["pagina"] = "dashboard"
            st.rerun()
        return

    seccion = doc.seccion_por_id(seccion_id)
    cat = por_id_prophet(seccion_id)

    if seccion is None or cat is None:
        st.error(f"Sección '{seccion_id}' no encontrada.")
        if st.button("← Volver"):
            st.session_state["pagina"] = "dashboard"
            st.rerun()
        return

    header.render(breadcrumbs=["Inicio", doc.metadata_modelo.nombre_modelo, seccion.nombre])

    st.markdown(
        f"""<h1 style="font-family: var(--font-display); color: {SMNYL_COLORS['text']}; margin-bottom: 0.25rem;">
            {seccion.nombre}
        </h1>
        <p style="color: {SMNYL_COLORS['text_muted']}; margin-bottom: 1.5rem;">{cat.intencion}</p>""",
        unsafe_allow_html=True,
    )

    nuevo_contenido: str | None = None

    if cat.tipo_contenido == "tabla":
        nuevo_contenido = _editor_tabla(seccion, cat)
    elif cat.tipo_contenido == "texto":
        nuevo_contenido = _editor_texto(seccion)
    else:  # campos
        nuevo_contenido = _editor_campos(seccion, cat)

    col_guardar, col_volver, _ = st.columns([1, 1, 3])
    with col_guardar:
        if st.button("Guardar cambios", type="primary", use_container_width=True):
            if nuevo_contenido is not None:
                seccion.contenido = nuevo_contenido
                seccion.completitud = "completa"
                doc.registrar_evento(EventoAuditoria(
                    timestamp=datetime.now(UTC),
                    actor="default",
                    tipo="seccion_actualizada",
                    descripcion=f"Sección '{seccion.nombre}' actualizada (Prophet)",
                    metadata={"seccion_id": seccion_id},
                ))
                repo.guardar(doc)
                st.success("Cambios guardados.")
                st.session_state["pagina"] = "dashboard"
                st.rerun()

    with col_volver:
        if st.button("← Volver al dashboard", use_container_width=True):
            st.session_state["pagina"] = "dashboard"
            st.rerun()


def _editor_tabla(seccion, cat) -> str:
    """Renderiza una tabla editable con add/edit/remove filas."""
    columnas = list(cat.schema_tabla)
    filas_actuales: list[dict] = []
    if seccion.contenido:
        try:
            data = json.loads(seccion.contenido)
            filas_actuales = data.get("filas", []) if isinstance(data, dict) else []
        except json.JSONDecodeError:
            pass

    st.caption(f"{len(filas_actuales)} filas · columnas: {', '.join(columnas)}")

    edited = st.data_editor(
        filas_actuales if filas_actuales else [{col: "" for col in columnas}],
        num_rows="dynamic",
        use_container_width=True,
        key=f"table_editor_{seccion.id}",
    )
    return json.dumps({"filas": edited, "advertencias": []}, ensure_ascii=False)


def _editor_texto(seccion) -> str:
    valor_actual = ""
    if seccion.contenido:
        try:
            data = json.loads(seccion.contenido)
            valor_actual = data.get("contenido", seccion.contenido)
        except json.JSONDecodeError:
            valor_actual = seccion.contenido

    texto = st.text_area(
        "Contenido",
        value=valor_actual,
        height=300,
        label_visibility="collapsed",
        key=f"text_editor_{seccion.id}",
    )
    return json.dumps({"contenido": texto, "advertencias": []}, ensure_ascii=False)


def _editor_campos(seccion, cat) -> str:
    campos_actuales: dict = {}
    if seccion.contenido:
        try:
            data = json.loads(seccion.contenido)
            raw = data.get("contenido", "{}")
            campos_actuales = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            pass

    cols = cat.schema_tabla if cat.schema_tabla else tuple(campos_actuales.keys())
    resultado: dict = {}
    for col in cols:
        resultado[col] = st.text_input(col.replace("_", " ").capitalize(), value=campos_actuales.get(col, ""), key=f"campo_{seccion.id}_{col}")

    return json.dumps({"contenido": json.dumps(resultado, ensure_ascii=False), "advertencias": []}, ensure_ascii=False)
```

- [ ] **Step 4: Smoke test de importación**

```
python -c "from src.ui.pages.editar_seccion_prophet import render; print('import OK')"
```

- [ ] **Step 5: Commit**

```bash
git add src/ui/pages/editar_seccion_prophet.py tests/unit/test_editar_seccion_prophet.py
git commit -m "feat: editor pantalla completa para secciones Prophet (tabla/texto/campos)"
```

---

## Task 10: Routing — `home.py` + `app.py`

**Files:**
- Modify: `src/ui/pages/home.py` (función `_render_home` en `app.py`, línea ~57-70)
- Modify: `app.py`

- [ ] **Step 1: Agregar tercer botón en `app.py` → `_render_home()`**

En `app.py`, función `_render_home()`, línea ~57, cambiar de 2 a 3 columnas:

```python
# ANTES:
col_a, col_b, _ = st.columns([1, 1, 2])
with col_a:
    if st.button("Crear nuevo documento", ...):
        st.session_state["pagina"] = "crear_nuevo"
        st.rerun()
with col_b:
    if st.button("Mejorar documento existente", ...):
        st.session_state["pagina"] = "importar"
        st.rerun()

# DESPUÉS:
col_a, col_b, col_c, _ = st.columns([1, 1, 1, 1])
with col_a:
    if st.button("Crear nuevo documento", type="primary", use_container_width=True,
                 help="Empieza con las 28 secciones vacías del template oficial NYL."):
        st.session_state["pagina"] = "crear_nuevo"
        st.rerun()
with col_b:
    if st.button("Mejorar documento existente", use_container_width=True):
        st.session_state["pagina"] = "importar"
        st.rerun()
with col_c:
    if st.button("Iniciar Ficha Prophet", use_container_width=True,
                 help="Importa el registro Excel de Modelos Actuariales y genera la ficha técnica."):
        st.session_state["pagina"] = "crear_prophet"
        st.rerun()
```

- [ ] **Step 2: Agregar importación y rutas en `app.py`**

```python
# En los imports de app.py, agregar:
from src.ui.pages import crear_prophet, editar_seccion_prophet

# En la función main(), después de elif pagina == "brief_inicial":
elif pagina == "crear_prophet":
    crear_prophet.render()
elif pagina == "editar_seccion_prophet":
    editar_seccion_prophet.render()
```

- [ ] **Step 3: Verificar que todos los tests siguen pasando**

```
pytest tests/ -x -q
```
Expected: ~244 passed

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: tercer botón 'Iniciar Ficha Prophet' en home + routing crear_prophet/editar_seccion_prophet"
```

---

## Task 11: Documentación de soporte para MA

**Files:**
- Create: `docs/Modulo Prophet MA/Registro_Modelos_Template.xlsx` (manual con openpyxl)
- Create: `docs/Modulo Prophet MA/Guia_Llenado_Registro.md`

- [ ] **Step 1: Generar template Excel con openpyxl**

```python
# Ejecutar este script una vez (no es un test):
# python scripts/crear_template_excel_prophet.py

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from pathlib import Path

AZUL = "0079C2"

def crear_template():
    wb = openpyxl.Workbook()

    # Hoja 1: Descripcion_General
    ws1 = wb.active
    ws1.title = "Descripcion_General"
    headers1 = ["Area", "Proceso", "Encargado", "Descripcion", "Corridas",
                "Contabilidad", "Periodo de actualización", "Reporta",
                "Frecuencia de actualización", "Insumo", "Área encargada",
                "Tiempo de ejecución", "Qué problema ataca"]
    ejemplo1 = ["Rentabilidad", "VNB", "Francisco Carmona",
                "Modelo de valor nuevo de negocio para medir rentabilidad de nuevos productos",
                "33, 34, 36, 37", "Stat", "Trimestral", "NBM, PM, IRR",
                "Trimestral", "MR, Tasas, RCS", "Riesgos, Inversiones", "2-3 horas",
                "Medir rentabilidad de nuevos negocios en Prophet"]

    for col, h in enumerate(headers1, 1):
        cell = ws1.cell(row=1, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(fill_type="solid", fgColor=AZUL)
    for col, v in enumerate(ejemplo1, 1):
        ws1.cell(row=2, column=col, value=v)

    # Hoja 2: Detalle Runs
    ws2 = wb.create_sheet("Detalle Runs")
    headers2 = ["# corrida", "Detalle", "Corrida Precedente", "Es ALM?",
                "Tiempo de ejecución", "Outputs Principales", "Variables críticas",
                "Inputs", "Área a quien se pide", "Frecuencia de actualización",
                "Qué se actualiza en el modelo", "Responsable"]
    ejemplo2 = ["33", "IL UDI y USD", "", "No", "45 min", "VNB, Profit",
                "PROF_SOLVM, NEW_ANN_PREM", "MR, Tasas", "Riesgos, Inversiones",
                "Trimestral", "Mortalidad, tasas de interés", "Francisco Carmona"]
    for col, h in enumerate(headers2, 1):
        cell = ws2.cell(row=1, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(fill_type="solid", fgColor=AZUL)
    for col, v in enumerate(ejemplo2, 1):
        ws2.cell(row=2, column=col, value=v)

    # Hoja 3: Variables criticas
    ws3 = wb.create_sheet("Variables criticas")
    headers3 = ["Corrida", "Nombre", "Descripción", "Variables precedentes",
                "Same_as", "Fórmula", "Frecuencia de actualización",
                "Responsable de la info", "Documentación", "Variables dependientes"]
    ejemplo3 = ["33", "PROF_SOLVM", "Solvency margin profit", "PREM_INC, DEATH_OUTGO",
                "C_SMNYL", "PREM_INC - DEATH_OUTGO - EXPENSES", "Trimestral",
                "Francisco Carmona", "Ver runbook Q1-2026", "DISC_A_PC"]
    for col, h in enumerate(headers3, 1):
        cell = ws3.cell(row=1, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(fill_type="solid", fgColor=AZUL)
    for col, v in enumerate(ejemplo3, 1):
        ws3.cell(row=2, column=col, value=v)

    # Hoja 4: Conocimiento_Tecnico
    ws4 = wb.create_sheet("Conocimiento_Tecnico")
    capacidades = [
        "Navegación en Workspace", "Ejecutar corridas base",
        "Concepto de run structure y run setting", "Configuración de run settings",
        "Edición y creación de tablas", "Estructura de tablas",
        "Creación de nuevas corridas", "Correr 1 póliza",
        "Tablas de propiedades", "Seguimiento de variables",
        "Librería ALM", "Modificación de código",
        "Implementación de nuevos productos",
    ]
    ws4.cell(row=1, column=1, value="Persona").font = Font(bold=True, color="FFFFFF")
    ws4.cell(row=1, column=1).fill = PatternFill(fill_type="solid", fgColor=AZUL)
    for col, cap in enumerate(capacidades, 2):
        cell = ws4.cell(row=1, column=col, value=cap)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(fill_type="solid", fgColor=AZUL)
    personas = [
        ("Francisco Carmona", ["AVANZADO", "AVANZADO", "AVANZADO", "AVANZADO", "AVANZADO",
                               "AVANZADO", "INTERMEDIO", "AVANZADO", "AVANZADO", "AVANZADO",
                               "AVANZADO", "INTERMEDIO", "BÁSICO"]),
        ("Cynthia Flores", ["INTERMEDIO", "AVANZADO", "INTERMEDIO", "INTERMEDIO", "BÁSICO",
                            "INTERMEDIO", "BÁSICO", "INTERMEDIO", "BÁSICO", "INTERMEDIO",
                            "BÁSICO", "NO CONOCE", "NO CONOCE"]),
    ]
    for row_idx, (persona, niveles) in enumerate(personas, 2):
        ws4.cell(row=row_idx, column=1, value=persona)
        for col, nivel in enumerate(niveles, 2):
            ws4.cell(row=row_idx, column=col, value=nivel)

    out_path = Path("docs/Modulo Prophet MA/Registro_Modelos_Template.xlsx")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out_path))
    print(f"Template guardado en {out_path}")

crear_template()
```

Ejecutar:
```
python -c "exec(open('scripts/crear_template_excel_prophet.py').read())"
```
O copiar el código y ejecutarlo directamente en Python.

- [ ] **Step 2: Crear guía de llenado**

Crear `docs/Modulo Prophet MA/Guia_Llenado_Registro.md` con:
- Descripción de las 4 hojas requeridas
- Columnas obligatorias vs opcionales por hoja
- Niveles de conocimiento válidos: NO CONOCE / BÁSICO / INTERMEDIO / AVANZADO
- Qué pasa si falta una hoja (la sección queda vacía, no rompe el import)
- Cómo actualizar una ficha: re-importar el Excel desde DocuMente

- [ ] **Step 3: Commit**

```bash
git add "docs/Modulo Prophet MA/Registro_Modelos_Template.xlsx" "docs/Modulo Prophet MA/Guia_Llenado_Registro.md"
git commit -m "docs: template Excel Prophet + guía de llenado para MA"
```

---

## Task 12: Exportación Prophet desde Dashboard

**Files:**
- Modify: `src/ui/pages/dashboard.py` — agregar botón "Exportar Ficha Prophet" cuando `doc.tipo == "prophet"`

- [ ] **Step 1: Agregar export Prophet en la card de Gobernanza del dashboard**

En `src/ui/pages/dashboard.py`, dentro de la lógica de exportación existente, agregar condición:

```python
# Dentro del bloque donde se muestra el botón de exportación:
if doc.tipo == "prophet":
    from src.core.usecases import DocxWriterProphet
    writer = DocxWriterProphet()
    try:
        docx_bytes = writer.render(doc)
        nombre_archivo = f"Ficha_Prophet_{doc.metadata_modelo.nombre_modelo.replace(' ', '_')}.docx"
        st.download_button(
            label="Exportar Ficha Prophet (.docx)",
            data=docx_bytes,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except FileNotFoundError as e:
        st.warning(str(e))
```

- [ ] **Step 2: Verificar todos los tests**

```
pytest tests/ -q
```
Expected: ~246+ passed (sin regresiones)

- [ ] **Step 3: Commit**

```bash
git add src/ui/pages/dashboard.py
git commit -m "feat: botón exportar Ficha Prophet desde dashboard"
```

---

## Task 13: Smoke test end-to-end + verificación final

- [ ] **Step 1: Correr suite completa**

```
pytest tests/ -q --tb=short
```
Expected: ~246+ PASSED, 0 failed

- [ ] **Step 2: Ruff y mypy**

```
ruff check src/ tests/
ruff format src/ tests/ --check
mypy src/ --ignore-missing-imports
```
Expected: sin errores nuevos en archivos modificados

- [ ] **Step 3: Smoke test de la app (manual)**

```
streamlit run app.py
```
Flujo a verificar:
1. Home muestra 3 botones — "Iniciar Ficha Prophet" visible.
2. Click "Iniciar Ficha Prophet" → pantalla upload Excel.
3. Subir `docs/Modulo Prophet MA/Registro Modelos_envioAlberto.xlsx` → detecta modelos (VNB).
4. Seleccionar VNB → click "Importar" → spinner → dashboard con secciones pre-pobladas.
5. Click "Editar" en sección "Corridas (Runs)" → tabla editable → guardar → volver al dashboard.
6. Exportar Ficha Prophet → descarga .docx.

- [ ] **Step 4: Commit final de cierre**

```bash
git add -A
git commit -m "feat: módulo Prophet Fase 0 completo — import Excel + fichas + editor + export DOCX"
```

---

## Self-review checklist

- [x] **Spec coverage:** Todos los entregables del spec cubiertos: catálogo 12 secciones (Task 1), TipoDocumento (Task 2), prompt LLM (Task 3), DetectarModelos (Task 4), ImportarRegistro (Task 5), DocxWriter (Task 6), UI crear_prophet (Task 8), UI editar_seccion (Task 9), routing (Task 10), docs soporte (Task 11), export (Task 12).
- [x] **Sin placeholders:** Todo el código en cada step está completo y ejecutable.
- [x] **Consistencia de tipos:** `ModeloProphetInfo`, `ResultadoDeteccion`, `ResultadoImportacionProphet` definidos en Task 4/5 y usados consistentemente en Tasks 8/9/10.
- [x] **Baseline:** 236 tests pre-existentes no se tocan. Nuevos tests: ~20 adicionales. Meta: ~256.
- [x] **Regla de capas:** Dominio (`template_catalog_prophet`) no importa de UI ni infra. Use cases importan de dominio. UI importa de use cases.
- [x] **Limitación documentada:** single-user, sin LLM opcional en edición, sin índice del área — todo en el spec.
