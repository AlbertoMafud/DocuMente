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
  Upload,
  ClipboardList,
  Sparkles,
  Settings,
  HelpCircle,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { BrandLogo } from "@/components/layout/brand-logo";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const NAV_PRIMARY: NavItem[] = [
  { label: "Inicio", href: "/", icon: Home },
  { label: "Documentos", href: "/documentos", icon: FileText },
  { label: "Importar", href: "/importar", icon: Upload },
  { label: "Auditoría", href: "/auditoria", icon: ClipboardList },
  { label: "Ficha Prophet", href: "/prophet", icon: Sparkles, badge: "Beta" },
];

const NAV_SECONDARY: NavItem[] = [
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

function SidebarItem({ item, active }: { item: NavItem; active: boolean }) {
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

function APIStatus() {
  // Simple status — el sidebar se rerendera cuando cambie el flag global de
  // conexión. Por ahora hardcoded "Conectado".
  return (
    <div className="flex items-center gap-2 text-[0.7rem] text-smnyl-text-muted">
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-smnyl-success/60 opacity-50" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-smnyl-success" />
      </span>
      <span>API conectada</span>
    </div>
  );
}
