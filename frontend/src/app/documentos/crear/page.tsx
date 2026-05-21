/**
 * Crear nuevo documento — formulario simple con dos opciones:
 * MRM Model Development (28 secciones NYL) o Ficha Prophet (12 secciones).
 *
 * Opcionalmente acepta fuentes (PDF, DOCX, XLSX, CSV, TXT) para que el
 * LLM pre-pueble secciones con borradores automáticos. Solo para tipo
 * Model Development en esta primera versión.
 */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, FileText, Sparkles, Loader2 } from "lucide-react";
import { toast } from "sonner";

import type { TipoDocumento } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DropZone } from "@/components/upload/dropzone";
import { useCrearDocumento, useCrearDocumentoConFuentes } from "@/lib/api/hooks";

const FUENTES_ACCEPT = ".pdf,.docx,.xlsx,.xls,.csv,.txt";

export default function CrearDocumentoPage() {
  const router = useRouter();
  const [tipo, setTipo] = useState<TipoDocumento>("model_development");
  const [nombre, setNombre] = useState("");
  const [fuentes, setFuentes] = useState<File[]>([]);
  const [describirImagenes, setDescribirImagenes] = useState(false);
  const crear = useCrearDocumento();
  const crearConFuentes = useCrearDocumentoConFuentes();

  const isPending = crear.isPending || crearConFuentes.isPending;
  const puedeUsarFuentes = tipo === "model_development";

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!nombre.trim()) {
      toast.error("Necesito un nombre para el modelo.");
      return;
    }

    // Si hay fuentes y el tipo lo permite, usar el flujo multipart con sugerencias
    if (fuentes.length > 0 && puedeUsarFuentes) {
      const toastId = toast.loading(
        `Procesando ${fuentes.length} fuente${fuentes.length === 1 ? "" : "s"}… ` +
          "Esto puede tardar 30-60s con varias.",
      );
      crearConFuentes.mutate(
        {
          nombre_modelo: nombre.trim(),
          fuentes,
          describir_imagenes: describirImagenes,
        },
        {
          onSuccess: (res) => {
            toast.success(
              `"${res.documento.metadata_modelo.nombre_modelo}" creado.` +
                (res.secciones_prellenadas > 0
                  ? ` ${res.secciones_prellenadas} sección(es) con borrador automático.`
                  : ""),
              { id: toastId },
            );
            if (res.fuentes_descartadas.length > 0) {
              toast.warning(
                `No se pudo leer: ${res.fuentes_descartadas.join(", ")}`,
                { duration: 8000 },
              );
            }
            if (!res.llm_disponible) {
              toast.warning(
                "Fuentes guardadas pero LLM no disponible — sin borradores automáticos.",
                { duration: 8000 },
              );
            }
            router.push(`/documentos/${res.documento.id}`);
          },
          onError: (err) => {
            toast.error(`No se pudo crear: ${(err as Error).message}`, { id: toastId });
          },
        },
      );
      return;
    }

    // Sin fuentes — flujo JSON original
    crear.mutate(
      { tipo, nombre_modelo: nombre.trim() },
      {
        onSuccess: (doc) => {
          toast.success(`"${doc.metadata_modelo.nombre_modelo}" creado.`);
          router.push(`/documentos/${doc.id}`);
        },
        onError: (err) => {
          toast.error(`No se pudo crear: ${(err as Error).message}`);
        },
      },
    );
  }

  return (
    <div className="max-w-3xl">
      <Button variant="ghost" size="sm" asChild className="mb-4">
        <Link href="/">
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Volver a Inicio
        </Link>
      </Button>

      <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-2">
        Crear documento nuevo
      </h1>
      <p className="text-sm text-smnyl-text-muted mb-8 max-w-xl">
        Elige el tipo de documento y dale un nombre. DocuMente generará la estructura del
        template correspondiente; podrás editar la metadata y llenar secciones después.
      </p>

      <form onSubmit={handleSubmit} className="space-y-8 animate-fade-in">
        {/* Tipo de documento — cards seleccionables */}
        <div>
          <Label className="mb-3 block">Tipo de documento</Label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <TipoCard
              icon={FileText}
              titulo="Model Development"
              descripcion="28 secciones del template oficial NYL — para modelos sujetos al marco MRM."
              selected={tipo === "model_development"}
              onClick={() => setTipo("model_development")}
            />
            <TipoCard
              icon={Sparkles}
              titulo="Ficha Prophet"
              descripcion="12 secciones del registro de Modelos Actuariales — más ligera, formato tabular."
              selected={tipo === "prophet"}
              onClick={() => setTipo("prophet")}
            />
          </div>
        </div>

        {/* Nombre */}
        <div className="space-y-2 max-w-md">
          <Label htmlFor="nombre">Nombre del modelo</Label>
          <Input
            id="nombre"
            placeholder="Ej. Value of New Business — GMM"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            autoFocus
          />
          <p className="text-xs text-smnyl-text-muted">
            Puedes editarlo después junto con el resto de metadata.
          </p>
        </div>

        {/* Fuentes opcionales — solo Model Development por ahora */}
        {puedeUsarFuentes && (
          <div className="space-y-2">
            <Label>
              Fuentes adicionales{" "}
              <span className="text-smnyl-text-muted font-normal">(opcional)</span>
            </Label>
            <p className="text-xs text-smnyl-text-muted">
              PDFs, Word, Excel, CSV o TXT con información del modelo. Si subes algo,
              Claude lo leerá y propondrá borradores automáticos para las secciones
              aplicables. No necesitas que sea un documento institucional formal —
              instructivos o notas también sirven.
            </p>
            <DropZone
              accept={FUENTES_ACCEPT}
              multiple
              files={fuentes}
              onChange={setFuentes}
              titulo="Arrastra archivos aquí"
              subtitulo="PDF, DOCX, XLSX, CSV, TXT — varios OK"
            />
            {fuentes.length > 0 && (
              <label className="flex items-start gap-2 pt-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={describirImagenes}
                  onChange={(e) => setDescribirImagenes(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-smnyl-border text-smnyl-primary focus:ring-smnyl-primary"
                />
                <span className="text-xs text-smnyl-text-muted leading-relaxed">
                  <span className="font-medium text-smnyl-text">
                    Describir imágenes embebidas con IA
                  </span>
                  <br />
                  Procesa screenshots, flowcharts y diagramas con Claude
                  Vision (Haiku). Agrega ~2-5s por imagen y costo marginal
                  (~$0.001-0.005 c/u). Útil para docs con capturas de
                  Prophet, Excel o sistemas. Resultados se cachean por hash.
                </span>
              </label>
            )}
          </div>
        )}

        {/* Submit */}
        <div className="flex gap-3 pt-2">
          <Button type="submit" size="lg" disabled={isPending}>
            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {fuentes.length > 0 && puedeUsarFuentes
              ? `Crear con ${fuentes.length} fuente${fuentes.length === 1 ? "" : "s"}`
              : "Crear documento"}
          </Button>
          <Button type="button" variant="ghost" size="lg" asChild>
            <Link href="/">Cancelar</Link>
          </Button>
        </div>
      </form>
    </div>
  );
}

interface TipoCardProps {
  icon: React.ComponentType<{ className?: string }>;
  titulo: string;
  descripcion: string;
  selected: boolean;
  onClick: () => void;
}

function TipoCard({ icon: Icon, titulo, descripcion, selected, onClick }: TipoCardProps) {
  return (
    <button type="button" onClick={onClick} className="text-left">
      <Card
        className={`
          p-5 h-full cursor-pointer transition-all duration-200 ease-out
          ${selected
            ? "border-smnyl-primary bg-smnyl-accent-soft/15 ring-2 ring-smnyl-primary/20 shadow-smnyl-md"
            : "hover:border-smnyl-accent-soft hover:shadow-smnyl-md"}
        `}
      >
        <div
          className={`inline-flex h-9 w-9 items-center justify-center rounded-md mb-3
            ${selected ? "bg-smnyl-primary text-white" : "bg-smnyl-bg-soft text-smnyl-primary"}`}
        >
          <Icon className="h-4 w-4" />
        </div>
        <h3 className="font-display text-base font-semibold text-smnyl-text mb-1">{titulo}</h3>
        <p className="text-xs text-smnyl-text-muted leading-relaxed">{descripcion}</p>
      </Card>
    </button>
  );
}
