/**
 * Timeline vertical de eventos del audit_trail.
 *
 * Cada evento se rendera con icono + color de su tipo, descripción y
 * timestamp humano. Replica el timeline de Streamlit (timeline.py)
 * con paleta SMNYL y diseño premium.
 */
"use client";

import {
  Edit3,
  Download,
  CheckCheck,
  ArrowRight,
  Trash2,
  Archive,
  Undo2,
  GitBranch,
  FileText,
  Plus,
  CircleX,
  Sparkles,
} from "lucide-react";

import type { EventoAuditoria, TipoEvento } from "@/lib/api/types";
import { tiempoRelativo } from "@/lib/utils";

const TIPO_CONFIG: Record<
  TipoEvento,
  { label: string; icon: React.ComponentType<{ className?: string }>; color: string; bg: string }
> = {
  documento_creado: {
    label: "Documento creado",
    icon: Plus,
    color: "text-smnyl-success-dark",
    bg: "bg-smnyl-success-soft",
  },
  documento_importado: {
    label: "Documento importado",
    icon: FileText,
    color: "text-smnyl-info-dark",
    bg: "bg-smnyl-info-soft",
  },
  seccion_editada: {
    label: "Sección editada",
    icon: Edit3,
    color: "text-smnyl-success-dark",
    bg: "bg-smnyl-success-soft",
  },
  seccion_completada: {
    label: "Sección completada",
    icon: CheckCheck,
    color: "text-smnyl-success-dark",
    bg: "bg-smnyl-success-soft",
  },
  seccion_omitida: {
    label: "Sección omitida",
    icon: CircleX,
    color: "text-smnyl-text-muted",
    bg: "bg-smnyl-bg-soft",
  },
  transicion_estado: {
    label: "Transición de estado",
    icon: ArrowRight,
    color: "text-smnyl-primary",
    bg: "bg-smnyl-accent-soft/50",
  },
  metadata_actualizada: {
    label: "Metadata actualizada",
    icon: Sparkles,
    color: "text-smnyl-info-dark",
    bg: "bg-smnyl-info-soft",
  },
  exportado: {
    label: "Exportado",
    icon: Download,
    color: "text-smnyl-info-dark",
    bg: "bg-smnyl-info-soft",
  },
  signoff_reviewer: {
    label: "Sign-off Reviewer",
    icon: CheckCheck,
    color: "text-smnyl-warning-dark",
    bg: "bg-smnyl-warning-soft",
  },
  signoff_fae: {
    label: "Sign-off FAE",
    icon: CheckCheck,
    color: "text-smnyl-warning-dark",
    bg: "bg-smnyl-warning-soft",
  },
  archivado: {
    label: "Archivado",
    icon: Archive,
    color: "text-smnyl-text-muted",
    bg: "bg-smnyl-bg-soft",
  },
  desarchivado: {
    label: "Desarchivado",
    icon: Undo2,
    color: "text-smnyl-text-muted",
    bg: "bg-smnyl-bg-soft",
  },
  enviado_a_papelera: {
    label: "Movido a papelera",
    icon: Trash2,
    color: "text-smnyl-danger",
    bg: "bg-smnyl-danger-soft",
  },
  restaurado_de_papelera: {
    label: "Restaurado de papelera",
    icon: Undo2,
    color: "text-smnyl-text-muted",
    bg: "bg-smnyl-bg-soft",
  },
  eliminado_permanente: {
    label: "Eliminado permanentemente",
    icon: Trash2,
    color: "text-smnyl-danger",
    bg: "bg-smnyl-danger-soft",
  },
  purgado_automatico: {
    label: "Purgado automático",
    icon: Trash2,
    color: "text-smnyl-text-muted",
    bg: "bg-smnyl-bg-soft",
  },
  version_creada: {
    label: "Versión creada",
    icon: GitBranch,
    color: "text-smnyl-primary",
    bg: "bg-smnyl-accent-soft/50",
  },
  version_restaurada: {
    label: "Versión restaurada",
    icon: Undo2,
    color: "text-smnyl-primary",
    bg: "bg-smnyl-accent-soft/50",
  },
};

interface TimelineProps {
  eventos: EventoAuditoria[];
}

export function Timeline({ eventos }: TimelineProps) {
  if (eventos.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-smnyl-border bg-smnyl-bg-soft/40 p-8 text-center">
        <p className="text-sm italic text-smnyl-text-muted">
          Aún no hay eventos registrados.
        </p>
      </div>
    );
  }

  return (
    <ol className="relative space-y-1">
      <div
        className="absolute left-[18px] top-1 bottom-1 w-px bg-smnyl-border"
        aria-hidden
      />
      {eventos.map((e, i) => {
        const cfg = TIPO_CONFIG[e.tipo] ?? TIPO_CONFIG.metadata_actualizada;
        const Icon = cfg.icon;
        return (
          <li
            key={`${e.timestamp}-${i}`}
            className="relative flex gap-4 pl-0 py-2 animate-fade-in"
          >
            <div
              className={`
                relative z-10 shrink-0 flex h-9 w-9 items-center justify-center rounded-full
                ${cfg.bg} border-2 border-white shadow-smnyl-sm
              `}
            >
              <Icon className={`h-4 w-4 ${cfg.color}`} />
            </div>
            <div className="flex-1 min-w-0 pt-1">
              <div className="flex items-baseline gap-2 flex-wrap">
                <span className={`text-xs font-semibold uppercase tracking-wider ${cfg.color}`}>
                  {cfg.label}
                </span>
                <span className="text-xs text-smnyl-text-muted">·</span>
                <span className="text-xs text-smnyl-text-muted italic">
                  {tiempoRelativo(e.timestamp)}
                </span>
              </div>
              <p className="text-sm text-smnyl-text mt-0.5 leading-snug">
                {e.descripcion}
              </p>
              <p className="text-xs text-smnyl-text-muted mt-0.5">
                por <span className="font-medium">{e.actor}</span>
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
