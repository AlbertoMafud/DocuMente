/**
 * Auditoría completa del documento — timeline vertical de todos los eventos.
 */
"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ClipboardList } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuditoria, useDocumento } from "@/lib/api/hooks";
import { Timeline } from "@/components/auditoria/timeline";

export default function AuditoriaPage() {
  const { id } = useParams<{ id: string }>();
  const docQuery = useDocumento(id);
  const auditQuery = useAuditoria(id);

  return (
    <div className="space-y-6 max-w-4xl">
      <Button variant="ghost" size="sm" asChild>
        <Link href={`/documentos/${id}`}>
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Volver al dashboard
        </Link>
      </Button>

      <div>
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-primary/10 text-smnyl-primary mb-3">
          <ClipboardList className="h-5 w-5" />
        </div>
        <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-2">
          Auditoría
        </h1>
        <p className="text-sm text-smnyl-text-muted">
          Audit trail completo de{" "}
          <span className="font-medium text-smnyl-text">
            {docQuery.data?.metadata_modelo.nombre_modelo || "este documento"}
          </span>{" "}
          — cumple MRM §3.5 (trazabilidad de cambios).
        </p>
      </div>

      {auditQuery.isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : (
        <Timeline eventos={auditQuery.data ?? []} />
      )}
    </div>
  );
}
