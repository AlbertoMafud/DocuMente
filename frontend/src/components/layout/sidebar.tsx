/**
 * Sidebar premium — logo SMNYL + navegación principal + indicador de
 * conexión a la API.
 *
 * 240px fijo a la izquierda en desktop, sin colapso por ahora. La nav
 * usa Next/Link con highlight de la ruta activa.
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  FileText,
  Layers,
  Upload,
  Sparkles,
  Settings,
  HelpCircle,
} from "lucide-react";

import { useQuery } from "@tanstack/react-query";

import { cn } from "@/lib/utils";
import { healthApi } from "@/lib/api/client";
import { BrandLogo } from "@/components/layout/brand-logo";

export interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

// Exportados para que MobileNav (drawer <1024px) use exactamente la misma nav.
export const NAV_PRIMARY: NavItem[] = [
  // "Inicio" lista todos los documentos — no duplicamos con "/documentos"
  // "Auditoría" es contextual a un documento (vive en /documentos/[id]/auditoria),
  // no tiene sentido como item global del sidebar
  { label: "Inicio", href: "/", icon: Home },
  { label: "Importar", href: "/importar", icon: Upload },
  { label: "Crear nuevo", href: "/documentos/crear", icon: FileText },
  { label: "Ficha Prophet", href: "/prophet", icon: Sparkles, badge: "Beta" },
  { label: "Template Studio", href: "/studio", icon: Layers, badge: "Nuevo" },
];

export const NAV_SECONDARY: NavItem[] = [
  { label: "Configuración", href: "/configuracion", icon: Settings },
  { label: "Ayuda", href: "/ayuda", icon: HelpCircle },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-60 shrink-0 flex-col border-r border-smnyl-border bg-smnyl-bg-soft/30">
      <Link href="/" className="flex h-16 items-center gap-3 border-b border-smnyl-border px-5 group">
        <BrandLogo size={36} className="transition-transform duration-200 group-hover:scale-105" />
        <div className="leading-tight">
          <div className="font-display text-sm font-bold text-smnyl-text">DocuMente</div>
          <div className="text-[0.65rem] uppercase tracking-wider text-smnyl-text-muted">
            SMNYL
          </div>
        </div>
      </Link>

      <nav className="flex-1 space-y-0.5 px-3 py-4">
        {NAV_PRIMARY.map((item) => (
          <SidebarItem key={item.href} item={item} active={pathname === item.href} />
        ))}
      </nav>

      <div className="border-t border-smnyl-border px-3 py-3 space-y-0.5">
        {NAV_SECONDARY.map((item) => (
          <SidebarItem key={item.href} item={item} active={pathname === item.href} />
        ))}
      </div>

      <div className="border-t border-smnyl-border px-5 py-3">
        <APIStatus />
      </div>
    </aside>
  );
}

export function SidebarItem({ item, active }: { item: NavItem; active: boolean }) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      className={cn(
        "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium",
        "transition-all duration-200 ease-out",
        active
          ? "bg-smnyl-primary text-white shadow-smnyl-sm"
          : "text-smnyl-text-muted hover:bg-smnyl-bg-soft hover:text-smnyl-text",
      )}
    >
      <Icon className={cn("h-4 w-4 shrink-0", active && "text-white")} />
      <span className="flex-1 truncate">{item.label}</span>
      {item.badge && (
        <span
          className={cn(
            "rounded-full px-1.5 py-0.5 text-[0.65rem] font-semibold uppercase",
            active
              ? "bg-white/20 text-white"
              : "bg-smnyl-warning-soft text-smnyl-warning-dark",
          )}
        >
          {item.badge}
        </span>
      )}
    </Link>
  );
}

export function APIStatus() {
  // Health check real contra el backend — misma queryKey que /configuracion,
  // así comparten cache y un solo polling cada 30s alimenta a ambos.
  const health = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.ok,
    refetchInterval: 30_000,
    retry: 1,
  });

  const estado = health.isPending
    ? { dot: "bg-smnyl-text-muted", ping: false, label: "Verificando API…" }
    : health.isError
      ? { dot: "bg-smnyl-danger", ping: false, label: "API sin conexión" }
      : { dot: "bg-smnyl-success", ping: true, label: "API conectada" };

  return (
    <div
      className="flex items-center gap-2 text-[0.7rem] text-smnyl-text-muted"
      role="status"
      aria-live="polite"
    >
      <span className="relative flex h-2 w-2">
        {estado.ping && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-smnyl-success/60 opacity-50" />
        )}
        <span className={cn("relative inline-flex h-2 w-2 rounded-full", estado.dot)} />
      </span>
      <span>{estado.label}</span>
    </div>
  );
}
