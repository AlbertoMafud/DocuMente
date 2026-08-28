/**
 * MobileNav — navegación para viewports <1024px, donde el sidebar fijo
 * está oculto (`hidden lg:flex`). Hamburguesa en el topbar que abre un
 * drawer lateral con exactamente la misma nav del sidebar (P0-3 de la
 * auditoría visual: sin esto, Importar/Crear/Prophet/Configuración/Ayuda
 * son inalcanzables en tablet y móvil).
 */
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { BrandLogo } from "@/components/layout/brand-logo";
import {
  APIStatus,
  NAV_PRIMARY,
  NAV_SECONDARY,
  SidebarItem,
} from "@/components/layout/sidebar";

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  // Navegar cierra el drawer; Escape también.
  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <div className="lg:hidden">
      <Button
        variant="ghost"
        size="icon"
        aria-label="Abrir navegación"
        aria-expanded={open}
        onClick={() => setOpen(true)}
      >
        <Menu className="h-5 w-5" />
      </Button>

      {open && (
        <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Navegación">
          <button
            type="button"
            aria-label="Cerrar navegación"
            className="absolute inset-0 bg-smnyl-text/40 backdrop-blur-[2px]"
            onClick={() => setOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col bg-white shadow-smnyl-lg animate-fade-in">
            <div className="flex h-16 items-center justify-between border-b border-smnyl-border pl-5 pr-3">
              <Link href="/" className="flex items-center gap-3">
                <BrandLogo size={32} />
                <span className="font-display text-sm font-bold text-smnyl-text">
                  DocuMente
                </span>
              </Link>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Cerrar navegación"
                onClick={() => setOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
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
          </div>
        </div>
      )}
    </div>
  );
}
