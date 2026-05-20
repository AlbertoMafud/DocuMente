/**
 * Editar metadata del modelo — formulario con todos los campos MRM.
 *
 * Layout en 2 columnas; al guardar invalida cache del documento y vuelve
 * al dashboard. Solo se envían los campos modificados.
 */
"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Save, Loader2 } from "lucide-react";
import { toast } from "sonner";

import type { MetadataModelo, TierRiesgo } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useDocumento, useEditarMetadata } from "@/lib/api/hooks";

const TIER_OPTIONS: { value: TierRiesgo | ""; label: string }[] = [
  { value: "", label: "— Sin definir —" },
  { value: "low", label: "Low" },
  { value: "medium_minus", label: "Medium-" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "very_high", label: "Very High" },
  { value: "very_high_plus", label: "Very High+" },
  { value: "critical", label: "Critical" },
];

type FormState = Partial<MetadataModelo>;

export default function EditarMetadataPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const docQuery = useDocumento(id);
  const editar = useEditarMetadata();

  const [form, setForm] = useState<FormState>({});
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (!initialized && docQuery.data) {
      setForm(docQuery.data.metadata_modelo);
      setInitialized(true);
    }
  }, [docQuery.data, initialized]);

  if (docQuery.isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }

  if (!docQuery.data) {
    return (
      <p className="text-sm text-smnyl-danger">No se pudo cargar el documento.</p>
    );
  }

  function setField<K extends keyof MetadataModelo>(
    key: K,
    value: MetadataModelo[K],
  ) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function setList(key: "model_developers" | "model_users", raw: string) {
    const items = raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    setField(key, items);
  }

  function handleSave() {
    editar.mutate(
      { id, payload: form },
      {
        onSuccess: () => {
          toast.success("Metadata actualizada.");
          router.push(`/documentos/${id}`);
        },
        onError: (err) => toast.error(`Error: ${(err as Error).message}`),
      },
    );
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <Button variant="ghost" size="sm" asChild>
        <Link href={`/documentos/${id}`}>
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Volver al dashboard
        </Link>
      </Button>

      <div>
        <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-2">
          Editar metadata del modelo
        </h1>
        <p className="text-sm text-smnyl-text-muted max-w-2xl">
          Tabla de atributos sección 1.1 — identifica al modelo dentro del marco MRM.
          Solo se enviarán los campos que modifiques.
        </p>
      </div>

      <Card className="p-6 animate-fade-in">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-5">
          <Field
            label="Nombre del modelo"
            value={form.nombre_modelo ?? ""}
            onChange={(v) => setField("nombre_modelo", v)}
            placeholder="Ej. Value of New Business — GMM"
          />
          <Field
            label="Model ID"
            value={form.model_id ?? ""}
            onChange={(v) => setField("model_id", v)}
            placeholder="Identificador interno único"
          />
          <Field
            label="Model class"
            value={form.model_class ?? ""}
            onChange={(v) => setField("model_class", v)}
            placeholder="Ej. Stochastic / GLM / ML"
          />
          <Field
            label="Profit center"
            value={form.profit_center ?? ""}
            onChange={(v) => setField("profit_center", v)}
          />
          <Field
            label="FAE (Functional Area Executive)"
            value={form.fae ?? ""}
            onChange={(v) => setField("fae", v)}
          />
          <Field
            label="Model owner"
            value={form.model_owner ?? ""}
            onChange={(v) => setField("model_owner", v)}
          />
          <Field
            label="Model developers (separados por coma)"
            value={(form.model_developers ?? []).join(", ")}
            onChange={(v) => setList("model_developers", v)}
            placeholder="Nombre1, Nombre2, …"
          />
          <Field
            label="Model users (separados por coma)"
            value={(form.model_users ?? []).join(", ")}
            onChange={(v) => setList("model_users", v)}
          />
          <Field
            label="Versión actual"
            value={form.current_version ?? ""}
            onChange={(v) => setField("current_version", v)}
            placeholder="Ej. v1.2"
          />
          <Field
            label="Plataforma de implementación"
            value={form.implementation_platform ?? ""}
            onChange={(v) => setField("implementation_platform", v)}
            placeholder="Ej. Prophet, R, Python"
          />
          <Field
            label="Impacto financiero"
            value={form.financial_impact ?? ""}
            onChange={(v) => setField("financial_impact", v)}
          />
          <Field
            label="Estado del modelo"
            value={form.model_status ?? ""}
            onChange={(v) => setField("model_status", v)}
            placeholder="Ej. Production / Development"
          />
          <Field
            label="Target production date"
            value={form.target_production_date ?? ""}
            onChange={(v) => setField("target_production_date", v)}
            placeholder="YYYY-MM-DD"
          />
          <div className="space-y-2">
            <Label>Inherent risk tier</Label>
            <select
              className="
                flex h-10 w-full rounded-md border border-smnyl-border bg-white px-3 text-sm
                transition-all duration-200 ease-out
                focus-visible:outline-none focus-visible:border-smnyl-primary
                focus-visible:ring-2 focus-visible:ring-smnyl-primary/15
              "
              value={form.inherent_risk_tier ?? ""}
              onChange={(e) =>
                setField(
                  "inherent_risk_tier",
                  (e.target.value === "" ? null : e.target.value) as TierRiesgo | null,
                )
              }
            >
              {TIER_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <Field
            label="Nomenclatura"
            value={form.nomenclatura ?? ""}
            onChange={(v) => setField("nomenclatura", v)}
            placeholder="Ej. M07.P07.S03.006.D"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-5 mt-5">
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="intended">Uso intencionado</Label>
            <Textarea
              id="intended"
              rows={3}
              value={form.intended_use ?? ""}
              onChange={(e) => setField("intended_use", e.target.value)}
              placeholder="Para qué se diseñó el modelo, qué decisiones soporta."
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="restrictions">Restricciones de uso</Label>
            <Textarea
              id="restrictions"
              rows={3}
              value={form.use_restrictions ?? ""}
              onChange={(e) => setField("use_restrictions", e.target.value)}
              placeholder="Limitaciones, segmentos no aplicables, condiciones que invalidan el modelo."
            />
          </div>
        </div>
      </Card>

      <div className="flex gap-3">
        <Button size="lg" onClick={handleSave} disabled={editar.isPending}>
          {editar.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Guardar metadata
        </Button>
        <Button variant="ghost" size="lg" asChild>
          <Link href={`/documentos/${id}`}>Cancelar</Link>
        </Button>
      </div>
    </div>
  );
}

interface FieldProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}

function Field({ label, value, onChange, placeholder }: FieldProps) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  );
}
