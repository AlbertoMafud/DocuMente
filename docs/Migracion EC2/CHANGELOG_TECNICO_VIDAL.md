# Changelog técnico para Vidal — Plan de remediación S13→S16

> Documento vivo. Se actualiza al cierre de cada fase del plan de remediación. Audiencia: arquitecto de datos (Vidal). Idioma: español. **Si llegas a este documento por primera vez, lee la sección 1 (Resumen ejecutivo) y la sección 5 (Cómo se llama al LLM) — son las dos prioritarias para tu deploy en EC2.**

**Rama de trabajo:** `feat/remediacion-s13-s16` (creada desde `main@51d845e`). Las sub-ramas por fase se mergean a esta antes de subir a `main`.

**Última actualización:** 2026-05-19 — S13 día 1: foundation + A.1.b password-gate implementado.

---

## 1. Resumen ejecutivo

_Pendiente — se completará al cerrar Fase A._

**Qué cambia entre `main` y `feat/remediacion-s13-s16`:** el plan agrega 14 mejoras agrupadas en 4 fases (seguridad multi-tenant, contenido inteligente, apéndices avanzados + versionado, Prophet + auditoría frontend). El objetivo es llevar DocuMente de "MVP listo para piloto interno" a "producto pilotable con SLA".

**Lo que NO cambia:**
- Stack técnico: sigue Python 3.11 + Streamlit + SQLite (local) + Anthropic SDK.
- Estructura por capas (UI → Application → Domain → Infrastructure).
- Plantilla maestra MRM `model_development_smnyl.docx` (no se rediseña en este plan).
- Decisión Bedrock vs Anthropic directo — sigue pendiente de Compliance; el plan agrega capacidad de swap pero no fuerza el cambio.

---

## 2. Decisiones que afectan deploy

| Decisión | Impacto para Vidal |
|---|---|
| **Auth mechanism (Fase A.1)** | Necesito que confirmes si ALB hace OIDC con Cognito y forwardea `X-Amzn-Oidc-Identity` / `X-Amzn-Oidc-Data`, o si Cognito-Hosted-UI redirige y la app debe leer JWT/cookie. La rama 1 (header) es más simple; la rama 2 (JWT) requiere `python-jose` o equivalente. **Mientras tanto: password-gate temporal con env var `DOCUMENTE_GATE_PASSWORD`** |
| **LLM provider (sigue pendiente Compliance)** | El plan introduce un `LLMClient` factory que decide entre `AnthropicClient` (actual) o `BedrockClient` (nuevo) según env var `LLM_PROVIDER`. Sin cambios si se queda en Anthropic directo. Ver §5 |
| **Nuevas dependencias del SO (Fase C.1)** | Apéndices PDF requieren `poppler` (vía `pdf2image`) o `PyMuPDF`. Decisión técnica pendiente al implementar — prefiero PyMuPDF para evitar dep del SO en la AMI |
| **Schema migrations aditivas** | 3 migraciones nuevas: campos `archivado` (Fase A.5), tabla `versiones` (Fase C.2), campo `formulas_inline` (Fase C.1). Todas aditivas, idempotentes, validadas al boot |
| **Roles admin (Fase A.1.d)** | Para eliminación permanente de docs (papelera) necesito saber qué grupos Cognito vas a crear. Default propuesto: grupo `documente-admin` |

---

## 3. Nuevas dependencias

| Paquete | Versión mínima | Propósito | Impacto SO | Fase |
|---|---|---|---|---|
| `anthropic` | **>=0.50.0** (reforzado) | Soportar `thinking` y futuros features | Ninguno | Pre-existente, fix de S12 |
| `pdf2image` (alt) | >=1.16 | Render páginas PDF a PNG para apéndices | Requiere `poppler-utils` en SO | C.1 |
| `PyMuPDF` (recomendado) | >=1.23 | Mismo propósito, **sin dep del SO** | Ninguno | C.1 (alternativa) |
| `pylatexenc` | >=2.10 | Convertir LaTeX → MathML → OMML | Ninguno | C.1 |
| `Pillow` | >=10 | Manipulación de imágenes (fallback PNG) | Ninguno | C.1 |

_Notas de instalación SO_:
- Si elegimos `pdf2image`: en EC2 Ubuntu/Debian → `apt install poppler-utils`. Agregar al Dockerfile cuando llegue M1.
- Si elegimos `PyMuPDF`: cero dependencias extra. **Mi recomendación.**

---

## 4. Variables de entorno nuevas

| Variable | Default | Propósito | Cuándo se introduce |
|---|---|---|---|
| `DOCUMENTE_GATE_PASSWORD` | _(no default — bloquea si vacío)_ | Password temporal mientras se resuelve auth real. **Eliminar en cuanto Cognito esté integrado** | A.1.b |
| `COGNITO_USER_POOL_ID` | _(opcional)_ | ID del User Pool de Cognito para validar JWTs si se usa rama 2 | A.1.c (rama 2) |
| `DOCUMENTE_ADMIN_USERS` | _(vacío)_ | Lista CSV de `user_id` con rol admin (eliminación permanente, papelera global). Reemplazado por grupos Cognito tras A.1.d | A.5 |
| `LLM_PROVIDER` | `anthropic` | Selector del provider: `anthropic` (directo) o `bedrock` | Si se activa Bedrock |
| `AWS_BEDROCK_REGION` | `us-east-1` | Región Bedrock si `LLM_PROVIDER=bedrock` | Si se activa Bedrock |

---

## 5. Cómo se llama al LLM (sección crítica para Vidal)

### Estado actual (`main@8d64520`)

```
src/llm/client.py:LLMClient (abstract)
    └─> src/llm/anthropic_client.py:AnthropicClient  ← única implementación
            └─> anthropic.Anthropic(api_key=ANTHROPIC_API_KEY).messages.create(...)
```

`LLMClient` ya es interfaz abstracta. `AnthropicClient` lee `ANTHROPIC_API_KEY` del `.env` y llama el SDK oficial. Modelos usados:
- `claude-opus-4-7` o `claude-sonnet-4-6` para drafting/interview.
- `claude-haiku-4-5-20251001` para extracción tabular, traducción ES/EN, detección de idioma.

### Estado futuro (post Fase A si se activa Bedrock)

```
src/llm/client.py:LLMClient (abstract)
    ├─> src/llm/anthropic_client.py:AnthropicClient
    └─> src/llm/bedrock_client.py:BedrockClient  ← NUEVO (a crear si Compliance decide Bedrock)
```

Factory en `src/llm/factory.py`:
```python
def crear_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    if provider == "bedrock":
        return BedrockClient(region=os.getenv("AWS_BEDRECK_REGION", "us-east-1"))
    return AnthropicClient(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### Archivos a tocar si Vidal decide Bedrock

| Archivo | Cambio |
|---|---|
| `src/llm/bedrock_client.py` (nuevo) | Implementar `LLMClient` usando `boto3.client("bedrock-runtime").invoke_model(...)`. Mapear los model IDs: `claude-opus-4-7` → `anthropic.claude-opus-4-7-v1:0` (o el ARN equivalente Bedrock) |
| `src/llm/factory.py` (nuevo) | Factory de arriba |
| `src/core/usecases/*.py` que instancian `AnthropicClient()` directamente | Reemplazar por `crear_llm_client()` |
| `pyproject.toml` | Agregar `boto3>=1.34` (opcional, ya viene con AWS CLI) |
| `app.py` | No cambia — la factory es transparente |

**Notas Bedrock:**
- IAM role en EC2 con policy `bedrock:InvokeModel` sobre los model ARNs deseados.
- Sin API key — auth automática vía role.
- Latencia esperada similar (~2-5s por sección).
- **No requiere cambios a la lógica de negocio** ni a los prompts existentes.

---

## 6. Schema de BD: migraciones aditivas aplicadas

_Pendiente — se completará al cerrar cada fase._

Cada migración se aplica al boot de `app.py` con `ALTER TABLE IF NOT EXISTS` (idempotente). El archivo `src/storage/db.py` contendrá una función `aplicar_migraciones_aditivas(conn)` que se llama una sola vez.

### Migraciones planeadas

| Fase | Migración | Archivo |
|---|---|---|
| A.5 | Agregar columnas `archivado BOOLEAN DEFAULT FALSE`, `archivado_en TIMESTAMP NULL` en `documentos` | `src/storage/db.py` |
| C.1 | Agregar columna `formulas_inline JSON DEFAULT '[]'` en `secciones` | `src/storage/db.py` |
| C.2 | Crear tabla `versiones` (id, documento_id FK, numero INT, snapshot JSON, comentario TEXT, hash_contenido TEXT, creado_en TIMESTAMP) | `src/storage/db.py` |

---

## 7. Estructura de carpetas: qué se agregó

_Pendiente — se completará al cerrar cada fase. Solo se listan diffs._

---

## 8. Archivos modificados sensibles para deploy

_Pendiente — se completará al cerrar cada fase._

Foco actual:
- `app.py` (auth gate + routing nuevo)
- `pyproject.toml` (lower bounds + deps nuevas)
- `src/storage/db.py` (migraciones aditivas)
- `src/llm/client.py` + factory (si se activa Bedrock)

---

## 9. Checklist de deploy actualizado

_Pendiente — espejo del §8 de `MIGRATION_TO_EC2.md` con cambios post-S13._

---

## 10. Riesgos y mitigaciones para Vidal

| Riesgo | Mitigación |
|---|---|
| Si elegimos `pdf2image`, AMI estándar no trae `poppler-utils` | Migrar a `PyMuPDF` (recomendado). Decisión al implementar C.1 |
| Migraciones aditivas se aplican en orden no determinístico si hay race | Lock al boot — solo el primer worker aplica; los demás esperan |
| `LLM_PROVIDER=bedrock` sin IAM role configurado → 403 al primer llamado | Validación al boot: ping a Bedrock con `ListFoundationModels`. Si falla → app bootea con warning prominente |
| Cognito decide rama 2 (JWT) → necesitamos `python-jose` o equivalente | Acordado al implementar A.1.c; agrego al `pyproject.toml` solo si esa rama se confirma |

---

## 11. Q&A esperado

_Pendiente — se anticipa al cerrar Fase A._

Preguntas tentativas que Vidal va a hacer:
1. ¿Pierdo data si no aplico las migraciones aditivas? — _No, son backward-compatible. La app sigue funcionando con schema viejo siempre que no uses features nuevos._
2. ¿Tengo que rebootear EC2 al hacer pull? — _Solo si tocas `pyproject.toml`; las migraciones aditivas se aplican en cada arranque._
3. ¿Cómo desactivo features nuevos si me dan problema? — _Cada feature opt-in tiene su env var (`DOCUMENTE_POLISH_ENABLED`, etc.) — set a `false` para desactivar._
4. ¿Qué pasa si pongo `LLM_PROVIDER=bedrock` sin tener Bedrock configurado? — _App bootea con warning, los flujos LLM degradan elegantemente (no crashea)._
5. ¿Cómo verifico que el password-gate está en producción y no en dev? — _Si `DOCUMENTE_GATE_PASSWORD` está set, el gate está activo; el banner del header muestra "Modo password-gate" para que sea obvio._

---

## Historial de updates de este documento

| Fecha | Fase cerrada | Resumen |
|---|---|---|
| 2026-05-19 | Sprint S13 — Fase A casi completa (4 de 5 sub-tareas) | A.1.b password-gate, A.2 onboarding-fix, A.3 idioma-normaliza, A.4 PDF-ancla, A.5 archivado-papelera-purga. A.1.c (Cognito multi-tenant real) bloqueado pendiente reunión Vidal. 307 tests passing (de 263 baseline → +44). |

---

## Anexo S13 — Resumen de cambios para deploy

### Nuevas variables de entorno

- **`DOCUMENTE_GATE_PASSWORD`** *(opcional, recomendado activo en EC2 mientras se integra Cognito)*: si está set y no vacío, la app pide ese password antes de cualquier ruta. Si está unset o vacío, el gate se desactiva (modo dev local). Ver `src/ui/components/auth_gate.py`.

### Nuevas dependencias

Ninguna en S13. Las dependencias planeadas (pdf2image / pylatexenc / PyMuPDF) van en Fase C.1. La única dep usada por A.4 PDF-ancla es `pypdf` (ya estaba en `pyproject.toml`).

### Schema: migraciones aditivas aplicadas (Fase A.5)

`src/storage/db.py` ahora ejecuta migraciones idempotentes al boot vía `_aplicar_migraciones_aditivas(engine)`. Agrega 3 columnas a la tabla `documentos`:

| Columna | Tipo | Default | Propósito |
|---|---|---|---|
| `archivado` | `BOOLEAN NOT NULL` | `FALSE` | Doc oculto del home pero recuperable |
| `en_papelera` | `BOOLEAN NOT NULL` | `FALSE` | Doc en papelera, purga automática a 30 días |
| `archivado_en` | `DATETIME` (nullable) | `NULL` | Timestamp del último cambio de visibilidad |

**Para Vidal:** las BD viejas (preS13) en EC2 reciben estas columnas automáticamente al primer arranque post-pull. Ningún restart manual ni migration script — el engine init las aplica si faltan. No afecta datos existentes.

### Nuevos use cases y archivos

| Archivo | Propósito |
|---|---|
| `src/ui/components/auth_gate.py` | Password-gate temporal (A.1.b) |
| `src/ui/components/onboarding_banner.py` | Banner de prellenado tras onboarding (A.2) |
| `src/core/usecases/sugerencias_multifuente.py` | Refactorizado con `ResultadoSugerencias` (A.2) |
| `src/core/usecases/aplicar_brief.py` | Refactorizado con `ResultadoBrief` (A.2) |
| `src/core/usecases/crear_documento.py` | Refactorizado con `ResultadoCrearDocumento` (A.2) |
| `src/core/usecases/importar_documento.py` | Refactorizado con advertencias propagadas (A.2) |
| `src/llm/prompts/traduccion.py` | Prompts ES/EN + detector de idioma (A.3) |
| `src/core/usecases/traductor.py` | 5 modos: es/en (legacy) + es_normalize/en_normalize/bilingue (A.3) |
| `src/docs/readers/anchor_reader.py` | Factory que despacha .docx vs .pdf (A.4) |
| `src/docs/readers/pdf_anchor_reader.py` | Lector de PDF con heurística de headings (A.4) |
| `src/core/usecases/archivar_documento.py` | Use case archivar/papelera/eliminar + `purgar_papelera_expirada` (A.5) |

### Comportamiento que cambió de defaults previos

| Antes (`main@8d64520`) | Ahora (`feat/remediacion-s13-s16`) |
|---|---|
| `SugerenciasMultiFuente.ejecutar()` retornaba `int` | Retorna `ResultadoSugerencias` dataclass con errores |
| `AplicarBrief.ejecutar()` retornaba `int` | Retorna `ResultadoBrief` dataclass con errores |
| `CrearDocumentoEnBlanco.ejecutar()` retornaba `Documento` | Retorna `ResultadoCrearDocumento` (con `.documento`) |
| `ImportarDocumento.ejecutar()` retornaba `ResultadoImportacion` | Sigue retornando el mismo dataclass, pero con campos nuevos (advertencias, sugerencias detalle) |
| Errores LLM se suprimían silenciosamente | Errores se loguean (`logger.warning`) y propagan al resultado |
| `Idioma = Literal["es", "en"]` | `Idioma = Literal["es", "en", "es_normalize", "en_normalize", "bilingue"]` (legacy preservado) |
| `home` mostraba 5 recientes en lista plana | `home` tiene 3 tabs: Activos / Archivados / Papelera |
| `importar.py` solo aceptaba `.docx` | Acepta `.docx` o `.pdf` (con AnchorReader factory) |

### Tests / lint

- pytest: **307/307 passing** (de 263 baseline, +44 nuevos).
- ruff check: clean en `src/`, `tests/`, `app.py`.
- ruff format: clean.

### Lo que sigue para Vidal

1. **Set `DOCUMENTE_GATE_PASSWORD`** en EC2 como mitigación de emergencia mientras se resuelve A.1.c.
2. **Reunión 30 min** para confirmar mecánica de Cognito (ALB header vs JWT decode). El plan describe ambas ramas; necesitamos tu input antes de implementar A.1.c.
3. **No requiere migration script** — las migraciones aditivas se aplican al boot.
