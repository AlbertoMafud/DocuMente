/**
 * Página de importar documento — drop zone .docx/.pdf ancla + fuentes adicionales.
 *
 * Flujo: usuario arrastra/elige ancla → opcionalmente N fuentes → submit dispara
 * POST /documentos/importar (multipart). Al completar, redirige al dashboard.
 */
"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, FileText, FilePlus2, Loader2, X, UploadCloud } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { importarApi } from "@/lib/api/client";

type FileType = "docx" | "pdf";

const ANCLA_ACCEPT = ".docx,.pdf";
const FUENTES_ACCEPT = ".pdf,.xlsx,.xls,.csv,.txt,.docx";

export default function ImportarPage() {
  const router = useRouter();
  const [ancla, setAncla] = useState<File | null>(null);
  const [fuentes, setFuentes] = useState<File[]>([]);
  const [describirImagenes, setDescribirImagenes] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [dragOver, setDragOver] = useState<"ancla" | "fuentes" | null>(null);
  const anclaInputRef = useRef<HTMLInputElement>(null);
  const fuentesInputRef = useRef<HTMLInputElement>(null);

  const handleAnclaDrop = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;
    const f = files[0];
    const ext = f.name.split(".").pop()?.toLowerCase();
    if (ext !== "docx" && ext !== "pdf") {
      toast.error("El documento ancla debe ser .docx o .pdf.");
      return;
    }
    setAncla(f);
  }, []);

  const handleFuentesDrop = useCallback((files: FileList | null) => {
    if (!files) return;
    const nuevas = Array.from(files);
    setFuentes((prev) => [...prev, ...nuevas]);
  }, []);

  async function handleSubmit() {
    if (!ancla) {
      toast.error("Necesitas un documento ancla.");
      return;
    }
    setSubmitting(true);
    const toastId = toast.loading("Procesando documento — esto puede tardar 10-30s…");
    try {
      const doc = await importarApi.docx(ancla, fuentes, "default", describirImagenes);
      toast.success(`"${doc.metadata_modelo.nombre_modelo || ancla.name}" importado.`, {
        id: toastId,
      });
      router.push(`/documentos/${doc.id}`);
    } catch (err) {
      toast.error(`Error al importar: ${(err as Error).message}`, { id: toastId });
      setSubmitting(false);
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
        <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-2">
          Importar documento existente
        </h1>
        <p className="text-sm text-smnyl-text-muted max-w-xl">
          Sube un archivo <code className="px-1 py-0.5 rounded bg-smnyl-bg-soft text-xs">.docx</code>{" "}
          o <code className="px-1 py-0.5 rounded bg-smnyl-bg-soft text-xs">.pdf</code> con
          documentación de modelo. DocuMente lo analizará contra el Model Development Template
          oficial de NYL e identificará brechas para que las completes con apoyo de Claude.
        </p>
      </div>

      {/* Ancla */}
      <section className="animate-fade-in">
        <h2 className="font-display text-lg font-semibold text-smnyl-text mb-1">
          1. Documento ancla
        </h2>
        <p className="text-sm text-smnyl-text-muted mb-3">
          El archivo principal — DocuMente parsea su estructura y la mapea al template NYL.
        </p>

        <DropZone
          isOver={dragOver === "ancla"}
          onDrop={(files) => {
            setDragOver(null);
            handleAnclaDrop(files);
          }}
          onDragOver={() => setDragOver("ancla")}
          onDragLeave={() => setDragOver(null)}
          onClick={() => anclaInputRef.current?.click()}
        >
          {ancla ? (
            <FilePreview
              name={ancla.name}
              sizeKB={ancla.size / 1024}
              type={(ancla.name.split(".").pop()?.toLowerCase() as FileType) ?? "docx"}
              onRemove={() => setAncla(null)}
            />
          ) : (
            <DropZoneContent
              titulo="Arrastra el .docx o .pdf aquí"
              subtitulo="o haz clic para seleccionarlo"
            />
          )}
        </DropZone>
        <input
          ref={anclaInputRef}
          type="file"
          accept={ANCLA_ACCEPT}
          className="hidden"
          onChange={(e) => handleAnclaDrop(e.target.files)}
        />
      </section>

      {/* Fuentes adicionales */}
      <section className="animate-fade-in">
        <h2 className="font-display text-lg font-semibold text-smnyl-text mb-1">
          2. Fuentes adicionales <span className="text-smnyl-text-muted font-normal">(opcional)</span>
        </h2>
        <p className="text-sm text-smnyl-text-muted mb-3">
          PDFs, Excel, CSV o TXT con información complementaria. Claude las usará para pre-poblar
          las secciones vacías del documento.
        </p>

        <DropZone
          isOver={dragOver === "fuentes"}
          onDrop={(files) => {
            setDragOver(null);
            handleFuentesDrop(files);
          }}
          onDragOver={() => setDragOver("fuentes")}
          onDragLeave={() => setDragOver(null)}
          onClick={() => fuentesInputRef.current?.click()}
        >
          <DropZoneContent
            titulo="Arrastra archivos adicionales aquí"
            subtitulo="PDF, XLSX, CSV, TXT, DOCX — múltiples archivos OK"
          />
        </DropZone>
        <input
          ref={fuentesInputRef}
          type="file"
          accept={FUENTES_ACCEPT}
          multiple
          className="hidden"
          onChange={(e) => handleFuentesDrop(e.target.files)}
        />

        {fuentes.length > 0 && (
          <div className="mt-3 space-y-2">
            {fuentes.map((f, i) => (
              <Card key={`${f.name}-${i}`} className="p-3">
                <FilePreview
                  name={f.name}
                  sizeKB={f.size / 1024}
                  type={(f.name.split(".").pop()?.toLowerCase() as FileType) ?? "docx"}
                  onRemove={() => setFuentes((prev) => prev.filter((_, j) => j !== i))}
                />
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Checkbox de visión Claude para imágenes embebidas */}
      {ancla && (
        <label className="flex items-start gap-2 cursor-pointer p-3 rounded-md border border-smnyl-border bg-smnyl-bg-soft/30">
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
            Procesa screenshots, flowcharts y diagramas con Claude Vision
            (Haiku). Agrega ~2-5s por imagen y costo marginal
            (~$0.001-0.005 c/u). Útil para docs con capturas de Prophet,
            Excel o sistemas. Resultados se cachean por hash.
          </span>
        </label>
      )}

      <div className="flex gap-3 pt-4">
        <Button size="lg" onClick={handleSubmit} disabled={!ancla || submitting}>
          {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Importar documento
        </Button>
        <Button variant="ghost" size="lg" asChild>
          <Link href="/">Cancelar</Link>
        </Button>
      </div>
    </div>
  );
}

interface DropZoneProps {
  isOver: boolean;
  onDrop: (files: FileList | null) => void;
  onDragOver: () => void;
  onDragLeave: () => void;
  onClick: () => void;
  children: React.ReactNode;
}

function DropZone({ isOver, onDrop, onDragOver, onDragLeave, onClick, children }: DropZoneProps) {
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

function DropZoneContent({ titulo, subtitulo }: { titulo: string; subtitulo: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-center">
      <UploadCloud className="h-10 w-10 text-smnyl-text-muted/70 mb-3" />
      <p className="font-medium text-smnyl-text mb-0.5">{titulo}</p>
      <p className="text-xs text-smnyl-text-muted">{subtitulo}</p>
    </div>
  );
}

interface FilePreviewProps {
  name: string;
  sizeKB: number;
  type: FileType;
  onRemove: () => void;
}

function FilePreview({ name, sizeKB, type, onRemove }: FilePreviewProps) {
  const Icon = type === "pdf" ? FilePlus2 : FileText;
  return (
    <div className="flex items-center gap-3 p-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-md bg-smnyl-bg-soft text-smnyl-primary shrink-0">
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-smnyl-text truncate">{name}</p>
        <p className="text-xs text-smnyl-text-muted">
          {sizeKB < 1024 ? `${sizeKB.toFixed(1)} KB` : `${(sizeKB / 1024).toFixed(2)} MB`}
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
