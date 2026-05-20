/**
 * Onboarding del modelo — paso 2 del flujo de creación.
 *
 * 6 campos cortos sobre plataforma, frecuencia y rutas que evitan que
 * Claude pregunte estos hechos básicos en cada sección. Persiste como
 * memoria_modelo del documento (vía PATCH /metadata o similar).
 *
 * En esta primera versión es un wrapper sobre editar_metadata para
 * los campos relevantes; iteraciones futuras podrán añadir un endpoint
 * dedicado para memoria_modelo.
 */
"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Brain, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Stepper } from "@/components/ui/stepper";
import { Textarea } from "@/components/ui/textarea";
import { useDocumento, useEditarMetadata } from "@/lib/api/hooks";

const PASOS = ["Crear / Importar", "Onboarding", "Brief", "Dashboard"];

export default function OnboardingPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const docQuery = useDocumento(id);
  const editar = useEditarMetadata();

  const [plataforma, setPlataforma] = useState("");
  const [version, setVersion] = useState("");
  const [estado, setEstado] = useState("");
  const [target, setTarget] = useState("");
  const [intended, setIntended] = useState("");
  const [restrictions, setRestrictions] = useState("");

  // Hidrata desde el documento existente
  useState(() => {
    if (docQuery.data) {
      const m = docQuery.data.metadata_modelo;
      setPlataforma(m.implementation_platform);
      setVersion(m.current_version);
      setEstado(m.model_status);
      setTarget(m.target_production_date);
      setIntended(m.intended_use);
      setRestrictions(m.use_restrictions);
    }
  });

  function handleSubmit() {
    editar.mutate(
      {
        id,
        payload: {
          implementation_platform: plataforma,
          current_version: version,
          model_status: estado,
          target_production_date: target,
          intended_use: intended,
          use_restrictions: restrictions,
        },
      },
      {
        onSuccess: () => {
          toast.success("Onboarding guardado.");
          router.push(`/documentos/${id}/brief`);
        },
        onError: (err) => toast.error(`Error: ${(err as Error).message}`),
      },
    );
  }

  if (docQuery.isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <Button variant="ghost" size="sm" asChild>
        <Link href={`/documentos/${id}`}>
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Saltar al dashboard
        </Link>
      </Button>

      <Stepper pasos={PASOS} actualIdx={1} />

      <div>
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-primary/10 text-smnyl-primary mb-3">
          <Brain className="h-5 w-5" />
        </div>
        <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-2">
          Cuéntame del modelo (1 vez)
        </h1>
        <p className="text-sm text-smnyl-text-muted max-w-xl">
          Estos hechos básicos viajan en cada llamada al LLM — al saberlos arriba,
          Claude evita re-preguntarlos en cada sección. Toma ~2 minutos.
        </p>
      </div>

      <Card className="p-6 space-y-5 animate-fade-in">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-4">
          <div className="space-y-2">
            <Label>Plataforma de implementación</Label>
            <Input
              placeholder="Ej. Prophet 12.1, R, Python, Excel"
              value={plataforma}
              onChange={(e) => setPlataforma(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Versión actual</Label>
            <Input
              placeholder="Ej. v2.1"
              value={version}
              onChange={(e) => setVersion(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Estado del modelo</Label>
            <Input
              placeholder="Ej. Production, Development, Decommissioned"
              value={estado}
              onChange={(e) => setEstado(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Target production date</Label>
            <Input
              placeholder="YYYY-MM-DD"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label>Uso intencionado</Label>
          <Textarea
            rows={3}
            placeholder="¿Para qué se usa el modelo? ¿Qué decisiones soporta?"
            value={intended}
            onChange={(e) => setIntended(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label>Restricciones de uso</Label>
          <Textarea
            rows={3}
            placeholder="¿Qué NO debe hacer este modelo? ¿Qué segmentos no aplican?"
            value={restrictions}
            onChange={(e) => setRestrictions(e.target.value)}
          />
        </div>
      </Card>

      <div className="flex gap-3">
        <Button size="lg" onClick={handleSubmit} disabled={editar.isPending}>
          {editar.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Continuar a Brief
        </Button>
        <Button variant="ghost" size="lg" asChild>
          <Link href={`/documentos/${id}`}>Hacerlo después</Link>
        </Button>
      </div>
    </div>
  );
}
