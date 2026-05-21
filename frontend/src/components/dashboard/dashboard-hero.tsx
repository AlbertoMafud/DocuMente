/**
 * DashboardHero — header compacto del documento: nombre + estado pill +
 * meta (secciones, eventos) + acciones (Editar metadata, Exportar DOCX).
 *
 * El selector de idioma del export está en un DropdownMenu — soporta los
 * 5 modos del backend (bilingue, es, es_normalize, en, en_normalize).
 *
 * Replica el patrón premium T1 implementado en Streamlit (dashboard.py).
 */
"use client";

import Link from "next/link";
import { ArrowLeft, Edit, Download, ChevronDown } from "lucide-react";
import { toast } from "sonner";

import type { Documento } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { exportarApi } from "@/lib/api/client";

type IdiomaExport = "bilingue" | "es" | "es_normalize" | "en" | "en_normalize";

const IDIOMAS: { value: IdiomaExport; label: string; descripcion: string }[] = [
  {
    value: "bilingue",
    label: "Bilingüe (recomendado)",
    descripcion: "Mantiene el contenido en su idioma original",
  },
  {
    value: "es",
    label: "Español",
    descripcion: "Sin transformación LLM",
  },
  {
    value: "es_normalize",
    label: "Español — normalizar",
    descripcion: "LLM revisa redacción y consistencia",
  },
  {
    value: "en",
    label: "Inglés",
    descripcion: "Traduce todo al inglés vía LLM",
  },
  {
    value: "en_normalize",
    label: "Inglés — normalizar",
    descripcion: "Traduce + normaliza redacción",
  },
];

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

  async function handleExportar(idioma: IdiomaExport) {
    const idiomaLabel = IDIOMAS.find((i) => i.value === idioma)?.label ?? idioma;
    const toastId = toast.loading(`Generando DOCX (${idiomaLabel})…`);
    try {
      const blob = await exportarApi.docx(documento.id, {
        idioma_objetivo: idioma,
        crear_version: false,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const sufijo = idioma === "en" || idioma === "en_normalize" ? "_EN" : "";
      a.download = `${nombre.replace(/\s+/g, "_")}${sufijo}.docx`;
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
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="default">
                <Download className="mr-1 h-4 w-4" />
                Exportar DOCX
                <ChevronDown className="ml-1 h-3.5 w-3.5 opacity-80" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-72">
              <DropdownMenuLabel>Elige idioma</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {IDIOMAS.map((idioma) => (
                <DropdownMenuItem
                  key={idioma.value}
                  onSelect={() => handleExportar(idioma.value)}
                  className="flex-col items-start gap-0.5 py-2"
                >
                  <span className="text-sm font-medium">{idioma.label}</span>
                  <span className="text-xs text-smnyl-text-muted">
                    {idioma.descripcion}
                  </span>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  );
}
