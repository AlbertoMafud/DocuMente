/**
 * Dashboard de un documento — hero + métricas + brechas + secciones.
 *
 * El render se hace en cliente para aprovechar TanStack Query +
 * invalidations en mutations (archivar, omitir, etc.).
 */
"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useBrechas, useDocumento } from "@/lib/api/hooks";
import { DashboardHero } from "@/components/dashboard/dashboard-hero";
import { MetricsRow } from "@/components/dashboard/metrics-row";
import { BrechasAccordion } from "@/components/dashboard/brechas-accordion";
import { SeccionesAccordion } from "@/components/dashboard/secciones-accordion";

export default function DashboardPage() {
  const { id } = useParams<{ id: string }>();
  const docQuery = useDocumento(id);
  const brechasQuery = useBrechas(id);

  if (docQuery.isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-16 w-full max-w-xl" />
        <div className="grid grid-cols-5 gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (docQuery.error || !docQuery.data) {
    return (
      <div className="rounded-lg border border-smnyl-danger/40 bg-smnyl-danger-soft p-8 text-center max-w-xl mx-auto">
        <AlertCircle className="mx-auto h-10 w-10 text-smnyl-danger mb-3" />
        <h2 className="font-display text-lg font-semibold text-smnyl-danger mb-2">
          No se pudo cargar el documento
        </h2>
        <p className="text-sm text-smnyl-text-muted mb-4">
          {(docQuery.error as Error)?.message ?? "El documento puede haber sido eliminado."}
        </p>
        <Button asChild>
          <Link href="/">Volver a Inicio</Link>
        </Button>
      </div>
    );
  }

  const brechas = brechasQuery.data ?? [];

  return (
    <div className="space-y-8">
      <DashboardHero documento={docQuery.data} />
      <MetricsRow documento={docQuery.data} brechas={brechas} />
      <BrechasAccordion brechas={brechas} />
      <SeccionesAccordion documento={docQuery.data} brechas={brechas} />
    </div>
  );
}
