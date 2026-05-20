/**
 * Versiones del documento — snapshots inmutables.
 *
 * Lista vN..v1 (desc) + botón "Crear versión ahora" con comentario opcional.
 * Las versiones son idempotentes: si el hash de contenido es igual al de la
 * última, se reutiliza en lugar de duplicar.
 */
"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, GitBranch, Loader2, Plus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useCrearVersion, useDocumento, useVersiones } from "@/lib/api/hooks";
import { tiempoRelativo } from "@/lib/utils";

export default function VersionesPage() {
  const { id } = useParams<{ id: string }>();
  const docQuery = useDocumento(id);
  const versionesQuery = useVersiones(id);
  const crearVersion = useCrearVersion();
  const [comentario, setComentario] = useState("");
  const [creando, setCreando] = useState(false);

  function handleCrear() {
    crearVersion.mutate(
      { docId: id, comentario },
      {
        onSuccess: (v) => {
          toast.success(`Versión v${v.numero} creada.`);
          setComentario("");
          setCreando(false);
        },
        onError: (err) => toast.error(`Error: ${(err as Error).message}`),
      },
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <Button variant="ghost" size="sm" asChild>
        <Link href={`/documentos/${id}`}>
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Volver al dashboard
        </Link>
      </Button>

      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-primary/10 text-smnyl-primary mb-3">
            <GitBranch className="h-5 w-5" />
          </div>
          <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-2">
            Versiones
          </h1>
          <p className="text-sm text-smnyl-text-muted max-w-2xl">
            Snapshots inmutables de{" "}
            <span className="font-medium text-smnyl-text">
              {docQuery.data?.metadata_modelo.nombre_modelo ?? "este documento"}
            </span>
            . Cada versión captura el estado completo y es restaurable.
          </p>
        </div>
        {!creando && (
          <Button onClick={() => setCreando(true)}>
            <Plus className="mr-1 h-4 w-4" />
            Crear versión ahora
          </Button>
        )}
      </div>

      {creando && (
        <Card className="p-5 animate-fade-in">
          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="comentario">Comentario (opcional)</Label>
              <Input
                id="comentario"
                placeholder="Ej. Cierre Q2 — supuestos actualizados"
                value={comentario}
                onChange={(e) => setComentario(e.target.value)}
                autoFocus
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCrear} disabled={crearVersion.isPending}>
                {crearVersion.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Crear snapshot
              </Button>
              <Button variant="ghost" onClick={() => setCreando(false)}>
                Cancelar
              </Button>
            </div>
          </div>
        </Card>
      )}

      {versionesQuery.isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : versionesQuery.data && versionesQuery.data.length > 0 ? (
        <div className="space-y-2">
          {[...versionesQuery.data].reverse().map((v) => (
            <Card key={v.id} className="p-4 smnyl-card-hover">
              <div className="flex items-start gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-accent-soft/40 text-smnyl-primary shrink-0">
                  <span className="font-display text-sm font-bold">v{v.numero}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-smnyl-text">
                    {v.comentario || "Sin comentario"}
                  </p>
                  <p className="text-xs text-smnyl-text-muted mt-0.5">
                    Creada {tiempoRelativo(v.creado_en)} ·{" "}
                    <code className="bg-smnyl-bg-soft px-1.5 py-0.5 rounded text-[0.7rem]">
                      {v.hash_contenido.slice(0, 8)}
                    </code>
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-smnyl-border bg-smnyl-bg-soft/40 px-6 py-12 text-center">
          <GitBranch className="h-10 w-10 text-smnyl-text-muted/60 mx-auto mb-3" />
          <h3 className="font-display text-lg font-semibold text-smnyl-text mb-1">
            Sin versiones todavía
          </h3>
          <p className="text-sm text-smnyl-text-muted max-w-md mx-auto">
            Las versiones se crean automáticamente al exportar con la opción
            &quot;Crear nueva versión&quot;, o manualmente desde aquí.
          </p>
        </div>
      )}
    </div>
  );
}
