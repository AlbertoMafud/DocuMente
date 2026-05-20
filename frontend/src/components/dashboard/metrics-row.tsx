/**
 * MetricsRow — 5 cards densas con border-left de color + mini progress bar.
 *
 * Layout: Resolución | Críticas | Atención | Sugerencias | Omitidas.
 * Replica el patrón premium T1 del Streamlit (dashboard.py _render_resumen).
 */
"use client";

import type { Brecha, Documento } from "@/lib/api/types";

interface MetricsRowProps {
  documento: Documento;
  brechas: Brecha[];
}

interface MetricCardProps {
  label: string;
  value: string | number;
  sub: string;
  accent: string;
  progressPct?: number;
}

function MetricCard({ label, value, sub, accent, progressPct }: MetricCardProps) {
  return (
    <div
      className="
        relative rounded-xl border border-smnyl-border bg-white p-4
        shadow-smnyl-sm transition-all duration-200 ease-out
        hover:shadow-smnyl-md
      "
      style={{ borderLeftWidth: 3, borderLeftColor: accent }}
    >
      <div className="text-[0.68rem] font-semibold uppercase tracking-[0.07em] text-smnyl-text-muted">
        {label}
      </div>
      <div className="mt-1 font-display text-2xl font-semibold text-smnyl-text leading-tight">
        {value}
      </div>
      {progressPct !== undefined && (
        <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-smnyl-bg-soft">
          <div
            className="h-full transition-all duration-500 ease-out"
            style={{ width: `${progressPct}%`, backgroundColor: accent }}
          />
        </div>
      )}
      <div className="mt-1.5 text-[0.78rem] leading-snug text-smnyl-text-muted">{sub}</div>
    </div>
  );
}

export function MetricsRow({ documento, brechas }: MetricsRowProps) {
  const oblig = documento.secciones.filter((s) => s.obligatoria);
  const nCompletas = oblig.filter((s) => s.completitud === "completa").length;
  const nOmitidas = oblig.filter((s) => s.completitud === "omitida").length;
  const resueltoPct = Math.round(documento.porcentaje_resuelto * 100);

  const nAlta = brechas.filter((b) => b.severidad === "alta").length;
  const nMedia = brechas.filter((b) => b.severidad === "media").length;
  const nBaja = brechas.filter((b) => b.severidad === "baja").length;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 animate-fade-in">
      <MetricCard
        label="Resolución"
        value={`${resueltoPct}%`}
        sub={`${nCompletas} de ${oblig.length} secciones obligatorias`}
        accent="#0079c2"  // primary
        progressPct={resueltoPct}
      />
      <MetricCard
        label="Críticas"
        value={nAlta}
        sub="bloquean revisión MRM"
        accent="#754a62"  // danger
      />
      <MetricCard
        label="Atención"
        value={nMedia}
        sub="resolver antes de aprobar"
        accent="#544235"  // warning_dark
      />
      <MetricCard
        label="Sugerencias"
        value={nBaja}
        sub="mejoras opcionales"
        accent="#0a385e"  // info_dark
      />
      <MetricCard
        label="Omitidas"
        value={nOmitidas}
        sub="resueltas con motivo"
        accent="#565656"  // text_muted
      />
    </div>
  );
}
