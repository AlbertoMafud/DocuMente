# Guía DocuMente — entiende todo el proyecto

> Documento personal de Alberto. Dos partes:
>
> - **Parte 1 (conceptual):** qué es cada cosa, por qué existe, cómo se relacionan. Sin código.
> - **Parte 2 (técnica simplificada):** un tour por el código en español llano, con snippets cortos.
>
> Lectura completa: ~2 horas. La parte 1 sola: ~30-45 min.

---

# PARTE 1 — CONCEPTUAL

## 1. ¿Qué es DocuMente, en una analogía?

Imagina que tu equipo tiene un proceso para documentar modelos actuariales. Hoy ese proceso es así:

1. Un actuario abre un Word en blanco
2. Empieza a escribir lo que se le ocurre, intentando recordar todo lo que el marco MRM exige
3. Se pierde, se olvida, los documentos quedan inconsistentes entre modelos
4. El área de Riesgos los revisa, encuentra brechas, devuelve el documento

DocuMente convierte ese proceso en una conversación guiada:

1. El actuario abre DocuMente
2. Crea un documento (o sube uno existente)
3. DocuMente le hace preguntas inteligentes, organizadas por las 28 secciones del template oficial NYL
4. Genera un borrador profesional en Word con marca SMNYL al exportar
5. Riesgos lo revisa con menos brechas porque el sistema ya identificó las críticas

**La metáfora corta:** DocuMente es como tener un copiloto de documentación. No reemplaza al humano, lo acelera y le quita la fricción.

---

## 2. ¿Qué partes tiene el sistema?

Piensa en DocuMente como **un cerebro Python con tres caras**:

```
                ┌──────────────────┐
                │   Streamlit      │  ← Cara 1 (la original)
                │   (legacy)       │     Funciona, es lo que vio MA al principio
                └────────┬─────────┘
                          ↓
                ┌──────────────────┐
                │   FastAPI        │  ← Cara 2 (nueva)
                │   (API REST)     │     Cerebro expuesto vía web — JSON in/out
                └────────┬─────────┘
                          ↓
                ┌──────────────────┐
                │   Next.js 14     │  ← Cara 3 (nueva, premium)
                │   (frontend)     │     Lo que verá un cliente corporate real
                └──────────────────┘
                          ↑
                ┌─────────────────────────────────────┐
                │   CEREBRO PYTHON (dominio)          │
                │   src/core/                          │
                │   - Modelos: Documento, Seccion…    │
                │   - Use cases: lo que el sistema HACE│
                │   - Reglas MRM (state machine)      │
                └─────────────────────────────────────┘
                          ↑
                ┌─────────────────────────────────────┐
                │   ÓRGANOS (infraestructura)         │
                │   - LLM (Anthropic Claude)          │
                │   - Lectura/escritura de Word       │
                │   - Base de datos (SQLite)          │
                │   - Almacenamiento de archivos      │
                └─────────────────────────────────────┘
```

### ¿Por qué tenemos 3 caras?

Históricamente teníamos solo Streamlit. Funciona pero tiene 3 limitaciones grandes:

1. **No se siente premium.** Streamlit es ideal para prototipos, pero las grandes empresas asocian "look Streamlit" con "demo interno", no con "producto".
2. **No tiene routing real.** Cuando navegas en Streamlit, la URL no cambia — esto rompe la expectativa de cualquier app web moderna.
3. **Re-renderiza todo en cada interacción.** Animaciones, transiciones suaves, micro-interacciones — todo eso es muy difícil en Streamlit.

Por eso construimos las **caras 2 y 3**:

- **FastAPI** convierte el cerebro Python en una API REST. Cualquier frontend en el mundo puede consumirla.
- **Next.js 14** es un frontend moderno (el mismo stack que usa Vercel, Linear, Cal.com) que se ve y se siente como un producto enterprise.

**Streamlit sigue ahí** porque queremos que la transición sea suave. Si algo falla en Next.js, puedes seguir usando Streamlit sin perder un día.

---

## 3. ¿Cuáles son las "cosas" del dominio?

El dominio (cerebro) trabaja con estos conceptos:

### Documento
Es la entidad raíz. Tiene un nombre (ej. "Value of New Business — GMM"), un estado (borrador, en revisión, aprobado, publicado, retirado), una lista de secciones y un audit trail (historial de qué pasó con él).

### Sección
Cada documento tiene secciones. Para el template NYL son 28 (organizadas en 9 capítulos: Problem Statement, Model Profile, Ancillary Documents, Methodology, Data, Implementation, Outputs & Performance, Model Governance, Ongoing Monitoring). Para Prophet son 12 (más compactas, formato tabular).

Cada sección tiene:
- Un nombre y número (ej. "4.4 Key Assumptions")
- Si es obligatoria o no
- Contenido (markdown libre)
- Estado: vacía / parcial / completa / omitida (con motivo)
- Una "intención" que describe qué debe contener
- Preguntas guía que el LLM usa para entrevistar

### Brecha
Cuando el sistema analiza el documento, detecta "brechas" — cosas que faltan o están mal. Cada brecha tiene una severidad (alta / media / baja) y una sugerencia para arreglarla.

Ejemplos de brechas:
- "La sección '4.4 Key Assumptions' está vacía y es obligatoria."
- "Faltan campos de metadata obligatorios: Nombre del modelo, Model Owner."

### Evento de auditoría
Cualquier acción importante queda registrada en el audit trail del documento: quién la hizo, cuándo, qué tipo (creado, editado, exportado, firmado, archivado, etc.) y una descripción.

Esto es **obligatorio para MRM** — el regulador interno necesita trazabilidad completa.

### Versión (snapshot)
Cuando el usuario quiere "congelar" el estado del documento en un punto del tiempo, crea una versión. Es un snapshot inmutable que no se puede editar después.

### Apéndice
Archivos que viven junto al documento: tablas de Excel, PDFs, fórmulas LaTeX. Se embeben en el .docx final al exportar.

### Estado de entrevista
Cuando el usuario está chateando con Claude para llenar una sección, ese chat tiene un estado: mensajes intercambiados, si la sección quedó cerrada, etc.

---

## 4. ¿Qué "hace" el sistema? (los use cases)

Use cases son las acciones que el sistema sabe ejecutar. Los más importantes:

| Use case | Qué hace | Quién lo dispara |
|---|---|---|
| **CrearDocumentoEnBlanco** | Crea un documento nuevo con las secciones vacías del template | El usuario al hacer "Crear nuevo" |
| **ImportarDocumento** | Toma un .docx o .pdf existente, lo parsea, lo mapea contra el template, detecta brechas | El usuario al subir un archivo |
| **GapAnalyzer** | Revisa un documento y devuelve la lista de brechas | Cualquier pantalla que muestre el estado |
| **IniciarEntrevista** | Arranca una conversación con Claude para llenar una sección específica | El usuario al hacer "Entrevistar" |
| **ResponderPregunta** | Procesa el turno del usuario en una entrevista en curso | Cada vez que el usuario manda un mensaje |
| **ExportarDocumento** | Toma el documento, lo renderea contra la plantilla Word maestra de SMNYL y devuelve los bytes del .docx | El usuario al hacer "Exportar DOCX" |
| **CambiarEstadoDocumento** | Mueve el documento de borrador a en-revisión, de en-revisión a aprobado, etc. | El usuario al hacer click en "Pasar a En Revisión" |
| **RegistrarSignoff** | El reviewer o el FAE firma el documento | El usuario en gobernanza |
| **CrearVersion** | Snapshot inmutable del documento | El usuario al exportar con toggle activo |
| **DocumentPolisher** | Claude revisa el documento completo y reporta inconsistencias | El usuario opcionalmente antes de exportar |
| **AdjuntarTablaApendice / Pdf / Formula** | Suben archivos auxiliares que se embeben en el .docx final | El usuario en la sección de apéndices |

**Nota importante:** estos use cases viven en `src/core/usecases/`. **No saben** si los llamó Streamlit, FastAPI o un script CLI. Son puros — reciben argumentos y devuelven resultados.

---

## 5. ¿Cómo se conectan las piezas?

Hay un principio arquitectónico estricto:

```
PRESENTACIÓN  →  APLICACIÓN  →  DOMINIO
       ↓             ↓              ↑
   INFRAESTRUCTURA  ←──────────────┘
```

Traducido en lenguaje normal:

- **Presentación** (Streamlit/Next.js) llama a use cases
- **Use cases** trabajan con modelos del dominio
- **Modelos del dominio** son objetos Pydantic puros — no saben de SQL, ni de HTTP, ni de archivos
- **Infraestructura** (BD, LLM, archivos) implementa interfaces definidas en el dominio

La regla de oro: **el dominio nunca importa nada de infraestructura ni de presentación**. Si un día decidimos cambiar SQLite por PostgreSQL, o Anthropic por Bedrock, o Streamlit por Next.js — el dominio no se entera.

Esto es por lo que esta sesión 14 fue tan rápida: **el dominio nunca tuvo que cambiar**. Solo agregamos una capa nueva (FastAPI) y un frontend nuevo (Next.js) que consumen el mismo cerebro.

---

## 6. ¿Por qué la migración a Next.js + FastAPI fue tan ambiciosa?

Tres razones que están conectadas:

### Razón 1: Streamlit tiene un techo visual

Por más CSS custom que le inyectes, Streamlit siempre se nota. La estructura del DOM es rígida (data-testid hashes), las animaciones son limitadas, el routing es fake. Para SMNYL como cliente corporate, eso es un blocker.

### Razón 2: Sin API REST, no hay integraciones

Si mañana queremos:
- Mandar reportes diarios a n8n
- Una app móvil
- Un dashboard en Tableau con datos de DocuMente
- Una integración con SharePoint

…todas necesitan una API REST. Hoy con FastAPI ya está construida.

### Razón 3: Es estándar moderno

Next.js + FastAPI es el stack que el mercado espera. Si SMNYL contrata a alguien externo para mantener DocuMente, o quiere abrirlo a otros usuarios, el stack es el "default" de la industria. Esto **baja el costo de mantenimiento futuro**.

---

## 7. ¿Qué tan listo está el producto?

Al cierre de la sesión 14:

### Funcionalmente listo
- Crear, importar, editar, archivar, papelera, restaurar documentos
- 28 secciones del template NYL + 12 de Prophet
- Entrevista LLM con Claude para llenar secciones
- Brechas detectadas y agrupadas por severidad
- State machine MRM (5 estados + signoffs)
- Versiones (snapshots inmutables)
- Apéndices: Excel multi-hoja, PDF, fórmulas LaTeX
- Auditoría completa
- Export DOCX con marca SMNYL
- Vista previa
- Onboarding + brief inicial
- Dos frontends paralelos (Streamlit + Next.js) con paridad funcional

### Funcionalmente pendiente
- Demo con MA (Carmona / Cynthia / Magallanes) — bloqueado por D.1.a (template Prophet pulido)
- Go/no-go de Prophet Fase 1

### Técnicamente pendiente
- Cognito real (acordarlo con Vidal)
- Migración a EC2 (instalar servicios, configurar nginx)
- CORS restrictivo en producción (hoy está `*` para dev local)
- Tests E2E con Playwright (hoy: cero)
- Build production del frontend validado en máquina limpia

---

## 8. ¿Qué riesgos veo?

### Riesgo 1: Auth bearer token compartido
Hoy todos comparten el mismo password (`DOCUMENTE_GATE_PASSWORD`). Para piloto interno dentro de SMNYL + VPN está bien, pero si se expone públicamente sin Cognito real, es un riesgo. Mitigación: A.1.c con Vidal.

### Riesgo 2: SQLite con 2 procesos escribiendo
Streamlit y FastAPI pueden escribir simultáneamente. SQLite tolera readers concurrentes pero serializa writes. Para piloto interno está bien. En multi-user real, migrar a PostgreSQL es 1 día.

### Riesgo 3: Frontend en Node.js agrega superficie
Si servimos el frontend con `npm start` (Next.js server), agregamos un proceso Node a la EC2. Si lo servimos como estático con nginx, no hay JS server-side. Recomendación: estático para empezar.

### Riesgo 4: El Streamlit y el Next.js pueden divergir
Si en algún momento solo arreglamos un bug en uno y no en el otro, se confunde el equipo. Mitigación: definir fecha de sunset del Streamlit (sugerencia: 2-3 semanas post-go-live de Next.js).

---

# PARTE 2 — TÉCNICA SIMPLIFICADA

> A partir de aquí entra código. Si solo necesitas entender el "qué" del producto, la parte 1 fue suficiente.

## 9. Tour por el repo

Al abrir el repo en VS Code verás:

```
DocuMente/
├── app.py                    ← Si haces "streamlit run app.py", esto arranca
├── pyproject.toml            ← Define deps Python y configs de tools
├── src/                      ← Todo el código Python
├── frontend/                 ← Todo el código TypeScript de Next.js
├── tests/                    ← Pruebas automatizadas
├── docs/                     ← Documentación (esta carpeta)
├── data/                     ← BD local + archivos subidos (no se sube a git)
└── SMNYL/                    ← Materiales fuente (no se sube a git)
```

La regla de oro: **si algo está dentro de `src/core/`, no debería importar nada de `src/ui/`, `src/api/` ni `src/storage/`** (excepto Protocols/interfaces).

---

## 10. Cómo se ve un use case por dentro

Ejemplo simplificado: `CrearDocumentoEnBlanco` (en `src/core/usecases/crear_documento.py`):

```python
@dataclass
class CrearDocumentoEnBlanco:
    repo: DocumentoRepository  # ← interfaz, no implementación

    def ejecutar(self, nombre_modelo: str, model_id: str, user_id: str = "default") -> ResultadoCrearDocumento:
        # 1. Validar inputs
        if not nombre_modelo.strip():
            raise ValueError("nombre_modelo no puede estar vacío.")

        # 2. Construir el modelo (Pydantic) en memoria
        documento = Documento(
            user_id=user_id,
            metadata_modelo=MetadataModelo(nombre_modelo=nombre_modelo, model_id=model_id),
            secciones=construir_secciones_vacias(),  # ← 28 secciones del template NYL
        )

        # 3. Registrar evento de auditoría
        documento.registrar_evento(EventoAuditoria(
            actor=user_id,
            tipo="documento_creado",
            descripcion=f"Documento creado desde cero: {nombre_modelo}",
        ))

        # 4. Persistir vía el repo
        self.repo.guardar(documento)

        # 5. Devolver el resultado
        return ResultadoCrearDocumento(documento=documento, ...)
```

**Lee este patrón con calma.** Es la columna vertebral del sistema:
1. Recibe argumentos primitivos (strings, ints)
2. Valida
3. Construye o modifica objetos del dominio
4. Registra eventos de auditoría
5. Persiste vía repo
6. Devuelve resultado

Casi todos los use cases siguen esta forma. Cuando entiendes uno, los demás se leen rápido.

---

## 11. Cómo se ve un endpoint FastAPI

Ejemplo: el endpoint que el frontend Next.js llama para crear un documento (en `src/api/routers/documentos.py`):

```python
@router.post("", response_model=DocumentoDTO, status_code=201)
def crear_documento(
    payload: CrearDocumentoRequest,    # ← Pydantic valida automáticamente
    repo: DocRepoDep,                   # ← Inyectado por FastAPI
    user: CurrentUser,                  # ← Inyectado por la auth
) -> DocumentoDTO:
    actor = payload.actor or user

    # Llamada al use case del dominio
    uc = CrearDocumentoEnBlanco(repo=repo)
    resultado = uc.ejecutar(
        nombre_modelo=payload.nombre_modelo,
        model_id=payload.nombre_modelo.replace(" ", "_").lower(),
        user_id=actor,
    )

    # Convertir el modelo del dominio a un DTO para JSON response
    return DocumentoDTO.from_domain(resultado.documento)
```

**Lee este patrón con calma.** Es como todos los endpoints REST del proyecto:
1. Recibe `payload` validado por Pydantic
2. FastAPI inyecta repos y user automáticamente vía `Depends`
3. Instancia el use case con sus dependencias
4. Lo ejecuta con los datos del payload
5. Convierte el resultado a un DTO (porque el modelo del dominio podría tener campos sensibles o no serializables)
6. FastAPI serializa el DTO a JSON y lo manda al cliente

---

## 12. Cómo se ve una página de Next.js

Ejemplo simplificado: la página de crear documento (en `frontend/src/app/documentos/crear/page.tsx`):

```tsx
"use client";  // ← Le dice a Next.js que esto se ejecuta en el browser

export default function CrearDocumentoPage() {
  const router = useRouter();
  const [nombre, setNombre] = useState("");
  const [tipo, setTipo] = useState<TipoDocumento>("model_development");

  // Hook de TanStack Query que envuelve la llamada al API
  const crear = useCrearDocumento();

  function handleSubmit() {
    crear.mutate(
      { tipo, nombre_modelo: nombre },
      {
        onSuccess: (doc) => {
          toast.success(`"${doc.metadata_modelo.nombre_modelo}" creado.`);
          router.push(`/documentos/${doc.id}`);  // ← Redirige al dashboard
        },
        onError: (err) => toast.error(`No se pudo crear: ${err.message}`),
      },
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <Input value={nombre} onChange={(e) => setNombre(e.target.value)} />
      <Button type="submit" disabled={crear.isPending}>
        Crear documento
      </Button>
    </form>
  );
}
```

**Lo importante:** la página no sabe ni del backend ni del repo. Solo llama al hook `useCrearDocumento` que internamente hace `fetch(POST /documentos)`. TanStack Query se encarga de cache, invalidations, loading states, errors.

---

## 13. El flujo completo end-to-end (con código)

Cuando el usuario hace click en "Crear documento" en el frontend Next.js, pasa esto:

```
[Browser] Click handler en Button
   ↓
[frontend/src/app/documentos/crear/page.tsx]
   crear.mutate({ tipo, nombre_modelo })
   ↓
[frontend/src/lib/api/hooks.ts]
   useCrearDocumento() → documentosApi.crear(payload)
   ↓
[frontend/src/lib/api/client.ts]
   fetch("http://localhost:8001/documentos", {
     method: "POST",
     headers: { "Content-Type": "application/json", "Authorization": "Bearer ..." },
     body: JSON.stringify(payload)
   })
   ↓
[red] HTTP request al backend
   ↓
[src/api/main.py]
   FastAPI matchea la ruta → src/api/routers/documentos.py:crear_documento()
   ↓
[src/api/routers/documentos.py]
   Valida payload con Pydantic
   Llama al use case CrearDocumentoEnBlanco
   ↓
[src/core/usecases/crear_documento.py]
   ejecuta() → construye Documento Pydantic, persiste vía repo
   ↓
[src/storage/repositories.py]
   SQLAlchemy → INSERT en SQLite
   ↓
[regreso por el mismo camino]
   Documento → DocumentoDTO → JSON
   ↓
[Browser] TanStack Query recibe la respuesta
   Invalida query "documentos" → la home se refrescaría si volvieras
   toast.success() + router.push() al dashboard del nuevo doc
```

Cada uno de estos pasos ya está implementado. La belleza de esto es que **si necesitas cambiar cómo se persiste un documento**, solo tocas `src/storage/repositories.py`. Todo lo demás sigue funcionando.

---

## 14. ¿Cómo agrego una funcionalidad nueva?

Imagina que quieres agregar "favoritos" — marcar documentos importantes con una estrella.

**Backend (Python):**

1. **Modelo:** En `src/core/models/documento.py`, agrega `es_favorito: bool = False` al `Documento`.
2. **Use case:** En `src/core/usecases/`, crea `marcar_favorito.py` con un dataclass `MarcarFavorito` que tenga método `ejecutar(doc_id, es_favorito)`.
3. **Schema API:** En `src/api/schemas/documento.py`, agrega `es_favorito: bool` al `DocumentoListItem` y `DocumentoDTO`.
4. **Router:** En `src/api/routers/documentos.py`, agrega `@router.post("/{id}/favorito")` que llama al use case.
5. **Tests:** En `tests/unit/`, escribe tests del use case. En `tests/integration/test_api_smoke.py`, agrega test del endpoint.

**Frontend (Next.js):**

6. **Tipos:** En `frontend/src/lib/api/types.ts`, agrega `es_favorito: boolean` a `DocumentoListItem`.
7. **Cliente:** En `frontend/src/lib/api/client.ts`, agrega `documentosApi.marcarFavorito(id, es_favorito)`.
8. **Hook:** En `frontend/src/lib/api/hooks.ts`, agrega `useMarcarFavorito()` con invalidations.
9. **UI:** En `frontend/src/components/home/document-card.tsx`, agrega un botón estrella que llame al hook.

Es laborioso, pero cada paso es mecánico. Y los tests del paso 5 garantizan que el contrato API → frontend no se rompe.

---

## 15. Comandos que vas a usar todos los días

```bash
# Arrancar todo localmente (3 terminales)
streamlit run app.py --server.port 8052           # Terminal 1
uvicorn src.api.main:app --reload --port 8001     # Terminal 2
cd frontend && npm run dev                         # Terminal 3

# Tests
pytest                                             # Backend completo
cd frontend && npm run lint                        # Frontend lint
cd frontend && ./node_modules/.bin/tsc --noEmit    # Frontend type check

# Git workflow típico
git status                                         # Ver qué cambió
git diff                                            # Ver el contenido del cambio
git add <archivo>                                   # Stagear
git commit -m "mensaje"                             # Commitear
git log --oneline -10                               # Historial reciente

# Cuando termines algo grande
git push                                            # Subir a GitHub
```

---

## 16. Si te atoras

### Error frecuente 1: "ANTHROPIC_API_KEY not found"

Causa: el `.env` no existe en el directorio donde corres el comando.

```bash
ls .env   # ¿Existe?
# Si no:
cp /c/Users/alber/Claude_AI/proyectos/DocuMente/.env .env
```

### Error frecuente 2: "Port 8001 already in use"

Causa: ya hay otro proceso usando ese puerto. Usa otro:

```bash
uvicorn src.api.main:app --reload --port 8002
```

Y actualiza `NEXT_PUBLIC_API_URL` en `frontend/.env.local` para que el frontend apunte al puerto nuevo.

### Error frecuente 3: "Module not found"

Causa: dependencia faltante.

```bash
# Backend:
pip install -e ".[dev]"

# Frontend:
cd frontend && npm install
```

### Error frecuente 4: Cambio el código, refresh el browser, no veo el cambio

Posibles causas:

1. **Streamlit:** click en "Always rerun" (arriba a la derecha de la app) — sino solo recarga al cambiar archivo
2. **Next.js dev:** debería recargar solo. Si no, hard refresh con `Ctrl+Shift+R`
3. **API:** asegúrate que `uvicorn --reload` está activo

### Error frecuente 5: "git push rejected"

Causa: el branch remoto tiene commits que no tienes localmente.

```bash
git pull --rebase   # Trae los cambios remotos y reaplica los tuyos encima
git push            # Vuelve a intentar
```

---

## 17. Glosario rápido

| Término | Significa |
|---|---|
| **MRM** | Model Risk Management — marco regulatorio interno de SMNYL para gobierno de modelos |
| **FAE** | Functional Area Executive — rol senior que firma la aprobación de un modelo |
| **Reviewer** | Rol que valida el documento antes del FAE |
| **Tier de riesgo** | Clasificación de un modelo según su impacto (low, medium, high, very_high, critical) |
| **Prophet** | Software de modelos actuariales que usa SMNYL — origen de las fichas técnicas |
| **Use case** | Acción que el sistema sabe ejecutar (Crear, Importar, Exportar, etc.) |
| **DTO** | Data Transfer Object — Pydantic schema usado solo para serializar JSON, separado del modelo del dominio |
| **Repository** | Patrón que abstrae el acceso a la BD — la lógica no sabe si es SQLite o PostgreSQL |
| **Protocol** | Interface de Python (`typing.Protocol`) — define qué métodos debe tener una clase sin forzar herencia |
| **TanStack Query** | Librería de React para manejar server state (cache, refetch, invalidations) |
| **shadcn/ui** | Sistema de componentes UI copy-paste (no es una librería npm), basados en Radix UI + Tailwind |
| **Bearer token** | Esquema de auth donde el cliente manda `Authorization: Bearer <token>` en cada request |
| **CORS** | Mecanismo del browser que controla qué dominios pueden llamar a tu API |
| **App Router** | Routing system nuevo de Next.js 14 (vs Pages Router viejo) |
| **RSC** | React Server Components — componentes que renderizan en el server, no en el browser |

---

## 18. Cierre

Si entendiste hasta aquí, sabes:

1. **Qué hace DocuMente** y por qué existe
2. **Cómo está organizado** (3 caras + 1 cerebro + órganos)
3. **Qué conceptos del dominio existen** (Documento, Sección, Brecha, etc.)
4. **Cómo agregar funcionalidad nueva** sin romper la arquitectura
5. **Qué comandos usar** para arrancar y depurar
6. **Dónde están los riesgos** y cómo se mitigan

Para profundizar:
- `docs/ARQUITECTURA.md` — la versión técnica formal de esto
- `docs/HANDOFF_VIDAL.md` — el cambio main → branch explicado para Vidal
- `docs/MIGRATION_TO_EC2.md` — qué hace falta para desplegar en producción
- `docs/MRM_REQUIREMENTS.md` — qué exige el marco regulatorio interno

Si en algún momento te abruma la cantidad de código, recuerda: la regla de oro es **el dominio no sabe nada del mundo exterior**. Si te concentras en entender `src/core/`, lo demás es plumbing.
