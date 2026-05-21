/**
 * Vista previa de una versión histórica (read-only).
 *
 * Renderiza el documento tal como estaba en vN, sin tocar el activo.
 * Reusa el componente Markdown del preview activo. El usuario puede
 * regresar a /versiones o decidir descargar/restaurar desde ahí.
 */
"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, FileText, History } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { Seccion } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useVerVersion } from "@/lib/api/hooks";

export default function VerVersionPage() {
  const { id, numero } = useParams<{ id: string; numero: string }>();
  const numeroVersion = parseInt(numero, 10);
  const query = useVerVersion(id, isNaN(numeroVersion) ? null : numeroVersion);

  if (query.isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }

  if (!query.data) {
    return (
      <div className="rounded-lg border border-smnyl-danger/40 bg-smnyl-danger-soft p-6 max-w-xl">
        <p className="text-sm text-smnyl-danger font-medium">
          No se encontró la versión v{numero} de este documento.
        </p>
      </div>
    );
  }

  const doc = query.data;
  const nombre = doc.metadata_modelo.nombre_modelo || "Documento sin nombre";

  return (
    <div className="space-y-6 max-w-5xl">
      <Button variant="ghost" size="sm" asChild>
        <Link href={`/documentos/${id}/versiones`}>
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Volver a versiones
        </Link>
      </Button>

      <div className="rounded-md border border-smnyl-info/40 bg-smnyl-info-soft p-3 flex items-start gap-2">
        <History className="h-4 w-4 text-smnyl-info-dark mt-0.5 shrink-0" />
        <p className="text-xs text-smnyl-info-dark leading-relaxed">
          <strong>Versión histórica v{numero} (read-only).</strong> Estás
          viendo el snapshot inmutable. El documento activo NO se ha
          modificado. Para descargar este DOCX o restaurar el documento
          a este estado, usa los botones en{" "}
          <Link
            href={`/documentos/${id}/versiones`}
            className="text-smnyl-primary hover:underline font-medium"
          >
            la pantalla de versiones
          </Link>
          .
        </p>
      </div>

      <div>
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-primary/10 text-smnyl-primary mb-3">
          <FileText className="h-5 w-5" />
        </div>
        <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-1">
          {nombre} — v{numero}
        </h1>
        <p className="text-sm text-smnyl-text-muted">
          Estado en ese momento: <strong>{doc.estado}</strong>
          {" · "}
          {doc.secciones.length} secciones del template
        </p>
      </div>

      <Card className="p-10 lg:p-14 bg-white shadow-smnyl-md animate-fade-in">
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
            Versión: <strong>v{numero}</strong> · Snapshot inmutable
          </p>
        </div>

        {doc.secciones.map((s) => (
          <SeccionPreview key={s.id} seccion={s} />
        ))}
      </Card>
    </div>
  );
}

function SeccionPreview({ seccion }: { seccion: Seccion }) {
  return (
    <section className="mt-10 first:mt-0">
      <div className="flex items-baseline justify-between gap-4 flex-wrap mb-3 pb-2 border-b border-smnyl-border/60">
        <h2 className="font-display text-2xl font-semibold text-smnyl-text">
          {seccion.numero} {seccion.nombre}
        </h2>
        {seccion.completitud === "omitida" && (
          <Badge variant="secondary">Omitida</Badge>
        )}
      </div>
      {seccion.contenido ? (
        <div
          className="
            prose prose-sm max-w-none font-body text-smnyl-text leading-relaxed
            prose-headings:font-display prose-headings:text-smnyl-text
            prose-strong:text-smnyl-text prose-strong:font-semibold
            prose-table:text-sm prose-table:border-collapse
            prose-th:border prose-th:border-smnyl-border prose-th:bg-smnyl-bg-soft prose-th:px-3 prose-th:py-2
            prose-td:border prose-td:border-smnyl-border prose-td:px-3 prose-td:py-2
            prose-code:bg-smnyl-bg-soft prose-code:px-1 prose-code:rounded
          "
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{seccion.contenido}</ReactMarkdown>
        </div>
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
        <p className="text-sm italic text-smnyl-text-muted">
          (Sección vacía en este snapshot.)
        </p>
      )}
    </section>
  );
}
