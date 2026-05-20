/**
 * Vista previa del documento completo — todas las secciones concatenadas
 * en un layout tipo paper continuo.
 */
"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, FileText, Download, Edit } from "lucide-react";
import { toast } from "sonner";

import type { Seccion } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDocumento } from "@/lib/api/hooks";
import { exportarApi } from "@/lib/api/client";

export default function VistaPreviaPage() {
  const { id } = useParams<{ id: string }>();
  const docQuery = useDocumento(id);

  async function handleExportar() {
    if (!docQuery.data) return;
    const toastId = toast.loading("Generando DOCX con marca SMNYL…");
    try {
      const blob = await exportarApi.docx(id, {
        idioma_objetivo: "bilingue",
        crear_version: false,
      });
      const nombre = docQuery.data.metadata_modelo.nombre_modelo || "documento";
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${nombre.replace(/\s+/g, "_")}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success("DOCX descargado", { id: toastId });
    } catch (err) {
      toast.error(`Error: ${(err as Error).message}`, { id: toastId });
    }
  }

  if (docQuery.isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }

  if (!docQuery.data) {
    return (
      <p className="text-sm text-smnyl-danger">No se pudo cargar el documento.</p>
    );
  }

  const doc = docQuery.data;
  const nombre = doc.metadata_modelo.nombre_modelo || "Documento sin nombre";

  return (
    <div className="space-y-6 max-w-5xl">
      <Button variant="ghost" size="sm" asChild>
        <Link href={`/documentos/${id}`}>
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Volver al dashboard
        </Link>
      </Button>

      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-primary/10 text-smnyl-primary mb-3">
            <FileText className="h-5 w-5" />
          </div>
          <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-1">
            Vista previa
          </h1>
          <p className="text-sm text-smnyl-text-muted">
            Preview en tiempo real. Para la versión con marca SMNYL completa,{" "}
            <button
              onClick={handleExportar}
              className="text-smnyl-primary hover:underline font-medium"
            >
              exporta a DOCX
            </button>
            .
          </p>
        </div>
        <Button onClick={handleExportar}>
          <Download className="mr-1 h-4 w-4" />
          Exportar DOCX
        </Button>
      </div>

      <Card className="p-10 lg:p-14 bg-white shadow-smnyl-md animate-fade-in">
        {/* Portada */}
        <div className="border-b-2 border-smnyl-primary pb-4 mb-8">
          <p className="text-xs uppercase tracking-wider text-smnyl-text-muted">
            {doc.tipo === "prophet"
              ? "Ficha Prophet — Modelos Actuariales"
              : "Model Development Documentation"}
          </p>
          <h1 className="font-display text-4xl font-semibold text-smnyl-text mt-2">
            {nombre}
          </h1>
          <p className="text-sm text-smnyl-text-muted mt-1">
            Estado: <strong>{doc.estado}</strong> · Versión:{" "}
            {doc.metadata_modelo.current_version || "1.0"} · Generado en tiempo real
          </p>
        </div>

        {/* Secciones */}
        {doc.secciones.map((s, i) => (
          <SeccionPreview
            key={s.id}
            seccion={s}
            documentoId={id}
            idx={i}
          />
        ))}
      </Card>
    </div>
  );
}

interface SeccionPreviewProps {
  seccion: Seccion;
  documentoId: string;
  idx: number;
}

function SeccionPreview({ seccion, documentoId }: SeccionPreviewProps) {
  return (
    <section className="mt-10 first:mt-0">
      <div className="flex items-baseline justify-between gap-4 flex-wrap mb-3 pb-2 border-b border-smnyl-border/60">
        <h2 className="font-display text-2xl font-semibold text-smnyl-text">
          {seccion.numero} {seccion.nombre}
        </h2>
        <div className="flex items-center gap-2">
          {seccion.completitud === "omitida" && (
            <Badge variant="secondary">Omitida</Badge>
          )}
          <Button variant="ghost" size="sm" asChild>
            <Link
              href={`/documentos/${documentoId}/secciones/${encodeURIComponent(seccion.id)}`}
            >
              <Edit className="mr-1 h-3.5 w-3.5" />
              Editar
            </Link>
          </Button>
        </div>
      </div>
      {seccion.contenido ? (
        <pre className="whitespace-pre-wrap font-body text-sm leading-relaxed text-smnyl-text">
          {seccion.contenido}
        </pre>
      ) : seccion.completitud === "omitida" ? (
        <p className="text-sm italic text-smnyl-text-muted">
          Sección marcada como omitida.{" "}
          {seccion.motivo_omision && (
            <>
              Motivo:{" "}
              <span className="text-smnyl-text">{seccion.motivo_omision}</span>
            </>
          )}
        </p>
      ) : (
        <div
          className="rounded-md border-l-4 px-4 py-3"
          style={{
            backgroundColor: "#fdf4ee",
            borderLeftColor: "#544235",
          }}
        >
          <p className="text-sm text-smnyl-text-muted italic">
            Sección {seccion.obligatoria ? "obligatoria" : "opcional"} pendiente. Click{" "}
            <strong>Editar</strong> para llenarla manualmente o usa la entrevista desde el dashboard.
          </p>
        </div>
      )}
    </section>
  );
}
