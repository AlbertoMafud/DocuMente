/**
 * Apéndices del documento — listado + upload de tabla/PDF/fórmula.
 *
 * El usuario elige una sección destino + el tipo de apéndice. Cada apéndice
 * queda vinculado a su sección y se embebe en el .docx final al exportar.
 */
"use client";

import { useCallback, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Paperclip,
  FileSpreadsheet,
  FilePlus2,
  Sigma,
  X,
  Loader2,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";

import type { Apendice, Seccion } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  useAdjuntarFormula,
  useAdjuntarPdf,
  useAdjuntarTabla,
  useApendices,
  useBorrarApendice,
  useDocumento,
} from "@/lib/api/hooks";

type Tipo = "tabla" | "pdf" | "formula";

export default function ApendicesPage() {
  const { id } = useParams<{ id: string }>();
  const docQuery = useDocumento(id);
  const apendicesQuery = useApendices(id);

  if (docQuery.isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }
  if (!docQuery.data) {
    return <p className="text-sm text-smnyl-danger">No se pudo cargar.</p>;
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <Button variant="ghost" size="sm" asChild>
        <Link href={`/documentos/${id}`}>
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Volver al dashboard
        </Link>
      </Button>

      <div>
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-primary/10 text-smnyl-primary mb-3">
          <Paperclip className="h-5 w-5" />
        </div>
        <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-2">
          Apéndices
        </h1>
        <p className="text-sm text-smnyl-text-muted max-w-2xl">
          Archivos auxiliares que se embeberán en el .docx final: tablas Excel/CSV,
          páginas de PDFs y fórmulas LaTeX renderizadas como imagen.
        </p>
      </div>

      <UploaderCard documentoId={id} secciones={docQuery.data.secciones} />

      <section>
        <h2 className="font-display text-lg font-semibold text-smnyl-text mb-3">
          {apendicesQuery.data?.length ?? 0} apéndice
          {apendicesQuery.data?.length === 1 ? "" : "s"}
        </h2>
        {apendicesQuery.isLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : apendicesQuery.data && apendicesQuery.data.length > 0 ? (
          <div className="space-y-2">
            {apendicesQuery.data.map((ap) => (
              <ApendiceRow
                key={ap.id}
                apendice={ap}
                documentoId={id}
                secciones={docQuery.data!.secciones}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-smnyl-border bg-smnyl-bg-soft/40 px-6 py-10 text-center">
            <p className="text-sm text-smnyl-text-muted">
              Sin apéndices todavía. Sube uno arriba.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}

function UploaderCard({
  documentoId,
  secciones,
}: {
  documentoId: string;
  secciones: Seccion[];
}) {
  const [tipo, setTipo] = useState<Tipo>("tabla");
  const [seccionId, setSeccionId] = useState<string>(secciones[0]?.id ?? "");
  const [titulo, setTitulo] = useState("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [latex, setLatex] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const tabla = useAdjuntarTabla();
  const pdf = useAdjuntarPdf();
  const formula = useAdjuntarFormula();

  const cargando = tabla.isPending || pdf.isPending || formula.isPending;

  const handleFile = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;
    setArchivo(files[0]);
  }, []);

  function reset() {
    setArchivo(null);
    setLatex("");
    setTitulo("");
  }

  function handleSubmit() {
    if (!seccionId) {
      toast.error("Elige una sección destino.");
      return;
    }
    if (tipo === "tabla") {
      if (!archivo) return toast.error("Selecciona el archivo Excel/CSV.");
      if (!titulo.trim()) return toast.error("El título base es requerido.");
      tabla.mutate(
        { docId: documentoId, sid: seccionId, archivo, titulo_base: titulo.trim() },
        {
          onSuccess: (aps) => {
            toast.success(`${aps.length} apéndice(s) creado(s).`);
            reset();
          },
          onError: (err) => toast.error(`Error: ${(err as Error).message}`),
        },
      );
    } else if (tipo === "pdf") {
      if (!archivo) return toast.error("Selecciona el PDF.");
      if (!titulo.trim()) return toast.error("El título es requerido.");
      pdf.mutate(
        { docId: documentoId, sid: seccionId, archivo, titulo: titulo.trim() },
        {
          onSuccess: () => {
            toast.success("Apéndice PDF creado.");
            reset();
          },
          onError: (err) => toast.error(`Error: ${(err as Error).message}`),
        },
      );
    } else {
      if (!latex.trim()) return toast.error("Pega la fórmula LaTeX.");
      if (!titulo.trim()) return toast.error("El título es requerido.");
      formula.mutate(
        {
          docId: documentoId,
          sid: seccionId,
          latex_source: latex,
          titulo: titulo.trim(),
        },
        {
          onSuccess: () => {
            toast.success("Fórmula LaTeX adjuntada.");
            reset();
          },
          onError: (err) => toast.error(`Error: ${(err as Error).message}`),
        },
      );
    }
  }

  const accept = tipo === "tabla" ? ".xlsx,.xls,.csv" : tipo === "pdf" ? ".pdf" : "";

  return (
    <Card className="p-5 animate-fade-in">
      <Tabs value={tipo} onValueChange={(v) => setTipo(v as Tipo)}>
        <TabsList>
          <TabsTrigger value="tabla">
            <FileSpreadsheet className="mr-1.5 h-3.5 w-3.5" />
            Tabla (Excel/CSV)
          </TabsTrigger>
          <TabsTrigger value="pdf">
            <FilePlus2 className="mr-1.5 h-3.5 w-3.5" />
            PDF
          </TabsTrigger>
          <TabsTrigger value="formula">
            <Sigma className="mr-1.5 h-3.5 w-3.5" />
            Fórmula LaTeX
          </TabsTrigger>
        </TabsList>

        <TabsContent value="tabla" className="space-y-4">
          <SeccionPicker
            secciones={secciones}
            value={seccionId}
            onChange={setSeccionId}
          />
          <div className="space-y-2">
            <Label>Título base</Label>
            <Input
              placeholder="Ej. Tabla de mortalidad SOA 2017"
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
            />
            <p className="text-xs text-smnyl-text-muted">
              Si el Excel tiene múltiples hojas, cada apéndice tendrá el sufijo
              {" "}&ldquo; — {"<"}nombre hoja{">"}&rdquo;.
            </p>
          </div>
          <FilePickerInline file={archivo} onChange={setArchivo} accept={accept} inputRef={inputRef} onClick={() => inputRef.current?.click()} onFiles={handleFile} />
        </TabsContent>

        <TabsContent value="pdf" className="space-y-4">
          <SeccionPicker
            secciones={secciones}
            value={seccionId}
            onChange={setSeccionId}
          />
          <div className="space-y-2">
            <Label>Título del apéndice</Label>
            <Input
              placeholder="Ej. Diagrama de flujo del proceso de runs"
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
            />
          </div>
          <FilePickerInline file={archivo} onChange={setArchivo} accept={accept} inputRef={inputRef} onClick={() => inputRef.current?.click()} onFiles={handleFile} />
        </TabsContent>

        <TabsContent value="formula" className="space-y-4">
          <SeccionPicker
            secciones={secciones}
            value={seccionId}
            onChange={setSeccionId}
          />
          <div className="space-y-2">
            <Label>Título de la fórmula</Label>
            <Input
              placeholder="Ej. Reserva técnica formal"
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>LaTeX</Label>
            <Textarea
              rows={5}
              placeholder="R_t = \\sum_{i=0}^{n} v^i \\cdot p_i \\cdot B_i"
              value={latex}
              onChange={(e) => setLatex(e.target.value)}
              className="font-mono text-sm"
            />
            <p className="text-xs text-smnyl-text-muted">
              Se renderea como imagen al exportar — sin entornos {"$$ ... $$"}, solo
              la expresión.
            </p>
          </div>
        </TabsContent>
      </Tabs>

      <div className="mt-5 flex gap-2">
        <Button onClick={handleSubmit} disabled={cargando}>
          {cargando && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Adjuntar
        </Button>
      </div>
    </Card>
  );
}

function SeccionPicker({
  secciones,
  value,
  onChange,
}: {
  secciones: Seccion[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label>Sección destino</Label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="
          flex h-10 w-full rounded-md border border-smnyl-border bg-white px-3 text-sm
          transition-all duration-200 ease-out
          focus-visible:outline-none focus-visible:border-smnyl-primary
          focus-visible:ring-2 focus-visible:ring-smnyl-primary/15
        "
      >
        {secciones.map((s) => (
          <option key={s.id} value={s.id}>
            {s.numero} {s.nombre}
          </option>
        ))}
      </select>
    </div>
  );
}

function FilePickerInline({
  file,
  onChange,
  accept,
  inputRef,
  onClick,
  onFiles,
}: {
  file: File | null;
  onChange: (f: File | null) => void;
  accept: string;
  inputRef: React.RefObject<HTMLInputElement>;
  onClick: () => void;
  onFiles: (files: FileList | null) => void;
}) {
  return (
    <div className="space-y-2">
      <Label>Archivo</Label>
      {file ? (
        <div className="flex items-center gap-3 rounded-md border border-smnyl-border bg-smnyl-bg-soft/30 p-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-white text-smnyl-primary">
            <FilePlus2 className="h-4 w-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-smnyl-text truncate">{file.name}</p>
            <p className="text-xs text-smnyl-text-muted">
              {(file.size / 1024).toFixed(1)} KB
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onChange(null)}
            aria-label="Quitar"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      ) : (
        <>
          <Button variant="outline" onClick={onClick}>
            <FilePlus2 className="mr-1 h-4 w-4" />
            Seleccionar archivo
          </Button>
          <input
            ref={inputRef}
            type="file"
            accept={accept}
            className="hidden"
            onChange={(e) => onFiles(e.target.files)}
          />
        </>
      )}
    </div>
  );
}

function ApendiceRow({
  apendice,
  documentoId,
  secciones,
}: {
  apendice: Apendice;
  documentoId: string;
  secciones: Seccion[];
}) {
  const seccionOrigen = secciones.find((s) => s.id === apendice.seccion_origen_id);
  const borrar = useBorrarApendice();
  const Icon =
    apendice.tipo === "tabla" ? FileSpreadsheet :
    apendice.tipo === "pdf" ? FilePlus2 :
    Sigma;

  return (
    <Card className="p-4 smnyl-card-hover">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-accent-soft/40 text-smnyl-primary shrink-0">
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-medium text-smnyl-text truncate">{apendice.titulo}</p>
            <Badge variant="secondary">{apendice.tipo}</Badge>
          </div>
          <p className="text-xs text-smnyl-text-muted mt-0.5">
            Vinculado a{" "}
            <span className="font-medium text-smnyl-text">
              {seccionOrigen
                ? `${seccionOrigen.numero} ${seccionOrigen.nombre}`
                : apendice.seccion_origen_id}
            </span>
            {apendice.nombre_archivo_original && (
              <>
                {" · "}
                <code className="bg-smnyl-bg-soft px-1.5 py-0.5 rounded text-[0.7rem]">
                  {apendice.nombre_archivo_original}
                </code>
              </>
            )}
          </p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Borrar apéndice"
          onClick={() =>
            borrar.mutate(
              { docId: documentoId, apendiceId: apendice.id },
              {
                onSuccess: () => toast.success("Apéndice eliminado."),
                onError: (err) => toast.error(`Error: ${(err as Error).message}`),
              },
            )
          }
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </Card>
  );
}
