# Plan de migración DocuMente → AWS EC2

> **Documento vivo.** Se actualiza con cada feature que se desarrolle en el MVP. Cada vez que una nueva pieza de funcionalidad entre, se agrega o actualiza una fila en la tabla de la sección §3. Cuando llegue el momento de migrar, este plan se ejecuta — no se descubre.

---

## 0. Premisa

DocuMente se desarrolla 100% local en la máquina de Alberto durante el MVP, con Streamlit + SQLite + filesystem local + Anthropic API. **No instalamos Docker ni tocamos AWS hoy.**

Sin embargo, cada decisión técnica se evalúa contra esta pregunta: *"¿Esto bloquea o complica la migración futura a EC2 multi-usuario?"*

Si la respuesta es sí, se replantea. Si la respuesta es no, avanzamos.

---

## 1. Principios arquitectónicos del MVP que evitan dolor en la migración

Los siguientes seis principios se aplican desde la primera línea de código:

1. **Doce factores** ([12factor.net](https://12factor.net)): config en variables de entorno, logs estructurados a stdout, dependencias explícitas en `pyproject.toml`. No agrega complejidad — es la forma correcta.
2. **Persistencia abstraída**: la lógica de negocio nunca toca SQLite directamente. Siempre vía un `Repository`. Migrar a PostgreSQL = cambiar el adaptador, no la app.
3. **Almacenamiento de archivos abstraído**: los `.docx` se acceden vía interfaz `Storage`, nunca por path local en código de negocio. Migrar a S3 = cambiar el adaptador.
4. **LLM Client como interfaz**: hoy es `AnthropicClient`, mañana puede ser `BedrockClient` (Anthropic vía AWS Bedrock — mismo modelo, sin sacar datos de la nube de SMNYL). Swap del adaptador.
5. **Identidad de usuario explícita desde día 1**: aunque siempre sea `user_id="default"` en MVP, el modelo de datos lo incluye. Evita migraciones de schema dolorosas después.
6. **Configuración por entorno**: nada de paths absolutos hardcoded; todo viene de `.env` o config file. Cambiar de "local" a "EC2" = cambiar valores, no código.

---

## 2. Estado actual del MVP (snapshot)

> Esta sección se actualiza con cada release del MVP.

| Aspecto | Estado actual (Fase 2 completa) |
|---|---|
| Lenguaje | Python 3.11+ |
| UI | Streamlit (local, single-user) — router con 4 pantallas (home/importar/dashboard/entrevista) |
| LLM | Anthropic API directo vía `AnthropicClient`. Modelo: `claude-opus-4-7` con adaptive thinking. Prompt caching agresivo en contexto fijo (~12K tokens). |
| LLM abstraction | `LLMClient` Protocol — listo para swap a Bedrock sin tocar lógica de negocio |
| Persistencia | SQLite vía SQLAlchemy + Repository pattern (Documentos + Estados de entrevista). URL configurable por `DATABASE_URL` |
| Storage de archivos | `FilesystemStorage` implementa interfaz `Storage` (ya lista para swap a S3) |
| Configuración | `pydantic-settings` lee `.env` de forma tipada (`src/config.py`) |
| Auth | Ninguno (single-user, `USER_ID="default"` ya en modelo de datos) |
| Logs | (pendiente) `structlog` a stdout |
| Despliegue | `streamlit run app.py` en local |
| Containerización | Ninguna |

---

## 3. Inventario de features y su estrategia de migración

> **Cada feature que se agrega al MVP debe registrarse aquí.** Esta es la tabla más importante del documento.

| # | Feature | Implementación local actual | Cambios para migrar a EC2 | Riesgo de migración | Estado |
|---|---|---|---|---|---|
| 1 | Configuración via env vars | `.env` + `python-dotenv` + `pydantic-settings` | Mover valores a AWS Parameter Store / Secrets Manager; mismo código de carga | Bajo | ✅ Fase 0 |
| 2 | Logo + assets | Carpeta `assets/` local en disco | Servir desde S3 o CDN; ruta vía `Storage` interface | Bajo | ✅ Fase 0 |
| 3 | Modelos de dominio (Pydantic) | `src/core/models/` puro Python, sin I/O | Sin cambios | Nulo | ✅ Fase 1 |
| 4 | Persistencia de Documento | SQLite (`data/documente.db`) vía SQLAlchemy + `DocumentoRepository`; URL viene de `DATABASE_URL` | Cambiar `DATABASE_URL` a `postgresql://...`; SQLAlchemy se encarga del resto. Script de migración de datos si hay seed | Bajo | ✅ Fase 1 |
| 5 | Storage de archivos `.docx` | `FilesystemStorage` (interfaz `Storage`) escribe a `data/uploads/` y `data/exports/` | Implementar `S3Storage` que cumpla la misma interfaz; configurar IAM role para EC2 | Bajo | ✅ Fase 1 |
| 6 | DocxReader | Parsea `.docx` con `python-docx` desde un `Path` local que provee el Storage | Sin cambios — el reader recibe `Path`; con `S3Storage` el path local es una descarga temporal | Bajo | ✅ Fase 1 |
| 7 | GapAnalyzer | Pura lógica de dominio, sin I/O | Sin cambios | Nulo | ✅ Fase 1 |
| 8 | Use case `ImportarDocumento` | Inyecta dependencias (Storage, Reader, Repo, Analyzer) | Sin cambios — solo cambian las implementaciones inyectadas | Nulo | ✅ Fase 1 |
| 9 | UI Streamlit (router + 4 pantallas) | `app.py` + `src/ui/pages/` + componentes en `src/ui/components/` | Sin cambios funcionales; solo se containeriza | Bajo (ver §4 M1) | ✅ Fase 1 / 2 |
| 10 | Configuración tipada | `src/config.py` con `pydantic-settings` lee `.env` | Mover valores a AWS Parameter Store / Secrets Manager; el código de carga no cambia | Bajo | ✅ Fase 2 |
| 11 | LLMClient (interfaz) | `LLMClient` Protocol + `AnthropicClient` (Anthropic SDK directo) con prompt caching | Si TI/Riesgos pide no sacar datos: implementar `BedrockClient` (mismo modelo Claude vía AWS Bedrock) que cumpla el Protocol. Swap del adaptador inyectado | Bajo (1-2 días — M8) | ✅ Fase 2 |
| 12 | Prompts del sistema | `src/llm/prompts/` lee archivos de `docs/` y los ensambla con `lru_cache` | Sin cambios. Si en EC2 los archivos viven en S3, swap del loader | Bajo | ✅ Fase 2 |
| 13 | InterviewEngine + Drafter | Use cases puros que dependen del Protocol `LLMClient` | Sin cambios al cambiar de proveedor LLM | Nulo | ✅ Fase 2 |
| 14 | EstadoEntrevista (persistencia) | SQLite vía `EstadoEntrevistaRepository` + tabla `estados_entrevista` | Cambio de URI a PostgreSQL | Bajo | ✅ Fase 2 |
| 15 | Pantalla de entrevista (chat) | Streamlit `st.chat_input` + `st.session_state` para router | Sin cambios al containerizar; en multi-usuario añadir aislamiento por `user_id` (ya está en modelo) | Bajo | ✅ Fase 2 |
| 16 | Estrategia tiered de modelos | `LLMClient.chat()` con parámetro `tarea`; `AnthropicClient` mapea `chat→Sonnet 4.6`, `drafting→Opus 4.7`, `extraction→Haiku 4.5` | Sin cambios. Si TI pide Bedrock, swap del adaptador (mismo Protocol). | Bajo | ✅ Fase 2.5 |
| 17 | MetricasUso + pricing.py | Tarifas oficiales por modelo en `src/llm/pricing.py`; `LlamadaLLM` se acumula en `Documento.metricas_uso` automáticamente | Mantener tabla de tarifas actualizada cuando Anthropic publique cambios. Si se usa Bedrock, ajustar precios (suelen ser similares) | Bajo | ✅ Fase 2.5 |
| 18 | MemoriaModelo + KnowledgeExtractor (Haiku) | Memoria persistida con `Documento`. Extracción post-cierre best-effort con Haiku | Sin cambios — memoria es JSON serializado, vive con el documento. Haiku se usa solo para extracción. | Nulo | ✅ Fase 2.5 |
| 19 | Pantalla onboarding | Streamlit form con persistencia vía `DocumentoRepository` | Sin cambios | Nulo | ✅ Fase 2.5 |
| 20 | Apendices (Excel/CSV) | `Apendice` persistido con documento; archivos Excel/CSV en `Storage` (filesystem MVP) | Migrar archivos a S3 = swap del adaptador `Storage`. Apéndices ya tienen `archivo_id_storage` apuntando al ID interno del Storage. | Bajo | ✅ Fase 2.5 |
| 21 | Vista previa HTML | Streamlit pure (sin servir HTML por separado) | Sin cambios. Si se quiere endpoint público de preview, generar HTML estático desde el modelo Pydantic | Bajo | ✅ Fase 2.5 |
| — | *(filas se agregan aquí conforme avance el MVP)* | | | | |

**Convención de filas:**
- **Riesgo Bajo**: cambio mecánico, < 1 día de trabajo en migración.
- **Riesgo Medio**: requiere pruebas adicionales o adaptación; 1-3 días.
- **Riesgo Alto**: requiere rediseño parcial del feature; >3 días — **bandera roja, replantear ahora**.

Si alguna fila queda en "Riesgo Alto" durante el MVP → revisitar la implementación para bajarla a Medio o Bajo antes de avanzar.

---

## 4. Hitos de migración a EC2 (post-MVP, secuencial)

Cuando se decida ejecutar la migración (probablemente Fase 6 o post-MVP):

### M1 — Containerización
- Crear `Dockerfile` y `docker-compose.yml`.
- Validar que la app corre dentro de un contenedor localmente sin diferencia funcional respecto a `streamlit run app.py`.
- **Esfuerzo:** 1-2 días.

### M2 — Sustituir SQLite → PostgreSQL
- Cambiar `DATABASE_URL` en `.env` (de `sqlite:///...` a `postgresql://...`).
- SQLAlchemy se encarga del resto si seguimos el Repository pattern.
- Script de migración de datos (si hay datos de demo a preservar).
- **Esfuerzo:** 1-2 días.

### M3 — Sustituir filesystem local → S3
- Implementar `S3Storage` que cumple la interfaz `Storage` ya definida en MVP.
- Cambiar `EXPORTS_PATH` a un bucket S3.
- Configurar IAM role para EC2 con acceso al bucket.
- **Esfuerzo:** 1-2 días.

### M4 — Auth básica
- Opción A: `streamlit-authenticator` con base de datos de usuarios.
- Opción B: AWS Cognito como gateway de auth enfrente.
- Decisión informada por requerimientos de TI/Compliance de SMNYL.
- **Esfuerzo:** 3-5 días.

### M5 — Provisión EC2
- Terraform o consola AWS:
  - Instancia EC2 (t3.medium o similar, ajustable)
  - Security group (HTTPS only desde IPs autorizadas)
  - EBS volume para persistencia
  - Application Load Balancer con HTTPS (ACM cert)
  - Route 53 para DNS interno
- **Esfuerzo:** 2-3 días (con apoyo de TI).

### M6 — CI/CD
- GitHub Actions:
  - Build de imagen Docker
  - Push a ECR
  - Deploy a EC2 (vía SSM o sustitución blue/green)
- **Esfuerzo:** 2-3 días.

### M7 — Observabilidad
- CloudWatch logs (recolectados desde stdout del contenedor)
- Métricas básicas (CPU, memoria, latencia de requests)
- Alertas (Slack o email a Alberto)
- **Esfuerzo:** 1-2 días.

### M8 — Bedrock (opcional)
- Si TI/Riesgos pide no usar Anthropic API directo:
  - Implementar `BedrockClient` que cumple la interfaz `LLMClient`.
  - Configurar IAM role para EC2 con acceso a Bedrock.
  - Mismo modelo Claude, sin que datos salgan de la nube de SMNYL.
- **Esfuerzo:** 1-2 días.

**Total estimado: 13-22 días a tiempo parcial** = ~3-4 semanas.

---

## 5. Decisiones diferidas a la migración

Cosas que postergamos resolver hasta el momento de migrar:

| Decisión | Cuando se resuelve | Quién decide |
|---|---|---|
| Método de auth (Cognito / Streamlit auth / Active Directory) | M4 | TI SMNYL + Alberto |
| Dominio de la app (`documente.smnyl.com.mx` ?) | M5 | TI SMNYL |
| Certificados HTTPS (ACM provisto o cert internal) | M5 | TI SMNYL |
| ¿Anthropic API directo o Bedrock? | M8 (o antes si TI pide) | Riesgos + TI SMNYL |
| Tamaño de instancia EC2 | M5 | TI SMNYL (basado en uso esperado) |
| Backup strategy de PostgreSQL | M2 | TI SMNYL |
| Disaster recovery / multi-AZ | Post-migración | TI SMNYL |

---

## 6. Lo que el MVP NO debe hacer (porque rompería la migración)

- ❌ Hardcodear paths absolutos a archivos locales (todo via interfaz `Storage`)
- ❌ Usar `os.path.join` con `~/Documents` o similares
- ❌ Asumir un solo usuario en la lógica (el modelo `Documento` ya tiene `user_id` desde Fase 1)
- ❌ Usar Streamlit features que rompen multi-sesión (ej. variables globales mutables fuera de `st.session_state`)
- ❌ Asumir que `data/documente.db` siempre es accesible (toda escritura via Repository)
- ❌ Usar credenciales de Anthropic en código (siempre via env)
- ❌ Usar paths relativos al CWD sin pasar por config (ej. `open("data/foo.json")` directo)

Si en code review se detecta cualquiera de estos patrones → corregir antes de mergear.

---

## 7. Auditoría arquitectónica final (Fase 6)

Antes de cerrar el MVP, ejecutar checklist:

- [ ] Toda persistencia pasa por `Repository` o `Storage` interface
- [ ] El `LLMClient` es una interfaz; hoy hay un `AnthropicClient`
- [ ] Modelo `Documento` tiene campo `user_id` (aunque siempre sea `"default"`)
- [ ] Toda config vive en `.env` o archivo de config — nada hardcoded
- [ ] No hay paths absolutos en código de negocio
- [ ] Logs son estructurados (`structlog`) y van a stdout
- [ ] Esta tabla §3 está al día con todos los features del MVP
- [ ] No hay secretos commiteados al repo
- [ ] Tests pasan en CI (cuando exista)

Si todo pasa → **migración será mecánica**. Si algo falla → refactor antes de cerrar MVP.
