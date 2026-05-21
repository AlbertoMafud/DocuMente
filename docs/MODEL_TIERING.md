# MODEL_TIERING — qué LLM usa DocuMente para cada cosa

> Documento de referencia para el equipo. Si cambias el tier en
> `src/llm/client.py:32-37` (`_MODELO_POR_TAREA_DEFAULT`), actualiza este
> archivo en el mismo commit.

## Resumen ejecutivo

DocuMente NO usa un solo modelo para todo. Cada tarea elige el modelo
apropiado para su perfil de calidad/latencia/costo. Esto está hardcoded
en `src/llm/client.py` y es deliberado — la mezcla actual se balanceó
con base en pruebas reales y la prioridad del proyecto: **calidad del
output institucional > costo**.

| Tarea | Modelo | Justificación |
|---|---|---|
| `chat` — entrevista interactiva | **Claude Sonnet 4.6** | Excelente conversacional. Volumen alto, latencia importa. ~3× más barato que Opus. |
| `drafting` — borradores finales y polish | **Claude Opus 4.7** | Calidad institucional. Solo 1-2 llamadas por documento; costo justificable. |
| `extraction` — parseo tabular y estructurado | **Claude Haiku 4.5** | Prompts cortos, volumen alto, no requiere razonamiento profundo. Costo ~10× menor que Sonnet. |
| `vision` — describir imágenes embebidas (S16) | **Claude Haiku 4.5** (multimodal) | Describir screenshots/diagramas en 3-4 frases no requiere modelos premium. Costo marginal por imagen. |

## Quién consume cada tier

### `chat` (Sonnet 4.6)
- `interview_engine.py` → entrevista por sección (turnos alternados con el usuario)
- `traductor.py` → traducción ES↔EN al exportar (cuando el idioma cambia)

### `drafting` (Opus 4.7)
- `drafter.py` → genera el borrador final de una sección al cerrar la entrevista
- `sugerencias_multifuente.py` → prepuebla secciones desde fuentes (PDFs, Excel, etc.)
- `structure_realigner.py` → re-mapea estructura cuando el ancla no coincide con el template NYL
- `document_polisher.py` → revisión de coherencia entre secciones (opcional al exportar)

### `extraction` (Haiku 4.5)
- `table_extractor.py` → detecta columnas y esquema de un Excel/CSV
- `knowledge_extractor.py` → extracción de hechos estructurados desde texto plano

### `vision` (Haiku 4.5 multimodal) — agregado en S16
- `vision_describer.py` → describe imágenes embebidas en PDFs y DOCX
- Consumido opcionalmente por `pdf_reader.py` y `docx_reader_simple.py`
  cuando el flag `describir_imagenes=True` se pasa al endpoint

## Contexto típico por llamada

Estimación bruta del tamaño de input por llamada (tokens):

| Componente | Tokens típicos | Cacheado? |
|---|---|---|
| Contexto fijo: template NYL completo + extracto MRM + lineamientos de marca + tono | ~12K | **Sí (ephemeral)** — se paga 1× por sesión |
| Estado actual del documento (secciones + metadata) | 2K - 5K | No |
| Sección o turno activo | 1K - 3K | No |
| Fuentes externas (importadas/cargadas) | 5K - 50K | No (varía por upload) |
| **Total típico** | **20K - 70K** | — |

Con prompt caching, después de la primera llamada de una sesión el
**~90% de los tokens de input se leen del cache** (factor 10× más barato
que tokens nuevos). Esto hace que la entrevista interactiva, que llama
al LLM en cada turno, sea económica.

Ventana de contexto disponible: 200K (Opus/Sonnet) o 200K (Haiku 4.5).
Holgada para todos los casos actuales.

## Costos estimados

Precios públicos de Anthropic (USD por 1M tokens, sin cache; cache hits ~10× más barato):

| Modelo | Input | Output |
|---|---|---|
| Claude Opus 4.7 | $15 | $75 |
| Claude Sonnet 4.6 | $3 | $15 |
| Claude Haiku 4.5 | $1 | $5 |

**Costo típico por documento**:

| Flujo | Tier | Tokens aprox | Costo aprox |
|---|---|---|---|
| Entrevista completa (28 secciones, ~5 turnos c/u) | chat (Sonnet) | 140 llamadas × ~5K input + ~500 output | ~$1 - $3 |
| Drafter al cerrar cada sección (28×) | drafting (Opus) | 28 × ~15K input + 2K output | ~$3 - $6 |
| Polish coherencia (1× al exportar) | drafting (Opus) | ~50K input + 5K output | ~$0.50 |
| Extracción de tablas de Excel adjunto | extraction (Haiku) | ~10K input + 1K output | ~$0.01 |
| Visión por imagen embebida (S16) | vision (Haiku) | ~1.5K input (b64) + 200 output | ~$0.001-0.005 |

**Total documento maduro completo: ~$5-10 USD**. La mayor parte se va en
el drafter (28 llamadas a Opus). Cuando salgamos a producción y volumen
crezca, vale la pena evaluar si bajar drafter a Sonnet con un eval framework.

## Por qué NO cambiar el tiering ahora (S15+S16)

Cambiar el modelo del tier `drafting` (de Opus a Sonnet, por ejemplo)
sin un eval framework de calidad **es riesgo de regresión silenciosa**:
los outputs van a verse "OK", pero pueden volverse menos coherentes,
con menos vocabulario técnico actuarial, o con razonamiento más
superficial — y nos enteraríamos solo en piloto formal.

**Para cambiar tier en el futuro, primero**:

1. Construir un eval con 5-10 ejemplos institucionales reales (secciones
   completas redactadas por un actuario senior).
2. Generar la misma sección con Opus y con Sonnet en paralelo (ambos
   con el mismo contexto y prompts).
3. Comparar ciegas — un experto del dominio rankea cuál es mejor.
4. Solo cambiar si Sonnet empata o supera en ≥80% de los casos.

## Override por env var (opcional)

La env var `CLAUDE_MODEL` en `.env` **NO se aplica hoy** al diccionario
hardcoded. Es un bug menor — la variable existe en `Settings` pero
ningún use case la consulta. Para habilitarla habría que:

- Inyectar `modelos_override` al `AnthropicClient.__init__` desde
  `src/api/deps.py` leyendo `settings.claude_model`, y
- Decidir si la env var aplica a TODOS los tiers o solo a uno específico
  (probablemente solo a `drafting` — el más caro y donde más se ahorra).

Está fuera de scope S16 — se anota para una iteración futura cuando
haya eval framework.

## Bug pequeño detectado en S15 (no relacionado a modelos)

`src/storage/db.py:33-42` — `_resolver_database_url()` lee
`os.environ['DATABASE_URL']` **directamente** sin pasar por
`get_settings()`. Esto causa que el `.env` NO se aplique al SQLAlchemy
engine (sí se aplica al resto de `Settings`, incluyendo
`ANTHROPIC_API_KEY` y `CLAUDE_MODEL`).

**Síntoma observado en S15**: aunque el `.env` decía
`DATABASE_URL=sqlite:///data/documente_demo.db`, el backend siguió
escribiendo a `data/documente.db` (el default hardcoded).

**Workaround actual**: arrancar uvicorn con `export DATABASE_URL=...`
explícito en el shell.

**Fix sugerido** (3 líneas, opcional para una sesión futura):

```python
# src/storage/db.py
from src.config import get_settings

def _resolver_database_url() -> str:
    return get_settings().database_url
```

Esto haría que el `.env` se aplique correctamente y, de paso, que
también se respete cualquier override de Settings (útil para tests).

No es crítico — funciona con el workaround — pero conviene cerrarlo
antes de deploy a EC2 para no tener sorpresas con PostgreSQL.
