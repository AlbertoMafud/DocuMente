/**
 * DropZone — área de drag-and-drop reutilizable.
 *
 * Originalmente vivía inline en /importar/page.tsx. Extraído a componente
 * compartido cuando /crear ganó la opción de subir fuentes adicionales.
 *
 * Acepta uno o múltiples archivos. El consumidor decide qué tipos vía
 * `accept` (string CSV de extensiones, ej. ".pdf,.docx,.xlsx").
 */
"use client";

import { useCallback, useRef, useState } from "react";
import { FileText, FilePlus2, UploadCloud, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

type FileType = "docx" | "pdf" | "xlsx" | "csv" | "txt" | "otro";

function getType(filename: string): FileType {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "docx" || ext === "doc") return "docx";
  if (ext === "pdf") return "pdf";
  if (ext === "xlsx" || ext === "xls") return "xlsx";
  if (ext === "csv") return "csv";
  if (ext === "txt") return "txt";
  return "otro";
}

interface DropZoneProps {
  /** Extensiones aceptadas separadas por coma, ej. ".docx,.pdf,.xlsx" */
  accept: string;
  /** Si true, permite varios archivos; default false (solo uno) */
  multiple?: boolean;
  /** Archivos seleccionados (controlado por el padre) */
  files: File[];
  /** Callback cuando cambian los archivos */
  onChange: (files: File[]) => void;
  /** Texto principal del CTA */
  titulo?: string;
  /** Texto secundario explicativo */
  subtitulo?: string;
}

export function DropZone({
  accept,
  multiple = false,
  files,
  onChange,
  titulo = multiple ? "Arrastra archivos aquí" : "Arrastra el archivo aquí",
  subtitulo = "o haz clic para seleccionar",
}: DropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = useCallback(
    (newFiles: FileList | null) => {
      if (!newFiles) return;
      const list = Array.from(newFiles);
      if (multiple) {
        onChange([...files, ...list]);
      } else {
        onChange(list.slice(0, 1));
      }
    },
    [files, multiple, onChange],
  );

  const removeFile = useCallback(
    (index: number) => {
      onChange(files.filter((_, i) => i !== index));
    },
    [files, onChange],
  );

  return (
    <div className="space-y-3">
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={`
          rounded-xl border-2 border-dashed cursor-pointer
          transition-all duration-200 ease-out
          ${
            dragOver
              ? "border-smnyl-primary bg-smnyl-accent-soft/30"
              : "border-smnyl-border hover:border-smnyl-accent-soft hover:bg-smnyl-bg-soft/40"
          }
        `}
      >
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <UploadCloud className="h-8 w-8 text-smnyl-text-muted/70 mb-2" />
          <p className="font-medium text-smnyl-text mb-0.5 text-sm">{titulo}</p>
          <p className="text-xs text-smnyl-text-muted">{subtitulo}</p>
        </div>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((f, i) => (
            <Card key={`${f.name}-${i}`} className="p-3">
              <FilePreview
                name={f.name}
                sizeKB={f.size / 1024}
                type={getType(f.name)}
                onRemove={() => removeFile(i)}
              />
            </Card>
          ))}
        </div>
      )}
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
    <div className="flex items-center gap-3">
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
