/**
 * BrechasAccordion — 3 expanders por severidad (Críticas / Atención /
 * Sugerencias). El primer grupo no vacío arranca expandido para guiar
 * la atención (goal-gradient).
 *
 * Replica el patrón premium T1 del Streamlit (_render_brechas_agrupadas).
 */
"use client";

import { useState } from "react";
import { AlertTriangle, Lightbulb, AlertCircle } from "lucide-react";

import type { Brecha, Severidad } from "@/lib/api/types";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const SEV_CONFIG: Record<
  Severidad,
  { label: string; icon: React.ComponentType<{ className?: string }>; accentClass: string }
> = {
  alta: { label: "Críticas", icon: AlertCircle, accentClass: "text-smnyl-danger" },
  media: { label: "Atención", icon: AlertTriangle, accentClass: "text-smnyl-warning-dark" },
  baja: { label: "Sugerencias", icon: Lightbulb, accentClass: "text-smnyl-info-dark" },
};

interface BrechasAccordionProps {
  brechas: Brecha[];
}

export function BrechasAccordion({ brechas }: BrechasAccordionProps) {
  const grupos = {
    alta: brechas.filter((b) => b.severidad === "alta"),
    media: brechas.filter((b) => b.severidad === "media"),
    baja: brechas.filter((b) => b.severidad === "baja"),
  };
  // Primer grupo no vacío abre por default
  const primerNoVacio = (["alta", "media", "baja"] as Severidad[]).find(
    (s) => grupos[s].length > 0,
  );
  const [open, setOpen] = useState<string | undefined>(primerNoVacio);

  if (brechas.length === 0) {
    return (
      <div className="rounded-xl border border-smnyl-success-dark/30 bg-smnyl-success-soft/60 p-6 text-center animate-fade-in">
        <div className="mx-auto mb-3 inline-flex h-12 w-12 items-center justify-center rounded-full bg-smnyl-success-dark/15 text-2xl">
          🎉
        </div>
        <h3 className="font-display text-lg font-semibold text-smnyl-success-dark mb-1">
          ¡Documento listo para revisión!
        </h3>
        <p className="text-sm text-smnyl-text-muted max-w-lg mx-auto">
          No hay brechas detectadas en las secciones obligatorias. Puedes exportar el
          documento o seguir refinando contenido opcional.
        </p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <h2 className="font-display text-xl font-semibold text-smnyl-text mb-1">
        Brechas
      </h2>
      <p className="text-sm text-smnyl-text-muted mb-4">
        Agrupadas por severidad. Empieza por las marcadas como Críticas.
      </p>

      <Accordion type="single" collapsible value={open} onValueChange={setOpen}>
        <div className="space-y-2">
          {(["alta", "media", "baja"] as Severidad[]).map((sev) => {
            const lista = grupos[sev];
            if (lista.length === 0) return null;
            const cfg = SEV_CONFIG[sev];
            const Icon = cfg.icon;
            return (
              <AccordionItem key={sev} value={sev}>
                <AccordionTrigger>
                  <div className="flex items-center gap-3">
                    <Icon className={`h-4 w-4 ${cfg.accentClass}`} />
                    <span className="font-medium">{cfg.label}</span>
                    <span className="text-smnyl-text-muted text-xs">·</span>
                    <span className="text-smnyl-text-muted text-sm">{lista.length}</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <ul className="divide-y divide-smnyl-border/60">
                    {lista.map((b, i) => (
                      <li key={`${b.seccion_id}-${i}`} className="py-2.5">
                        <p className="text-sm font-medium text-smnyl-text leading-snug">
                          {b.mensaje}
                        </p>
                        {b.sugerencia && (
                          <p className="text-xs text-smnyl-text-muted leading-snug mt-1">
                            <span className="italic">Sugerencia:</span> {b.sugerencia}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                </AccordionContent>
              </AccordionItem>
            );
          })}
        </div>
      </Accordion>
    </div>
  );
}
