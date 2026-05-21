/**
 * WelcomeHero — pantalla de bienvenida cuando no hay docs activos.
 * Replica el modo "sin actividad" del home Streamlit.
 */
"use client";

import Link from "next/link";
import { FilePlus2, Upload, Sparkles } from "lucide-react";

import { Card } from "@/components/ui/card";

interface CTACardProps {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  primary?: boolean;
}

function CTACard({ href, icon: Icon, title, description, primary }: CTACardProps) {
  return (
    <Link href={href} className="group block">
      <Card
        className={`
          h-full p-6 cursor-pointer
          hover:shadow-smnyl-md hover:-translate-y-0.5 hover:border-smnyl-accent-soft
          ${primary ? "border-smnyl-primary/40 bg-gradient-to-br from-white to-smnyl-accent-soft/30" : ""}
        `}
      >
        <div
          className={`
            inline-flex h-10 w-10 items-center justify-center rounded-lg mb-4
            ${primary ? "bg-smnyl-primary text-white" : "bg-smnyl-bg-soft text-smnyl-primary"}
            group-hover:scale-110 transition-transform duration-200
          `}
        >
          <Icon className="h-5 w-5" />
        </div>
        <h3 className="font-display text-lg font-semibold text-smnyl-text mb-1">{title}</h3>
        <p className="text-sm text-smnyl-text-muted leading-relaxed">{description}</p>
      </Card>
    </Link>
  );
}

export function WelcomeHero() {
  return (
    <section className="animate-fade-in">
      <h1 className="font-display text-4xl font-semibold text-smnyl-text leading-tight mb-3">
        Documenta modelos sin fricción
      </h1>
      <p className="text-lg text-smnyl-text-muted max-w-2xl mb-10 leading-relaxed">
        DocuMente entrevista, estructura y genera documentación institucional alineada
        con el marco MRM de SMNYL — desde cero o partiendo de un documento existente.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <CTACard
          primary
          href="/documentos/crear"
          icon={FilePlus2}
          title="Crear nuevo documento"
          description="Empieza con las 28 secciones vacías del template oficial NYL."
        />
        <CTACard
          href="/importar"
          icon={Upload}
          title="Mejorar documento existente"
          description="Sube un .docx o .pdf y DocuMente detectará brechas vs el template."
        />
        <CTACard
          href="/prophet"
          icon={Sparkles}
          title="Iniciar Ficha Prophet"
          description="Importa el registro Excel de Modelos Actuariales y genera la ficha técnica."
        />
      </div>
    </section>
  );
}
