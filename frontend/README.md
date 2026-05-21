# DocuMente — Frontend (Next.js 14)

Frontend premium para DocuMente, consume la API REST en `src/api/`.

## Stack

- **Next.js 14** App Router + TypeScript estricto
- **Tailwind CSS** con tokens SMNYL (espejo de `src/ui/theme.py`)
- **shadcn/ui** componentes primitivos (Button, Card, Badge, Tabs, Progress, …)
- **TanStack Query** para server state + cache + invalidations
- **Lucide React** para iconografía consistente
- **Sonner** para toasts premium con acción "Deshacer"
- **Framer Motion** disponible (animaciones futuras)

## Arquitectura

```
frontend/
├── src/
│   ├── app/                  Rutas (App Router)
│   │   ├── layout.tsx        Root layout con sidebar + topbar
│   │   ├── page.tsx          Home (lista de documentos)
│   │   └── globals.css       Tokens HSL para shadcn + SMNYL base styles
│   ├── components/
│   │   ├── ui/               shadcn primitivos (button, card, badge, tabs, …)
│   │   ├── layout/           sidebar.tsx, topbar.tsx
│   │   ├── home/             continue-hero, welcome-hero, document-card, document-list
│   │   └── providers.tsx     QueryClient + Toaster
│   └── lib/
│       ├── utils.ts          cn() + tiempoRelativo()
│       └── api/
│           ├── types.ts      Espejo manual de DTOs en src/api/schemas/
│           ├── client.ts     Wrapper fetch tipado contra FastAPI
│           └── hooks.ts      TanStack Query hooks por endpoint
├── tailwind.config.ts        Tokens SMNYL (colors.smnyl.*) + shadcn HSL vars
├── components.json           shadcn config
└── package.json
```

## Comandos

```bash
# Setup inicial (una sola vez)
npm install

# Dev server — abre http://localhost:3000 (o el siguiente libre)
npm run dev

# Type check
npx tsc --noEmit

# Lint
npm run lint

# Build production
npm run build
npm start
```

## Variables de entorno

Copia `.env.local.example` a `.env.local` y ajusta:

- `NEXT_PUBLIC_API_URL` — URL del backend FastAPI (default `http://localhost:8001`)
- `NEXT_PUBLIC_API_TOKEN` — bearer token, solo si la API tiene `DOCUMENTE_GATE_PASSWORD` activo

## Convivencia con Streamlit

Mientras F3-F4 migran páginas, el Streamlit original sigue corriendo en `:8052`
contra la misma BD. Ambos frontends consumen los mismos use cases — el de
Streamlit directamente desde Python, el de Next.js vía la API REST.

## Sincronización con el dominio

Los tipos en `src/lib/api/types.ts` son espejo manual de los Pydantic DTOs en
`src/api/schemas/`. Cuando un schema cambie en Python:
1. Actualiza el TypeScript correspondiente
2. Corre `npm run lint` y `npx tsc --noEmit`
3. Los smoke tests Python (`tests/integration/test_api_smoke.py`) validan el contrato del lado servidor

Versiones futuras autogenerarán estos tipos desde `/openapi.json` con
`openapi-typescript` — está pendiente como improvement no-bloqueante.
