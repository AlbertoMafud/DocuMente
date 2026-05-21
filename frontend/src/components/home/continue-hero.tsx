/**
 * ContinueHero — banner prominente "Continúa donde te quedaste" para
 * el documento activo más reciente. Replica el componente Streamlit
 * (src/ui/components/continue_hero.py) con visual premium.
 */
"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

import type { DocumentoListItem } from "@/lib/api/types";
import { tiempoRelativo } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface ContinueHeroProps {
  doc: DocumentoListItem;
}

export function ContinueHero({ doc }: ContinueHeroProps) {
  const pct = Math.round(doc.porcentaje_completitud * 100);
  const nombre = doc.nombre_modelo || "Documento sin nombre";

  return (
    <section
      className="
        relative overflow-hidden rounded-xl border border-smnyl-accent-soft
        bg-gradient-to-br from-smnyl-primary/[0.03] via-white to-smnyl-accent-soft/40
        p-8 shadow-smnyl-sm animate-fade-in
      "
    >
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_30%_20%,rgba(0,121,194,0.06),transparent_60%)]" />

      <p className="text-[0.7rem] font-bold uppercase tracking-[0.12em] text-smnyl-primary-dark">
        Continúa donde te quedaste
      </p>
      <h1 className="font-display text-3xl font-semibold text-smnyl-text mt-2 mb-1">
        {nombre}
      </h1>
      <div className="text-sm text-smnyl-text-muted">
        <strong className="text-smnyl-primary-dark">{pct}% completo</strong>
        <span className="mx-2">·</span>
        Estado: {doc.estado}
      </div>
      <div className="text-xs italic text-smnyl-text-muted mt-1">
        Última edición {tiempoRelativo(doc.actualizado_en)}
      </div>

      <div className="mt-6">
        <Button asChild size="lg">
          <Link href={`/documentos/${doc.id}`}>
            Continuar
            <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </Button>
      </div>
    </section>
  );
}
