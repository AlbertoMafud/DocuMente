/**
 * Crear nuevo documento — formulario simple con dos opciones:
 * MRM Model Development (28 secciones NYL) o Ficha Prophet (12 secciones).
 *
 * Opcionalmente acepta fuentes (PDF, DOCX, XLSX, CSV, TXT) para que el
 * LLM pre-pueble secciones con borradores automáticos. Solo para tipo
 * Model Development en esta primera versión.
 *
 * Cuando hay fuentes, usa el endpoint SSE `/crear-con-fuentes/stream`
 * para mostrar progreso en vivo (S17) en lugar de esperar 10 min en
 * blanco.
 */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, FileText, Sparkles, Loader2, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

import type { TipoDocumento } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { DropZone } from "@/components/upload/dropzone";
import { documentosApi } from "@/lib/api/client";
import { useCrearDocumento } from "@/lib/api/hooks";

const FUENTES_ACCEPT = ".pdf,.docx,.xlsx,.xls,.csv,.txt";

interface SeccionCompletada {
  id: string;
  numero: string;
  nombre: string;
  estado: "poblada" | "sin_info" | "error";
}

interface ProgressState {
  fase: "extrayendo" | "creando" | "procesando" | "done" | "error";
  documentoId?: string;
  totalSecciones?: number;
  secciones: SeccionCompletada[];
  total: number;
  inicio: number;
}

export default function CrearDocumentoPage() {
  const router = useRouter();
  const [tipo, setTipo] = useState<TipoDocumento>("model_development");
  const [nombre, setNombre] = useState("");
  const [fuentes, setFuentes] = useState<File[]>([]);
  const [describirImagenes, setDescribirImagenes] = useState(false);
  const [progress, setProgress] = useState<ProgressState | null>(null);
  const crear = useCrearDocumento();

  const isPending = crear.isPending || progress !== null;
  const puedeUsarFuentes = tipo === "model_development";

  async function handleSubmitConStream() {
    setProgress({
      fase: "extrayendo",
      secciones: [],
      total: 0,
      inicio: Date.now(),
    });

    try {
      const iter = documentosApi.crearConFuentesStream(
        nombre.trim(),
        fuentes,
        "default",
        describirImagenes,
      );

      let documentoIdFinal: string | null = null;

      for await (const evt of iter) {
        if (evt.event === "created") {
          const data = evt.data as {
            documento_id: string;
            total_secciones: number;
            fuentes_extraidas: number;
            fuentes_descartadas: string[];
          };
          documentoIdFinal = data.documento_id;
          setProgress((p) =>
            p
              ? {
                  ...p,
                  fase: "procesando",
                  documentoId: data.documento_id,
                  totalSecciones: data.total_secciones,
                }
              : p,
          );
          if (data.fuentes_descartadas.length > 0) {
            toast.warning(
              `No se pudo leer: ${data.fuentes_descartadas.join(", ")}`,
              { duration: 8000 },
            );
          }
        } else if (evt.event === "progress") {
          const data = evt.data as {
            seccion_id: string;
            seccion_numero: string;
            seccion_nombre: string;
            completadas: number;
            total: number;
            estado: "poblada" | "sin_info" | "error";
          };
          setProgress((p) =>
            p
              ? {
                  ...p,
                  total: data.total,
                  secciones: [
                    ...p.secciones,
                    {
                      id: data.seccion_id,
                      numero: data.seccion_numero,
                      nombre: data.seccion_nombre,
                      estado: data.estado,
                    },
                  ],
                }
              : p,
          );
        } else if (evt.event === "done") {
          const data = evt.data as {
            documento_id: string;
            secciones_prellenadas: number;
            advertencias: string[];
            llm_disponible: boolean;
          };
          documentoIdFinal = data.documento_id;
          setProgress((p) => (p ? { ...p, fase: "done" } : p));
          toast.success(
            `Documento creado.` +
              (data.secciones_prellenadas > 0
                ? ` ${data.secciones_prellenadas} sección(es) con borrador automático.`
                : ""),
          );
          if (!data.llm_disponible && fuentes.length > 0) {
            toast.warning("LLM no disponible — sin borradores automáticos.", {
              duration: 8000,
            });
          }
          for (const adv of data.advertencias) {
            toast.warning(adv, { duration: 8000 });
          }
          // Navegación tras una pausa breve para que el usuario vea el "done"
          setTimeout(() => router.push(`/documentos/${data.documento_id}`), 800);
          return;
        } else if (evt.event === "error") {
          const data = evt.data as { detail: string };
          throw new Error(data.detail || "Error desconocido");
        }
      }

      // Si el stream terminó sin "done", aún así navegamos si tenemos id
      if (documentoIdFinal) {
        router.push(`/documentos/${documentoIdFinal}`);
      }
    } catch (err) {
      setProgress({
        fase: "error",
        secciones: progress?.secciones ?? [],
        total: progress?.total ?? 0,
        inicio: progress?.inicio ?? Date.now(),
      });
      toast.error(`No se pudo crear: ${(err as Error).message}`);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!nombre.trim()) {
      toast.error("Necesito un nombre para el modelo.");
      return;
    }

    // Si hay fuentes y el tipo lo permite, usar streaming
    if (fuentes.length > 0 && puedeUsarFuentes) {
      void handleSubmitConStream();
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

      {progress && <ProgressPanel state={progress} />}

      <form
        onSubmit={handleSubmit}
        className={`space-y-8 animate-fade-in ${progress ? "opacity-50 pointer-events-none" : ""}`}
      >
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

function ProgressPanel({ state }: { state: ProgressState }) {
  const completadas = state.secciones.length;
  const pct = state.total > 0 ? Math.round((completadas / state.total) * 100) : 0;
  const tiempoMs = Date.now() - state.inicio;
  const segundos = Math.floor(tiempoMs / 1000);
  const ritmoSeg = completadas > 0 ? tiempoMs / 1000 / completadas : 0;
  const restantes = Math.max(0, state.total - completadas);
  const etaSeg = Math.round(restantes * ritmoSeg);

  const labelFase = {
    extrayendo: "Subiendo y extrayendo texto de las fuentes…",
    creando: "Guardando documento en blanco…",
    procesando:
      state.total > 0
        ? `Procesando con IA (${completadas} de ${state.total})…`
        : "Iniciando IA…",
    done: "¡Listo! Redirigiendo al dashboard…",
    error: "Algo falló — revisa abajo.",
  }[state.fase];

  return (
    <Card className="p-6 mb-8 bg-smnyl-bg-soft/40 border-smnyl-primary/30">
      <div className="flex items-center gap-3 mb-3">
        {state.fase === "done" ? (
          <CheckCircle2 className="h-6 w-6 text-smnyl-success" />
        ) : (
          <Loader2 className="h-6 w-6 text-smnyl-primary animate-spin" />
        )}
        <div className="flex-1">
          <p className="text-sm font-medium text-smnyl-text">{labelFase}</p>
          {state.fase === "procesando" && etaSeg > 0 && (
            <p className="text-xs text-smnyl-text-muted">
              Llevamos {segundos}s · ETA ~{Math.floor(etaSeg / 60)}m {etaSeg % 60}s
            </p>
          )}
          {state.fase === "procesando" && etaSeg === 0 && completadas === 0 && (
            <p className="text-xs text-smnyl-text-muted">
              Calculando tiempo restante…
            </p>
          )}
        </div>
      </div>

      {state.total > 0 && (
        <Progress value={pct} className="mb-4" />
      )}

      {/* Lista de secciones completadas — animación al irse llenando */}
      {state.secciones.length > 0 && (
        <div className="space-y-1 max-h-64 overflow-y-auto">
          <p className="text-xs font-semibold uppercase tracking-wider text-smnyl-text-muted mb-2">
            Secciones procesadas
          </p>
          {state.secciones.map((s) => (
            <div
              key={s.id}
              className="flex items-center gap-2 text-sm text-smnyl-text animate-fade-in"
            >
              {s.estado === "poblada" && (
                <CheckCircle2 className="h-3.5 w-3.5 text-smnyl-success shrink-0" />
              )}
              {s.estado === "sin_info" && (
                <span className="h-3.5 w-3.5 rounded-full bg-smnyl-text-muted/30 shrink-0" />
              )}
              {s.estado === "error" && (
                <span className="h-3.5 w-3.5 rounded-full bg-smnyl-danger shrink-0" />
              )}
              <span className="font-mono text-xs text-smnyl-text-muted shrink-0">
                {s.numero}
              </span>
              <span className="truncate">{s.nombre}</span>
              {s.estado === "sin_info" && (
                <span className="text-xs text-smnyl-text-muted italic shrink-0">
                  (sin info en fuentes)
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
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
