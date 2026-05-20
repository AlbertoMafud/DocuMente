/**
 * Página de Ficha Prophet — flujo en 2 pasos:
 * 1. Sube Excel del registro → POST /prophet/detectar → lista de modelos
 * 2. Selecciona modelo + nombre → POST /prophet/importar → redirect al dashboard
 */
"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  Loader2,
  Sparkles,
  UploadCloud,
  FileSpreadsheet,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { prophetApi } from "@/lib/api/client";

type Modelo = { nombre: string; fila_idx: number; profit_center?: string };
type Step = "subir" | "elegir";

export default function ProphetPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("subir");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [modelos, setModelos] = useState<Modelo[]>([]);
  const [advertencias, setAdvertencias] = useState<string[]>([]);
  const [seleccionado, setSeleccionado] = useState<Modelo | null>(null);
  const [nombreCustom, setNombreCustom] = useState("");
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;
    const f = files[0];
    const ext = f.name.split(".").pop()?.toLowerCase();
    if (ext !== "xlsx" && ext !== "xls") {
      toast.error("El registro Prophet debe ser un archivo .xlsx o .xls.");
      return;
    }
    setArchivo(f);
  }, []);

  async function handleDetectar() {
    if (!archivo) return;
    setLoading(true);
    const toastId = toast.loading("Analizando el Excel…");
    try {
      const r = await prophetApi.detectar(archivo);
      setModelos(r.modelos);
      setAdvertencias(r.advertencias);
      toast.success(`${r.modelos.length} modelo(s) detectado(s).`, { id: toastId });
      setStep("elegir");
    } catch (err) {
      toast.error(`Error al analizar: ${(err as Error).message}`, { id: toastId });
    } finally {
      setLoading(false);
    }
  }

  async function handleImportar() {
    if (!archivo || !seleccionado) return;
    const nombre = (nombreCustom || seleccionado.nombre).trim();
    if (!nombre) {
      toast.error("Necesito un nombre para el modelo.");
      return;
    }
    setLoading(true);
    const toastId = toast.loading("Creando Ficha Prophet…");
    try {
      const doc = await prophetApi.importar(archivo, seleccionado.fila_idx, nombre);
      toast.success(`Ficha "${nombre}" creada.`, { id: toastId });
      router.push(`/documentos/${doc.id}`);
    } catch (err) {
      toast.error(`Error al importar: ${(err as Error).message}`, { id: toastId });
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      <Button variant="ghost" size="sm" asChild>
        <Link href="/">
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Volver a Inicio
        </Link>
      </Button>

      <div>
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-warning-soft text-smnyl-warning-dark mb-3">
          <Sparkles className="h-5 w-5" />
        </div>
        <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-2">
          Ficha Prophet
        </h1>
        <p className="text-sm text-smnyl-text-muted max-w-xl">
          Sube el registro Excel de Modelos Actuariales. DocuMente detectará los modelos
          disponibles y generará una ficha técnica pre-poblada con los datos del registro.
        </p>
      </div>

      <StepIndicator step={step} />

      {step === "subir" && (
        <section className="animate-fade-in space-y-4">
          <DropZone
            isOver={dragOver}
            onDrop={(files) => {
              setDragOver(false);
              handleFile(files);
            }}
            onDragOver={() => setDragOver(true)}
            onDragLeave={() => setDragOver(false)}
            onClick={() => inputRef.current?.click()}
          >
            {archivo ? (
              <FilePreview file={archivo} onRemove={() => setArchivo(null)} />
            ) : (
              <DropZoneEmpty />
            )}
          </DropZone>
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.xls"
            className="hidden"
            onChange={(e) => handleFile(e.target.files)}
          />

          <div className="flex gap-3">
            <Button size="lg" onClick={handleDetectar} disabled={!archivo || loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Analizar registro
              <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
            <Button variant="ghost" size="lg" asChild>
              <Link href="/">Cancelar</Link>
            </Button>
          </div>
        </section>
      )}

      {step === "elegir" && (
        <section className="animate-fade-in space-y-4">
          {advertencias.length > 0 && (
            <div className="rounded-lg border border-smnyl-warning-dark/30 bg-smnyl-warning-soft p-3">
              <p className="text-xs font-semibold text-smnyl-warning-dark uppercase tracking-wider mb-1">
                Advertencias del análisis
              </p>
              <ul className="text-xs text-smnyl-text-muted space-y-0.5 list-disc list-inside">
                {advertencias.slice(0, 5).map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <Label className="mb-2 block">Elige el modelo a documentar</Label>
            <div className="space-y-2">
              {modelos.length === 0 && (
                <p className="text-sm text-smnyl-text-muted italic">
                  No se detectaron modelos en el Excel. Verifica que la hoja
                  &quot;Descripcion_General&quot; existe.
                </p>
              )}
              {modelos.map((m) => (
                <button
                  key={m.fila_idx}
                  type="button"
                  onClick={() => setSeleccionado(m)}
                  className="block w-full text-left"
                >
                  <Card
                    className={`
                      p-4 cursor-pointer transition-all duration-200 ease-out
                      ${seleccionado?.fila_idx === m.fila_idx
                        ? "border-smnyl-primary bg-smnyl-accent-soft/20 ring-2 ring-smnyl-primary/20"
                        : "hover:border-smnyl-accent-soft hover:shadow-smnyl-md"}
                    `}
                  >
                    <div className="font-medium text-smnyl-text">{m.nombre}</div>
                    {m.profit_center && (
                      <div className="text-xs text-smnyl-text-muted mt-0.5">
                        Profit center: {m.profit_center}
                      </div>
                    )}
                  </Card>
                </button>
              ))}
            </div>
          </div>

          {seleccionado && (
            <div className="space-y-2 max-w-md">
              <Label htmlFor="nombre-custom">Nombre de la ficha</Label>
              <Input
                id="nombre-custom"
                placeholder={seleccionado.nombre}
                value={nombreCustom}
                onChange={(e) => setNombreCustom(e.target.value)}
              />
              <p className="text-xs text-smnyl-text-muted">
                Puedes ajustar el nombre. Por default se usa el del registro.
              </p>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <Button
              size="lg"
              onClick={handleImportar}
              disabled={!seleccionado || loading}
            >
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Crear ficha
            </Button>
            <Button variant="ghost" size="lg" onClick={() => setStep("subir")}>
              Volver al paso anterior
            </Button>
          </div>
        </section>
      )}
    </div>
  );
}

function StepIndicator({ step }: { step: Step }) {
  const steps = [
    { key: "subir", label: "Subir registro" },
    { key: "elegir", label: "Elegir modelo" },
  ] as const;
  return (
    <ol className="flex items-center gap-3 text-sm">
      {steps.map((s, i) => {
        const isActive = s.key === step;
        const isDone =
          (step === "elegir" && s.key === "subir");
        return (
          <li key={s.key} className="flex items-center gap-3">
            <span
              className={`
                inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold
                ${isActive
                  ? "bg-smnyl-primary text-white shadow-smnyl-sm"
                  : isDone
                    ? "bg-smnyl-success-dark text-white"
                    : "bg-smnyl-bg-soft text-smnyl-text-muted"}
              `}
            >
              {isDone ? "✓" : i + 1}
            </span>
            <span
              className={
                isActive
                  ? "font-medium text-smnyl-text"
                  : "text-smnyl-text-muted"
              }
            >
              {s.label}
            </span>
            {i < steps.length - 1 && (
              <span className="text-smnyl-text-muted mx-2">→</span>
            )}
          </li>
        );
      })}
    </ol>
  );
}

function DropZone({
  isOver,
  onDrop,
  onDragOver,
  onDragLeave,
  onClick,
  children,
}: {
  isOver: boolean;
  onDrop: (files: FileList | null) => void;
  onDragOver: () => void;
  onDragLeave: () => void;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onClick()}
      onDragOver={(e) => {
        e.preventDefault();
        onDragOver();
      }}
      onDragLeave={onDragLeave}
      onDrop={(e) => {
        e.preventDefault();
        onDrop(e.dataTransfer.files);
      }}
      className={`
        rounded-xl border-2 border-dashed cursor-pointer
        transition-all duration-200 ease-out
        ${isOver
          ? "border-smnyl-primary bg-smnyl-accent-soft/30"
          : "border-smnyl-border hover:border-smnyl-accent-soft hover:bg-smnyl-bg-soft/40"}
      `}
    >
      {children}
    </div>
  );
}

function DropZoneEmpty() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <UploadCloud className="h-10 w-10 text-smnyl-text-muted/70 mb-3" />
      <p className="font-medium text-smnyl-text mb-0.5">Arrastra el .xlsx aquí</p>
      <p className="text-xs text-smnyl-text-muted">
        o haz clic para seleccionar el registro Prophet
      </p>
    </div>
  );
}

function FilePreview({ file, onRemove }: { file: File; onRemove: () => void }) {
  return (
    <div className="flex items-center gap-3 p-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-md bg-smnyl-success-soft text-smnyl-success-dark shrink-0">
        <FileSpreadsheet className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-smnyl-text truncate">{file.name}</p>
        <p className="text-xs text-smnyl-text-muted">
          {file.size < 1024 * 1024
            ? `${(file.size / 1024).toFixed(1)} KB`
            : `${(file.size / 1024 / 1024).toFixed(2)} MB`}
        </p>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        aria-label="Quitar archivo"
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}
