/**
 * DocumentCard — fila compacta de un documento en la lista del home.
 *
 * Acciones contextuales según el modo:
 * - activos: Abrir + Archivar + Papelera
 * - archivados: Desarchivar
 * - papelera: Restaurar + indicador de días restantes
 */
"use client";

import Link from "next/link";
import { Archive, Trash2, ArchiveRestore, Undo2 } from "lucide-react";
import { toast } from "sonner";

import type { DocumentoListItem } from "@/lib/api/types";
import { tiempoRelativo } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  useArchivar,
  useDesarchivar,
  useEnviarAPapelera,
  useRestaurar,
} from "@/lib/api/hooks";

interface DocumentCardProps {
  doc: DocumentoListItem;
  modo: "activos" | "archivados" | "papelera";
}

const ESTADO_VARIANT: Record<DocumentoListItem["estado"],
  "draft" | "review" | "approved" | "published" | "secondary"
> = {
  draft: "draft",
  in_review: "review",
  approved: "approved",
  published: "published",
  retired: "secondary",
};

const ESTADO_LABEL: Record<DocumentoListItem["estado"], string> = {
  draft: "Borrador",
  in_review: "En revisión",
  approved: "Aprobado",
  published: "Publicado",
  retired: "Retirado",
};

export function DocumentCard({ doc, modo }: DocumentCardProps) {
  const archivar = useArchivar();
  const desarchivar = useDesarchivar();
  const papelera = useEnviarAPapelera();
  const restaurar = useRestaurar();

  const nombre = doc.nombre_modelo || "Documento sin nombre";
  const pct = Math.round(doc.porcentaje_completitud * 100);

  return (
    <Card className="p-4 smnyl-card-hover">
      <div className="flex items-start gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2.5 mb-1">
            <Link
              href={`/documentos/${doc.id}`}
              className="font-medium text-smnyl-text hover:text-smnyl-primary truncate transition-colors"
            >
              {nombre}
            </Link>
            <Badge variant={ESTADO_VARIANT[doc.estado]}>
              {ESTADO_LABEL[doc.estado]}
            </Badge>
          </div>
          <div className="text-xs text-smnyl-text-muted">
            {pct}% completitud · {doc.n_secciones} secciones · actualizado{" "}
            {tiempoRelativo(doc.actualizado_en)}
          </div>
        </div>

        <div className="flex gap-1 shrink-0">
          {modo === "activos" && (
            <>
              <Button variant="outline" size="sm" asChild>
                <Link href={`/documentos/${doc.id}`}>Abrir</Link>
              </Button>
              <Button
                variant="ghost"
                size="icon"
                title="Archivar"
                onClick={() =>
                  archivar.mutate(
                    { id: doc.id },
                    {
                      onSuccess: () =>
                        toast.success(`"${nombre}" archivado`, {
                          action: {
                            label: "Deshacer",
                            onClick: () => desarchivar.mutate(doc.id),
                          },
                        }),
                    },
                  )
                }
              >
                <Archive className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                title="Mover a papelera"
                onClick={() =>
                  papelera.mutate(
                    { id: doc.id },
                    {
                      onSuccess: () =>
                        toast.success(`"${nombre}" movido a papelera`, {
                          action: {
                            label: "Deshacer",
                            onClick: () => restaurar.mutate(doc.id),
                          },
                        }),
                    },
                  )
                }
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </>
          )}
          {modo === "archivados" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                desarchivar.mutate(doc.id, {
                  onSuccess: () => toast.success(`"${nombre}" desarchivado`),
                })
              }
            >
              <ArchiveRestore className="mr-1 h-3.5 w-3.5" />
              Desarchivar
            </Button>
          )}
          {modo === "papelera" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                restaurar.mutate(doc.id, {
                  onSuccess: () => toast.success(`"${nombre}" restaurado`),
                })
              }
            >
              <Undo2 className="mr-1 h-3.5 w-3.5" />
              Restaurar
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
