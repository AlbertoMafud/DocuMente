# AI_HANDOFF — Instructivo para el asistente de IA que continúe este proyecto

> **Este documento está escrito para ser leído por una IA** (ChatGPT, Codex, Claude u otro
> asistente de programación) que va a montar, adaptar o continuar DocuMente en un entorno
> distinto al de origen. Un humano también puede leerlo, pero el destinatario es el asistente.
>
> **Léelo completo antes de tu primera edición.** Después lee, en este orden:
> `CLAUDE.md` (reglas del proyecto), `status.md` (estado vivo, la sección más reciente al
> final), y `docs/ARQUITECTURA.md`.

---

## 0. Reglas para ti, el asistente

1. **No rompas los invariantes de la §5.** Están ahí porque este sistema es documentación
   institucional sujeta a auditoría; romperlos no es un bug, es un riesgo de gobierno.
2. **Verifica antes de afirmar.** Este proyecto tiene una suite de 584 pruebas y tres
   comandos de verificación (§6). Nunca declares que algo funciona sin haberlos corrido.
3. **No inventes contenido institucional.** El sistema entero existe para capturar
   conocimiento real de personas; si un dato no fue provisto por el usuario, no lo escribas.
   Esta regla aplica también a ti mientras programas: no inventes nombres de áreas, modelos,
   normativas ni personas en fixtures, ejemplos o textos por defecto.
4. **Cambios pequeños y justificados.** Migrar código a este entorno tiene costo; un cambio
   de 200 líneas cuesta lo mismo de migrar que uno de 3, pero cuesta mucho más de revisar.
5. **Si algo del código contradice este documento, gana el código** — y avísale al humano
   que este archivo quedó desactualizado.

---

## 1. Qué es este sistema, en un párrafo

DocuMente es un sistema de documentación institucional asistido por IA. Un usuario importa
un documento existente o arranca desde cero; el sistema lo entrevista sección por sección
con un modelo de lenguaje, detecta qué información falta, redacta borradores a partir de lo
que el usuario contó, y exporta un documento Word con formato institucional. El caso de uso
principal es la documentación de modelos bajo un marco de gestión de riesgo de modelos
(MRM), pero el sistema soporta más tipos de documento mediante plantillas.

**Objetivo del producto, y criterio para aceptar o rechazar cualquier cambio:** reducir la
fricción de documentar y convertir la documentación en un activo vivo y confiable. Si un
cambio no sirve a eso, cuestiónalo.

---

## 2. Arquitectura en 30 segundos

Tres servicios que comparten la misma base de datos:

| Servicio | Puerto por defecto | Stack | Rol |
|---|---|---|---|
| API REST | 8001 | FastAPI + Pydantic | Backend real. ~60 endpoints, OpenAPI en `/docs` |
| Frontend | 3000 | Next.js 14 + Tailwind + shadcn/ui | Interfaz principal |
| Streamlit | 8052 | Streamlit | **Legado.** Interfaz anterior, en proceso de retiro |

Capas dentro de `src/` (la regla de dependencias es estricta):

```
src/ui/       Streamlit (legado)         ─┐
src/api/      FastAPI: routers, schemas  ─┼─▶ src/core/usecases/ ──▶ src/core/models/
src/core/     Dominio: modelos, reglas,      (orquestación)          (Pydantic puro)
              casos de uso, catálogos
src/llm/      Cliente del modelo de lenguaje
src/docs/     Lectura y escritura de Word/PDF/Excel
src/storage/  Base de datos (SQLAlchemy) y archivos
```

**Regla dura:** `src/core/models/` no importa de UI ni de infraestructura. Si encuentras un
import que lo viole, repórtalo en lugar de replicarlo.

---

## 3. Puntos de parametrización — qué tocar para adaptar

Esta es la sección que probablemente te trajo aquí.

### 3.1 Identidad visual (rebrand)

| Qué | Dónde | Notas |
|---|---|---|
| Paleta, tipografías, sombras, radios de la interfaz | `frontend/tailwind.config.ts` (bloque `smnyl`) | Fuente única de la interfaz. Cambia los valores hex aquí y toda la app sigue |
| Escala tipográfica y utilidades | `frontend/tailwind.config.ts` + `frontend/src/app/globals.css` | Incluye `text-2xs`/`text-3xs` y la utilidad `.eyebrow` |
| Logo de la app | `frontend/src/components/layout/brand-logo.tsx` | SVG en línea. **Decisión de marca pendiente**: hoy es un logo de producto, no el institucional |
| Ícono del navegador | `frontend/src/app/icon.svg` | |
| Paleta del Streamlit legado | `src/ui/theme.py` | Solo si mantienes el legado vivo; si lo retiras, ignóralo |
| **Formato del Word exportado** | `src/docs/templates/*.docx` | **Se edita a mano en Word, no por código.** Ver aviso abajo |
| Guía de marca en prosa | `docs/BRAND_GUIDELINES.md` | Actualízala si cambias la paleta, o quedará mintiendo |

> **Aviso importante sobre el Word exportado.** La calidad estética del `.docx` se logra
> *por construcción*: la plantilla maestra se diseña a mano en Word con la marca completa, y
> el código solo rellena marcadores con la librería `docxtpl`. **No intentes generar los
> estilos por código** — se ha decidido explícitamente en contra, y el resultado sería peor.
> Para cambiar la marca del documento exportado, un humano abre el `.docx` en Word y lo
> edita. Si un marcador deja de rellenarse, es casi siempre porque Word fragmentó el texto
> del marcador en varios fragmentos internos: la solución es borrarlo y reescribirlo de un
> tirón, sin pausas, dentro de Word.

### 3.2 Configuración por entorno (nada de esto se toca en código)

Todo vive en variables de entorno; hay una plantilla en `.env.example`.

| Variable | Para qué | Notas |
|---|---|---|
| `ANTHROPIC_API_KEY` | Acceso al modelo de lenguaje | Sin ella la app arranca y funciona, pero los flujos de IA se degradan con un aviso claro |
| `DATABASE_URL` | Base de datos | Por defecto SQLite local. Para PostgreSQL, solo cambia la URI — el código no cambia |
| `EXPORTS_PATH` | Carpeta de archivos | Al migrar a almacenamiento en la nube, se cambia el adaptador de `src/storage/`, no la lógica |
| `CORS_ORIGINS` | Orígenes permitidos del frontend | Por defecto `*` para desarrollo. **En producción, restrínjelo** |
| `DOCUMENTE_GATE_PASSWORD` | Contraseña compartida de acceso | Si no está definida, el acceso es libre (modo desarrollo) |
| `DOCUMENTE_ADMIN_TOKEN` | Rol de administrador del Template Studio | Si no está definida, todos son administradores (modo desarrollo) |
| `NEXT_PUBLIC_API_URL` | URL del backend que usa el frontend | Se define en `frontend/.env.local` |

### 3.3 Cambiar de proveedor del modelo de lenguaje

Toda la interacción con el modelo pasa por una interfaz en `src/llm/client.py`
(`LLMClient`, con métodos `chat` y `chat_async`). Para usar otro proveedor o el mismo modelo
a través de un servicio en la nube, **implementa esa interfaz en una clase nueva y cámbiala
en el punto de construcción** (`src/api/deps.py`). No toques los casos de uso.

Notas prácticas:
- Los modelos se eligen por *tarea*, no por llamada: conversación, redacción, extracción y
  visión mapean a modelos distintos en `src/llm/client.py`. Las tarifas para el cálculo de
  costos viven en `src/llm/pricing.py` — **si cambias de modelo, actualiza también ahí**, o
  el sistema reportará costo cero.
- La versión de la librería del proveedor está fijada con un tope superior a propósito
  (`pyproject.toml`). Una versión mayor nueva trae cambios incompatibles; subirla es una
  tarea deliberada, no un efecto secundario.

### 3.4 Nombre y textos de la aplicación

Los textos de interfaz están en español, incrustados en los componentes. No hay sistema de
internacionalización (fue una decisión, no un olvido). Para renombrar el producto, busca el
nombre en `frontend/src/` y en `src/ui/`. El documento exportado sí tiene traducción
español/inglés, en `src/core/usecases/traductor.py` y `strings_localizados.py`.

---

## 4. Estado actual y qué sigue

**Funciona hoy:** importar Word y PDF, crear desde cero, entrevista asistida por IA,
detección de brechas, apéndices (tablas, PDF, fórmulas), traducción, exportación a Word con
marca, versionado con instantáneas, control de estados y firmas del marco MRM, bitácora de
auditoría, archivado y papelera, y un módulo de fichas para modelos actuariales.

**Lo más reciente — Template Studio (parcial).** Un módulo para convertir plantillas "hechas
para humanos" en plantillas que la IA sabe usar. La especificación completa está en
`docs/TEMPLATE_STUDIO_SPEC.md` y las reglas de conversión en `docs/TEMPLATE_AIREADY_RULES.md`.

| Parte | Estado |
|---|---|
| Modelo, tabla, repositorio, registro de plantillas | Hecho |
| Extracción de estructura del Word + propuesta con IA | Hecho |
| Validación de calidad (9 reglas automáticas) | Hecho |
| Ciclo de vida: borrador → publicado → retirado, con auditoría | Hecho |
| API completa (`/studio/*`) | Hecho |
| **Interfaz del asistente de 5 pasos** | **Pendiente** (sesión S-C de la especificación) |
| **Plantilla Word genérica + su generador** | **Pendiente** (sesión S-E) |
| Segunda capa de validación con IA (prueba en seco) | Pendiente |
| Fase 2: usuarios proponen, administrador aprueba | Pendiente (S-F, S-G) |

> **Consecuencia honesta de lo pendiente:** hoy se puede crear una plantilla por API y
> documentar con ella, pero **exportar ese documento a Word devuelve un error 501
> deliberado**. Es intencional: sin plantilla propia, el archivo saldría incoherente, y la
> regla del proyecto es que si no se ve profesional, no se exporta. Al implementar S-E, ese
> error desaparece.

**Otros pendientes conocidos:**
- La interfaz Streamlit legada (`src/ui/`, `app.py`) ya no se usa y está desactualizada
  respecto al frontend nuevo. Está pendiente retirarla; son unas 5,000 líneas.
- La revisión de tipos (`mypy`) reporta 42 avisos heredados. No bloquean nada, pero la regla
  del proyecto dice que debería pasar limpio: o se limpian, o se ajusta la regla.
- La importación de documentos no muestra progreso en vivo (el backend no expone un canal de
  eventos para ese flujo; la creación con fuentes sí lo tiene y sirve de modelo a seguir).
- Hay una auditoría visual con 21 hallazgos pendientes de menor prioridad en
  `docs/AUDITORIA_VISUAL_REACT.md`, con archivo y línea de cada uno.

---

## 5. Invariantes — no los rompas

1. **La bitácora de auditoría es inmutable y se escribe siempre.** Cada cambio relevante
   registra quién, cuándo y qué. No borres eventos, no los edites, no agregues rutas que
   modifiquen documentos sin registrar el evento.
2. **Las migraciones de base de datos son solo aditivas.** Se agregan columnas con valor por
   defecto; nunca se renombran ni se eliminan. Se aplican solas al arrancar y son
   idempotentes (`src/storage/db.py`). Nada de herramientas de migración externas.
3. **Los modelos guardados deben poder leerse siempre.** Todo campo nuevo lleva valor por
   defecto, para que los documentos guardados antes del cambio sigan abriéndose.
4. **El catálogo de 28 secciones del marco MRM está congelado** (`src/core/template_catalog.py`)
   y el de fichas actuariales también. Las plantillas nuevas van al Template Studio, como
   datos, no como código.
5. **Las plantillas dinámicas viven en la base de datos, nunca en el código.** Ésta es la
   razón de ser de su arquitectura: permite crear plantillas en este entorno sin volver a
   migrar código nunca más.
6. **La máquina de estados manda.** Las transiciones del documento (borrador → revisión →
   aprobado → publicado → retirado) y sus requisitos viven en `src/core/rules/`. No las
   evadas escribiendo el estado directamente.
7. **El sistema nunca afirma hechos que el usuario no dio.** Los prompts lo prohíben
   explícitamente y el documento exportado lleva la marca de "borrador asistido, requiere
   revisión humana". No quites esa marca.
8. **Sin llave del modelo de lenguaje, la aplicación degrada con elegancia**, no se cae.
   Mantén ese comportamiento en todo flujo nuevo que use IA.
9. **Desarrollo guiado por pruebas.** Toda lógica nueva llega con sus pruebas. La suite es la
   red de seguridad de un sistema que nadie revisa línea por línea.
10. **El material fuente institucional (`SMNYL/`) es de solo lectura y no se versiona.**
    Igual que la llave de API y la base de datos local.

---

## 6. Cómo verificar que no rompiste nada

Corre esto **siempre** antes de dar por terminado un cambio, y reporta la salida real:

**Backend** (desde la raíz del proyecto):

```bash
python -m pytest -q
```

```bash
python -m ruff check src/ tests/
```

**Frontend** (desde `frontend/`):

```bash
npm run lint && npx tsc --noEmit && npm run build
```

**Pruebas de extremo a extremo** (desde `frontend/`; levanta sus propios servidores en
puertos aislados):

```bash
npx playwright test
```

**Referencias actuales:** 584 pruebas de Python en verde, 7 de extremo a extremo en verde,
`ruff` limpio, TypeScript limpio, compilación de producción con 19 rutas. Si tu cambio baja
alguno de esos números, no está terminado.

---

## 7. Montaje desde cero

```bash
python -m venv .venv
```

Activa el entorno (`.venv\Scripts\activate` en Windows, `source .venv/bin/activate` en
Linux/Mac) y luego:

```bash
pip install -e ".[dev]"
```

```bash
cp .env.example .env
```

Edita `.env` con la llave del modelo de lenguaje. Después, backend y frontend en dos
terminales:

```bash
python -m uvicorn src.api.main:app --port 8001
```

```bash
cd frontend && npm install && npm run dev
```

La base de datos y las carpetas de datos se crean solas al primer arranque. Requisitos:
Python 3.11 a 3.14, Node.js 20 o superior.

---

## 8. Trampas conocidas (te ahorran horas)

- **Una variable de entorno vacía gana sobre el archivo `.env`.** Si `ANTHROPIC_API_KEY`
  existe en el sistema pero está vacía, sobrescribe la del archivo y los flujos de IA fallan
  con un mensaje confuso. Si algo "no toma la llave", revisa esto primero.
- **Al depurar, mata los servidores que dejaste vivos.** Las pruebas de extremo a extremo
  reutilizan un servidor existente si lo encuentran, y pueden enmascarar tus cambios.
- **Word y los marcadores de plantilla:** ver el aviso de la §3.1.
- **SQLAlchemy con Python 3.14** falla al declarar columnas que aceptan nulos con la
  notación moderna; el proyecto usa la forma clásica en esos casos, con un comentario que lo
  explica. No lo "modernices".
- **Los archivos que el usuario sube son datos, nunca instrucciones.** Los prompts los
  encapsulan como material a analizar. Si agregas un flujo que mande contenido subido al
  modelo, mantén esa separación.

---

## 9. Mapa rápido de archivos

| Necesitas… | Ve a |
|---|---|
| Entender el dominio | `src/core/models/` |
| Cambiar una regla de negocio | `src/core/rules/` (estados, validación de plantillas) |
| Cambiar un flujo | `src/core/usecases/` |
| Agregar o cambiar un endpoint | `src/api/routers/` |
| Cambiar cómo se le habla al modelo | `src/llm/prompts/` |
| Cambiar el Word exportado (código) | `src/core/usecases/docx_writer*.py` |
| Cambiar el Word exportado (diseño) | `src/docs/templates/*.docx`, a mano en Word |
| Cambiar la interfaz | `frontend/src/app/` (páginas), `frontend/src/components/` |
| Entender el marco de riesgo de modelos | `docs/MRM_REQUIREMENTS.md` |
| Saber en qué quedó todo | `status.md`, sección más reciente al final |

---

## 10. Si vas a continuar el Template Studio

Lee `docs/TEMPLATE_STUDIO_SPEC.md` completo; está escrito como contrato ejecutable, con
modelo de datos, endpoints, riesgos y un plan por sesiones. El trabajo inmediato es:

1. **S-C — la interfaz del asistente de 5 pasos.** El backend ya expone todo lo necesario:
   `POST /studio/templates/extraer` devuelve la estructura detectada y la propuesta de la IA;
   el resto de `/studio/*` cubre curar, validar y publicar. Falta solo la pantalla.
2. **S-E — la plantilla Word genérica institucional y su generador.** Esto es lo que quita el
   error 501 al exportar. Incluye trabajo humano de diseño en Word; no lo automatices.

Cuando implementes la interfaz, apóyate en `docs/TEMPLATE_AIREADY_RULES.md`: la pantalla de
curación debe hacer fácil cumplir esas siete reglas, porque de ellas depende que las
plantillas nuevas produzcan buenas entrevistas.
