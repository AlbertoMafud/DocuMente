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

| Aspecto | Estado actual (Fases 0–4 completas, sesión 7) |
|---|---|
| Lenguaje | Python 3.11+ |
| UI | Streamlit (local, single-user) — router con 7 pantallas (home, importar, onboarding, dashboard, entrevista, vista_previa, auditoria) |
| LLM | Anthropic API directo vía `AnthropicClient` con estrategia tiered: Sonnet 4.6 (chat), Opus 4.7 (drafting), Haiku 4.5 (extraction). Prompt caching agresivo en contexto fijo (~12K tokens) |
| LLM abstraction | `LLMClient` Protocol — listo para swap a Bedrock sin tocar lógica de negocio |
| Persistencia | SQLite vía SQLAlchemy + Repository pattern (Documentos + Estados de entrevista). URL configurable por `DATABASE_URL` |
| Storage de archivos | `FilesystemStorage` implementa interfaz `Storage` (ya lista para swap a S3) |
| Configuración | `pydantic-settings` lee `.env` de forma tipada (`src/config.py`) |
| Auth | Ninguno (single-user, `USER_ID="default"` ya en modelo de datos) |
| Logs | (pendiente) `structlog` a stdout |
| Despliegue | `streamlit run app.py` en local |
| Containerización | Ninguna |
| Generación DOCX | `DocxWriter` con `docxtpl` + plantilla maestra editada manualmente; Subdoc + RichText con bold/italic reales; tablas nativas con `Table Grid` y font adaptable |
| Multilenguaje | Toggle ES/EN en export. `TraductorDocumento` con prompt para inglés corporativo americano (efímero, no se persiste) |
| State machine | `DocumentStateMachine` con 5 estados oficiales MRM + sign-offs Reviewer/FAE como audit events inmutables |
| Tests | 174 tests pasan; ruff clean; mypy strict |

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
| 22 | DocumentStateMachine + transiciones | Lógica pura en `src/core/rules/`. State machine valida `draft → in_review → approved → published → retired` contra reglas MRM §10 | Sin cambios. Lógica pura, sin I/O | Nulo | ✅ Fase 4 |
| 23 | Sign-offs Reviewer/FAE | Audit events inmutables `signoff_reviewer` y `signoff_fae`. UI con checkbox de afirmación de independencia | En multi-user real, vincular sign-off al `user_id` del actor (ya disponible en modelo) | Bajo | ✅ Fase 4 |
| 24 | Timeline de auditoría (UI) | Componente Streamlit con CSS custom inyectado. Filtros por tipo de evento | Sin cambios | Nulo | ✅ Fase 4 |
| 25 | Omitir sección con motivo | `Completitud` extendido con `"omitida"`; nuevo evento `seccion_omitida`; state machine usa `porcentaje_resuelto` | Sin cambios; aditivo y backward-compatible | Nulo | ✅ Sesión 7 |
| 26 | DocxWriter | `docxtpl` + plantilla `model_development_smnyl_final.docx`; Subdoc con RichText (bold/italic reales); tablas nativas con `Table Grid` y font adaptable; `TableExtractor` con Haiku para 4 secciones tabulares | Sin cambios al código. La plantilla maestra debe seguir presente en `src/docs/templates/`; cuando S3 sea storage, la plantilla puede vivir en S3 o en disco del contenedor | Bajo | ✅ Fase 3 |
| 27 | ExportarDocumento + audit `exportado` | Use case orquestador: TableExtractor + DocxWriter + audit. UI con `st.download_button` post-generación | Sin cambios | Nulo | ✅ Fase 3 |
| 28 | TraductorDocumento (ES → EN) | Use case con prompt específico para U.S. corporate English. Sonnet (no Opus). Mutación efímera del documento — no persiste traducción | Sin cambios. Si TI elige Bedrock, sigue funcionando idéntico (mismo Protocol). | Nulo | ✅ Sesión 7 |
| 29 | Toggle de idioma en UI | Modal `st.dialog` en dashboard con radio Español / English; pasa `idioma_objetivo` al use case | Sin cambios | Nulo | ✅ Sesión 7 |
| 30 | Editor de metadata del modelo | Modal `st.dialog` para editar 8 campos clave; cambios registrados en audit como `metadata_actualizada` con delta exacto | Sin cambios | Nulo | ✅ Sesión 7 |
| 31 | Apéndices con tabla nativa | `markdown_blocks` separa contenido_md en `BloqueProsa` y `BloqueTabla`. Las tablas se incrustan con `subdoc.add_table()` y font 7-10pt adaptable | Sin cambios | Nulo | ✅ Sesión 7 |
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

---

## 8. Runbook de migración (paso a paso para el arquitecto)

> Esta sección es lo que el arquitecto ejecuta. Asume que ya tiene clonado el repo, acceso SSH a una EC2 ya provisionada, y endpoints de RDS y S3.

### 8.1 Archivos del repo que SÍ se copian a EC2

```
DocuMente/
├── app.py                    # entry point
├── pyproject.toml            # dependencias y configuración
├── src/                      # todo el código fuente
│   ├── core/                 # dominio + use cases
│   ├── llm/                  # cliente LLM + prompts
│   ├── ui/                   # páginas y componentes Streamlit
│   ├── docs/                 # reader, writer, plantilla
│   │   └── templates/
│   │       └── model_development_smnyl_final.docx   # CRÍTICO: el activo estético
│   ├── storage/              # repositorios y storage abstraction
│   └── config.py             # carga de settings
├── tests/                    # tests automatizados (para correr en EC2 si quieren)
├── docs/                     # documentación (este archivo + MRM_REQUIREMENTS, etc.)
├── assets/                   # logo SMNYL + fonts (no incluye el .docx plantilla)
└── README.md
```

### 8.2 Archivos / carpetas que NO se copian

| Archivo / carpeta | Por qué no |
|---|---|
| `.env` | Contiene credenciales locales. En EC2 se crea uno nuevo con valores de Secrets Manager |
| `data/documente.db` | Base de datos local (SQLite). En EC2 los datos viven en RDS PostgreSQL — vacía al inicio |
| `data/uploads/`, `data/exports/`, `data/backups/` | Archivos locales del usuario. En EC2 viven en S3 — bucket vacío al inicio |
| `.venv/` o `venv/` | Entorno Python local. Se reinstala en EC2 con `pip install -e ".[dev]"` |
| `__pycache__/`, `*.pyc` | Caché de Python. Se regenera |
| `.pytest_cache/`, `.ruff_cache/` | Caché de tooling. Se regenera |
| `.git/` | Si se clona vía `git clone`, ya viene incluido y eso está OK. Si se hace `scp -r`, no se copia y luego no hay forma de actualizar |
| Archivos `~$<nombre>.docx` | Lock files de Word abierto en local |

**Recomendación:** clonar el repo desde un GitHub privado de SMNYL (no `scp` de la máquina de Alberto). Eso permite que cada deploy futuro sea `git pull`.

### 8.3 Variables de entorno requeridas en EC2

Todas viven en `/etc/documente/.env` (o equivalente) y son leídas por `pydantic-settings` al arrancar:

```env
# === LLM ===
ANTHROPIC_API_KEY=sk-ant-api03-...               # Key corporativa SMNYL, NO la personal de Alberto
# (alternativa) AWS_BEDROCK=true                  # Si TI elige Bedrock; ANTHROPIC_API_KEY no se usa

# === Persistencia ===
DATABASE_URL=postgresql://documente:<pass>@<rds-endpoint>:5432/documente

# === Storage ===
STORAGE_BACKEND=s3                                # 'filesystem' (MVP) o 's3' (prod)
S3_BUCKET=smnyl-documente-uploads-prod
AWS_REGION=us-east-1
# (las credenciales IAM las hereda la EC2 vía role; no se ponen aquí)

# === Auth ===
AUTH_BACKEND=cognito                              # 'none' (MVP), 'cognito', o 'streamlit-authenticator'
COGNITO_USER_POOL_ID=us-east-1_XXXXX
COGNITO_CLIENT_ID=...

# === Configuración general ===
USER_ID_DEFAULT=default                           # Solo se usa si AUTH_BACKEND=none
LOG_LEVEL=INFO
EXPORTS_PATH=/tmp/documente-exports               # Solo si STORAGE_BACKEND=filesystem
```

### 8.4 Comandos de instalación (paso a paso)

```bash
# Conectar
ssh -i smnyl-key.pem ec2-user@documente.smnyl.local

# Setup base
sudo yum install -y python3.11 git nginx
sudo useradd -m documente
sudo mkdir -p /opt/documente /etc/documente

# Clonar
sudo -u documente git clone <github-url> /opt/documente
cd /opt/documente

# Entorno virtual
sudo -u documente python3.11 -m venv .venv
sudo -u documente .venv/bin/pip install --upgrade pip
sudo -u documente .venv/bin/pip install -e ".[dev]"

# Configuración (.env desde Secrets Manager)
sudo aws secretsmanager get-secret-value --secret-id documente/prod/env \
    --query SecretString --output text | sudo tee /etc/documente/.env
sudo chmod 600 /etc/documente/.env

# Migración de schema (PostgreSQL)
sudo -u documente .venv/bin/python -m src.storage.init_schema

# Servicio systemd (ver §8.5)
sudo cp deploy/documente.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable documente
sudo systemctl start documente

# nginx delante (ver §8.6)
sudo cp deploy/documente.nginx.conf /etc/nginx/conf.d/documente.conf
sudo systemctl reload nginx
```

### 8.5 Servicio systemd (`/etc/systemd/system/documente.service`)

```ini
[Unit]
Description=DocuMente Streamlit App
After=network.target

[Service]
Type=simple
User=documente
WorkingDirectory=/opt/documente
EnvironmentFile=/etc/documente/.env
ExecStart=/opt/documente/.venv/bin/python -m streamlit run app.py \
    --server.port 8501 \
    --server.address 127.0.0.1 \
    --server.headless true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 8.6 nginx delante (HTTPS)

```nginx
server {
    listen 443 ssl;
    server_name documente.smnyl.local;

    ssl_certificate /etc/ssl/smnyl/cert.pem;
    ssl_certificate_key /etc/ssl/smnyl/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

### 8.7 Subsecuentes deploys (cuando se mergea código nuevo)

```bash
ssh ec2-user@documente.smnyl.local
cd /opt/documente
sudo -u documente git pull
sudo -u documente .venv/bin/pip install -e ".[dev]"
sudo systemctl restart documente
```

Si hay CI/CD: este flujo se automatiza vía GitHub Actions / CodePipeline (M6).

### 8.8 Plan de rollback

Si un deploy rompe algo:

```bash
cd /opt/documente
sudo -u documente git log --oneline -5      # ver commits recientes
sudo -u documente git reset --hard <hash-anterior>
sudo -u documente .venv/bin/pip install -e ".[dev]"
sudo systemctl restart documente
```

Datos en BD/S3 NO se afectan por rollback de código (excepto si hubo migration que cambió schema — diseñar migrations aditivas para evitar esto).

### 8.9 Checklist de validación post-deploy

Después de cada deploy a EC2:

- [ ] `systemctl status documente` → `active (running)`
- [ ] `curl -k https://documente.smnyl.local/_stcore/health` → `200 OK`
- [ ] Login con un usuario de prueba funciona
- [ ] Importar un `.docx` de prueba funciona
- [ ] Exportar un `.docx` (en español e inglés) funciona
- [ ] CloudWatch muestra logs de la app sin errores
- [ ] RDS conexión OK; tabla `documentos` accesible
- [ ] S3 escritura/lectura OK; bucket vacío inicialmente
- [ ] Tests automatizados corren contra el ambiente: `pytest tests/integration/ -k "smoke"`

