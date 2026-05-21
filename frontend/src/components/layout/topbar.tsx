/**
 * Topbar premium — breadcrumbs a la izquierda, acciones globales a la derecha.
 *
 * Por ahora estático; en iteraciones futuras el breadcrumb se sincroniza
 * con la ruta y los handlers de "Notificaciones / User menu" se cablean.
 */
"use client";

import Link from "next/link";
import { Search, Bell, User } from "lucide-react";

import { Button } from "@/components/ui/button";

interface TopbarProps {
  breadcrumbs?: { label: string; href?: string }[];
}

export function Topbar({ breadcrumbs }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-smnyl-border bg-white/80 backdrop-blur-md px-6">
      <nav className="flex-1">
        <ol className="flex items-center gap-2 text-sm">
          {(breadcrumbs ?? [{ label: "Inicio", href: "/" }]).map((bc, i, arr) => (
            <li key={`${bc.label}-${i}`} className="flex items-center gap-2">
              {bc.href && i < arr.length - 1 ? (
                <Link
                  href={bc.href}
                  className="text-smnyl-text-muted hover:text-smnyl-primary transition-colors"
                >
                  {bc.label}
                </Link>
              ) : (
                <span className="font-medium text-smnyl-text">{bc.label}</span>
              )}
              {i < arr.length - 1 && (
                <span className="text-smnyl-text-muted">/</span>
              )}
            </li>
          ))}
        </ol>
      </nav>

      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" aria-label="Buscar">
          <Search className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Notificaciones">
          <Bell className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Perfil">
          <User className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
