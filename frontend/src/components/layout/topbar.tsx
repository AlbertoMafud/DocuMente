/**
 * Topbar premium — hamburguesa móvil + breadcrumb dinámico derivado de la ruta.
 *
 * El breadcrumb se construye desde usePathname(); para rutas de documento
 * usa useDocumento (enabled: !!id), que comparte cache de TanStack Query con
 * el dashboard — en navegación normal el nombre ya está cacheado y no hay
 * fetch extra. Las acciones globales (búsqueda, notificaciones, perfil) se
 * agregarán cuando existan de verdad — sin botones muertos (P0-6).
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useDocumento } from "@/lib/api/hooks";
import { MobileNav } from "@/components/layout/mobile-nav";

interface Crumb {
  label: string;
  href?: string;
}

// Rutas de primer nivel.
const TOP_LABELS: Record<string, string> = {
  importar: "Importar",
  prophet: "Ficha Prophet",
  configuracion: "Configuración",
  ayuda: "Ayuda",
};

// Sub-rutas dentro de /documentos/[id]/.
const DOC_SUB_LABELS: Record<string, string> = {
  entrevista: "Entrevista",
  metadata: "Metadata",
  auditoria: "Auditoría",
  "vista-previa": "Vista previa",
  versiones: "Versiones",
  apendices: "Apéndices",
  onboarding: "Onboarding",
  brief: "Brief inicial",
  secciones: "Editar sección",
};

function useBreadcrumbs(): Crumb[] {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  const esDoc =
    segments[0] === "documentos" && !!segments[1] && segments[1] !== "crear";
  const docId = esDoc ? segments[1] : "";
  const { data: doc } = useDocumento(docId);

  const crumbs: Crumb[] = [{ label: "Inicio", href: "/" }];

  if (segments.length === 0) return crumbs;

  if (segments[0] === "documentos") {
    if (segments[1] === "crear") {
      crumbs.push({ label: "Crear documento" });
      return crumbs;
    }
    const nombreDoc = doc?.metadata_modelo?.nombre_modelo || "Documento";
    const sub = segments[2] ? DOC_SUB_LABELS[segments[2]] : undefined;
    if (sub) {
      crumbs.push({ label: nombreDoc, href: `/documentos/${docId}` });
      crumbs.push({ label: sub });
    } else {
      crumbs.push({ label: nombreDoc });
    }
    return crumbs;
  }

  const top = TOP_LABELS[segments[0]];
  if (top) crumbs.push({ label: top });
  return crumbs;
}

export function Topbar() {
  const crumbs = useBreadcrumbs();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-2 border-b border-smnyl-border bg-white/80 backdrop-blur-md px-4 lg:px-6">
      <MobileNav />
      <nav className="min-w-0 flex-1" aria-label="Breadcrumb">
        <ol className="flex items-center gap-2 text-sm">
          {crumbs.map((bc, i, arr) => (
            <li key={`${bc.label}-${i}`} className="flex min-w-0 items-center gap-2">
              {bc.href && i < arr.length - 1 ? (
                <Link
                  href={bc.href}
                  className="truncate text-smnyl-text-muted hover:text-smnyl-primary transition-colors"
                >
                  {bc.label}
                </Link>
              ) : (
                <span
                  className="truncate font-medium text-smnyl-text"
                  aria-current={i === arr.length - 1 ? "page" : undefined}
                >
                  {bc.label}
                </span>
              )}
              {i < arr.length - 1 && <span className="text-smnyl-text-muted">/</span>}
            </li>
          ))}
        </ol>
      </nav>
    </header>
  );
}
