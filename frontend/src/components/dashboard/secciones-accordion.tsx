/**
 * SeccionesAccordion — agrupa las secciones por capítulo NYL (1-9).
 *
 * Cada capítulo muestra ✓/◐/○ + "X de Y resueltas". El primer capítulo
 * con pendientes (vacías/parciales o brecha crítica) arranca expandido.
 *
 * Replica el patrón del Streamlit (template_catalog.agrupar_secciones_por_capitulo).
 */
"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckCircle2, CircleDashed, Circle, FileEdit } from "lucide-react";

import type { Brecha, Documento, Seccion } from "@/lib/api/types";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const CAPITULOS_NYL: Record<string, string> = {
  "1": "Problem Statement",
  "2": "Model Profile",
  "3": "Ancillary Documents",
  "4": "Methodology",
  "5": "Data",
  "6": "Implementation",
  "7": "Outputs & Performance",
  "8": "Model Governance",
  "9": "Ongoing Monitoring",
};

interface SeccionesAccordionProps {
  documento: Documento;
  brechas: Brecha[];
}

function estadoMarker(secciones: Seccion[]) {
  const nResueltas = secciones.filter(
    (s) => s.completitud === "completa" || s.completitud === "omitida",
  ).length;
  const nVacias = secciones.filter((s) => s.completitud === "vacia").length;
  if (nResueltas === secciones.length && secciones.length > 0) {
    return { icon: CheckCircle2, color: "text-smnyl-success", label: "✓" };
  }
  if (nVacias === secciones.length) {
    return { icon: Circle, color: "text-smnyl-text-muted", label: "○" };
  }
  return { icon: CircleDashed, color: "text-smnyl-warning", label: "◐" };
}

export function SeccionesAccordion({ documento, brechas }: SeccionesAccordionProps) {
  // Si el doc es Prophet, no usa la agrupación NYL — muestra plano.
  if (documento.tipo === "prophet") {
    return <SeccionesPlanas documento={documento} />;
  }
  return <SeccionesNYL documento={documento} brechas={brechas} />;
}

function SeccionesNYL({ documento, brechas }: SeccionesAccordionProps) {
  // Agrupar por primer dígito del numero (1.1, 1.3 → cap 1)
  const grupos: Record<string, Seccion[]> = Object.fromEntries(
    Object.keys(CAPITULOS_NYL).map((cap) => [cap, [] as Seccion[]]),
  );
  for (const s of documento.secciones) {
    const cap = s.numero.split(".")[0];
    if (grupos[cap]) grupos[cap].push(s);
  }

  // Brechas por sección, para badge
  const brechasPorSeccion = new Map<string, number>();
  for (const b of brechas) {
    brechasPorSeccion.set(b.seccion_id, (brechasPorSeccion.get(b.seccion_id) ?? 0) + 1);
  }
  const idsConBrechaCritica = new Set(
    brechas.filter((b) => b.severidad === "alta").map((b) => b.seccion_id),
  );

  // Primer capítulo con pendientes — expandido por default
  const primerPendiente = Object.entries(grupos).find(([, secs]) => {
    const tienePendientes = secs.some(
      (s) => s.completitud === "vacia" || s.completitud === "parcial",
    );
    const tieneBrechaCrit = secs.some((s) => idsConBrechaCritica.has(s.id));
    return tienePendientes || tieneBrechaCrit;
  })?.[0];

  const [open, setOpen] = useState<string | undefined>(primerPendiente);

  return (
    <div className="animate-fade-in">
      <h2 className="font-display text-xl font-semibold text-smnyl-text mb-1">
        Secciones del Model Development Template
      </h2>
      <p className="text-sm text-smnyl-text-muted mb-4">
        Estado por capítulo. La entrevista te ayudará a llenar las vacías o parciales.
      </p>

      <Accordion type="single" collapsible value={open} onValueChange={setOpen}>
        <div className="space-y-2">
          {Object.entries(CAPITULOS_NYL).map(([cap, nombreCap]) => {
            const secs = grupos[cap];
            if (!secs || secs.length === 0) return null;
            const marker = estadoMarker(secs);
            const nResueltas = secs.filter(
              (s) => s.completitud === "completa" || s.completitud === "omitida",
            ).length;
            return (
              <AccordionItem key={cap} value={cap}>
                <AccordionTrigger>
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`text-base ${marker.color}`}>{marker.label}</span>
                    <span className="font-medium truncate">
                      Capítulo {cap}: {nombreCap}
                    </span>
                    <span className="text-smnyl-text-muted text-xs">·</span>
                    <span className="text-smnyl-text-muted text-sm">
                      {nResueltas} de {secs.length} resueltas
                    </span>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-1.5">
                    {secs.map((s) => (
                      <SeccionRow
                        key={s.id}
                        seccion={s}
                        documentoId={documento.id}
                        nBrechas={brechasPorSeccion.get(s.id) ?? 0}
                      />
                    ))}
                  </div>
                </AccordionContent>
              </AccordionItem>
            );
          })}
        </div>
      </Accordion>
    </div>
  );
}

function SeccionesPlanas({ documento }: { documento: Documento }) {
  return (
    <div className="animate-fade-in">
      <h2 className="font-display text-xl font-semibold text-smnyl-text mb-1">
        Secciones de la Ficha Prophet
      </h2>
      <p className="text-sm text-smnyl-text-muted mb-4">
        Cada sección corresponde a una hoja del registro Excel de Modelos Actuariales.
      </p>
      <div className="space-y-1.5">
        {documento.secciones.map((s) => (
          <SeccionRow key={s.id} seccion={s} documentoId={documento.id} nBrechas={0} />
        ))}
      </div>
    </div>
  );
}

interface SeccionRowProps {
  seccion: Seccion;
  documentoId: string;
  nBrechas: number;
}

function SeccionRow({ seccion, documentoId, nBrechas }: SeccionRowProps) {
  const completitudVariant: Record<
    Seccion["completitud"],
    { label: string; bg: string; fg: string }
  > = {
    completa: { label: "Completa", bg: "bg-smnyl-success-soft", fg: "text-smnyl-success-dark" },
    parcial: { label: "Parcial", bg: "bg-smnyl-warning-soft", fg: "text-smnyl-warning-dark" },
    vacia: { label: "Vacía", bg: "bg-smnyl-danger-soft", fg: "text-smnyl-danger" },
    omitida: { label: "Omitida", bg: "bg-smnyl-bg-soft", fg: "text-smnyl-text-muted" },
  };
  const v = completitudVariant[seccion.completitud];

  return (
    <div
      className="
        flex items-center gap-3 rounded-md px-3 py-2
        hover:bg-smnyl-bg-soft/60 transition-colors duration-150
      "
    >
      <span
        className={`shrink-0 inline-flex items-center rounded-full px-2 py-0.5 text-[0.65rem] font-semibold uppercase tracking-wider ${v.bg} ${v.fg}`}
      >
        {v.label}
      </span>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-smnyl-text truncate">
          {seccion.numero} {seccion.nombre}
        </div>
        {seccion.intencion && (
          <div className="text-xs text-smnyl-text-muted truncate">{seccion.intencion}</div>
        )}
      </div>
      {nBrechas > 0 && (
        <Badge variant="critica" className="shrink-0">
          {nBrechas} brecha{nBrechas === 1 ? "" : "s"}
        </Badge>
      )}
      <Button variant="ghost" size="sm" asChild className="shrink-0">
        <Link href={`/documentos/${documentoId}/secciones/${encodeURIComponent(seccion.id)}`}>
          <FileEdit className="mr-1 h-3.5 w-3.5" />
          Editar
        </Link>
      </Button>
    </div>
  );
}
