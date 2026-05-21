/**
 * Brief inicial — paso 3 del flujo, opcional.
 *
 * Captura una descripción ejecutiva del modelo en lenguaje natural que
 * DocuMente usará para pre-poblar las primeras secciones del template.
 * En esta versión, el brief se guarda como parte de la metadata y la
 * entrevista lo absorberá; iteraciones futuras añadirán un endpoint
 * dedicado AplicarBrief.
 */
"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, FileText, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Stepper } from "@/components/ui/stepper";
import { Textarea } from "@/components/ui/textarea";
import { useDocumento, useEditarMetadata } from "@/lib/api/hooks";

const PASOS = ["Crear / Importar", "Onboarding", "Brief", "Dashboard"];

export default function BriefPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const docQuery = useDocumento(id);
  const editar = useEditarMetadata();

  const [brief, setBrief] = useState("");

  function handleContinuar() {
    if (!brief.trim()) {
      router.push(`/documentos/${id}`);
      return;
    }
    // Guarda el brief como descripción extendida del intended_use si está vacío,
    // o como sufijo. Esto es temporal hasta que exista un endpoint AplicarBrief.
    const current = docQuery.data?.metadata_modelo.intended_use ?? "";
    const nuevo = current.trim()
      ? `${current.trim()}\n\n--- Brief inicial ---\n${brief.trim()}`
      : brief.trim();

    editar.mutate(
      { id, payload: { intended_use: nuevo } },
      {
        onSuccess: () => {
          toast.success("Brief guardado.");
          router.push(`/documentos/${id}`);
        },
        onError: (err) => toast.error(`Error: ${(err as Error).message}`),
      },
    );
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <Button variant="ghost" size="sm" asChild>
        <Link href={`/documentos/${id}`}>
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Saltar al dashboard
        </Link>
      </Button>

      <Stepper pasos={PASOS} actualIdx={2} />

      <div>
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-primary/10 text-smnyl-primary mb-3">
          <FileText className="h-5 w-5" />
        </div>
        <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-2">
          Brief inicial
        </h1>
        <p className="text-sm text-smnyl-text-muted max-w-xl">
          Describe el modelo en lenguaje natural — 2-5 párrafos. DocuMente lo usa para
          pre-poblar secciones y acortar la entrevista.
        </p>
      </div>

      <Card className="p-6 animate-fade-in">
        <div className="space-y-2">
          <Label htmlFor="brief">Descripción ejecutiva del modelo</Label>
          <Textarea
            id="brief"
            rows={12}
            placeholder={[
              "Ejemplos de qué incluir:",
              "• Problema que resuelve",
              "• Metodología o approach general",
              "• Datos que usa",
              "• Quiénes lo usan y cómo",
              "• Riesgos / limitaciones conocidas",
              "",
              "Escribe en flujo natural — no necesitas estructura formal.",
            ].join("\n")}
            value={brief}
            onChange={(e) => setBrief(e.target.value)}
            className="font-body text-sm leading-relaxed"
          />
          <p className="text-xs text-smnyl-text-muted">
            {brief.length} caracteres · puedes omitirlo y continuar al dashboard.
          </p>
        </div>
      </Card>

      <div className="flex gap-3">
        <Button size="lg" onClick={handleContinuar} disabled={editar.isPending}>
          {editar.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Continuar al dashboard
        </Button>
      </div>
    </div>
  );
}
