/**
 * DashboardHero — header compacto del documento: nombre + estado pill +
 * meta (secciones, eventos) + acciones (Editar metadata, Exportar DOCX).
 *
 * Replica el patrón premium T1 implementado en Streamlit (dashboard.py).
 */
"use client";

import Link from "next/link";
import { ArrowLeft, Edit, Download } from "lucide-react";
import { toast } from "sonner";

import type { Documento } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { exportarApi } from "@/lib/api/client";

const ESTADO_VARIANT: Record<
  Documento["estado"],
  "draft" | "review" | "approved" | "published" | "secondary"
> = {
  draft: "draft",
  in_review: "review",
  approved: "approved",
  published: "published",
  retired: "secondary",
};

const ESTADO_LABEL: Record<Documento["estado"], string> = {
  draft: "Borrador",
  in_review: "En revisión",
  approved: "Aprobado",
  published: "Publicado",
  retired: "Retirado",
};

interface DashboardHeroProps {
  documento: Documento;
}

export function DashboardHero({ documento }: DashboardHeroProps) {
  const nombre = documento.metadata_modelo.nombre_modelo || "Documento sin nombre";

  async function handleExportar() {
    const toastId = toast.loading("Generando DOCX con marca SMNYL…");
    try {
      const blob = await exportarApi.docx(documento.id, {
        idioma_objetivo: "bilingue",
        crear_version: false,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${nombre.replace(/\s+/g, "_")}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success("DOCX descargado", { id: toastId });
    } catch (err) {
      toast.error(`Error al exportar: ${(err as Error).message}`, { id: toastId });
    }
  }

  return (
    <div className="animate-fade-in">
      <div className="mb-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/">
            <ArrowLeft className="mr-1 h-3.5 w-3.5" />
            Volver a Inicio
          </Link>
        </Button>
      </div>

      <div className="flex items-start justify-between gap-6 flex-wrap">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3 mb-1.5 flex-wrap">
            <h1 className="font-display text-3xl font-semibold text-smnyl-text leading-tight">
              {nombre}
            </h1>
            <Badge variant={ESTADO_VARIANT[documento.estado]}>
              {ESTADO_LABEL[documento.estado]}
            </Badge>
          </div>
          <p className="text-sm text-smnyl-text-muted">
            {documento.secciones.length} secciones del template
            <span className="mx-2">·</span>
            {documento.n_eventos_audit} evento{documento.n_eventos_audit === 1 ? "" : "s"} en
            audit trail
            <span className="mx-2">·</span>
            {documento.tipo === "prophet" ? "Ficha Prophet" : "Model Development"}
          </p>
        </div>

        <div className="flex gap-2 shrink-0">
          <Button variant="outline" size="default" asChild>
            <Link href={`/documentos/${documento.id}/metadata`}>
              <Edit className="mr-1 h-4 w-4" />
              Editar metadata
            </Link>
          </Button>
          <Button size="default" onClick={handleExportar}>
            <Download className="mr-1 h-4 w-4" />
            Exportar DOCX
          </Button>
        </div>
      </div>
    </div>
  );
}
