/**
 * ErrorState — estado de error estándar con CTA de recuperación.
 *
 * Clona el patrón de referencia del dashboard (documentos/[id]/page.tsx):
 * card danger-soft + icono + mensaje claro en español + acciones. Unifica
 * los errores crudos sin CTA y los errores enmascarados como estado vacío
 * (auditoría S19, hallazgos P1-12 y P1-13).
 */
"use client";

import Link from "next/link";
import { AlertCircle, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  /** Título corto del problema, en español y sin jerga técnica. */
  titulo?: string;
  /** Detalle opcional (p. ej. el message del error de la API). */
  detalle?: string;
  /** Reintenta la carga (normalmente `() => query.refetch()`). */
  onRetry?: () => void;
  /** True mientras el reintento está en curso. */
  retrying?: boolean;
  /** Destino del link de escape. */
  volverHref?: string;
  volverLabel?: string;
  className?: string;
}

export function ErrorState({
  titulo = "No se pudo cargar la información",
  detalle,
  onRetry,
  retrying = false,
  volverHref = "/",
  volverLabel = "Volver a Inicio",
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "rounded-lg border border-smnyl-danger/40 bg-smnyl-danger-soft p-8 text-center",
        "max-w-xl mx-auto animate-fade-in",
        className,
      )}
    >
      <AlertCircle className="mx-auto h-10 w-10 text-smnyl-danger mb-3" aria-hidden="true" />
      <h2 className="font-display text-lg font-semibold text-smnyl-danger mb-2">
        {titulo}
      </h2>
      <p className="text-sm text-smnyl-text-muted mb-4">
        {detalle || "Verifica tu conexión con la API e inténtalo de nuevo."}
      </p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        {onRetry && (
          <Button onClick={onRetry} disabled={retrying}>
            <RotateCcw className={cn("mr-1 h-4 w-4", retrying && "animate-spin")} />
            Reintentar
          </Button>
        )}
        <Button variant={onRetry ? "ghost" : "default"} asChild>
          <Link href={volverHref}>{volverLabel}</Link>
        </Button>
      </div>
    </div>
  );
}
