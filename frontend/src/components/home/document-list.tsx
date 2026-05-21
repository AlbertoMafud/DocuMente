/**
 * DocumentList — lista de docs con tabs activos/archivados/papelera.
 *
 * Cada tab consulta su propio endpoint con TanStack Query; el cambio de
 * tab es instantáneo (cached) después del primer fetch.
 */
"use client";

import { FileText, Archive, Trash2 } from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { useDocumentos } from "@/lib/api/hooks";
import type { Visibilidad } from "@/lib/api/types";

import { DocumentCard } from "./document-card";

export function DocumentList() {
  return (
    <section className="mt-12">
      <h2 className="font-display text-xl font-semibold text-smnyl-text mb-1">
        Tus documentos
      </h2>
      <p className="text-sm text-smnyl-text-muted mb-4">
        Gestiona tus documentos activos, archivados o en papelera.
      </p>

      <Tabs defaultValue="activos">
        <TabsList>
          <TabsTrigger value="activos">
            <FileText className="mr-1.5 h-3.5 w-3.5" />
            Activos
          </TabsTrigger>
          <TabsTrigger value="archivados">
            <Archive className="mr-1.5 h-3.5 w-3.5" />
            Archivados
          </TabsTrigger>
          <TabsTrigger value="papelera">
            <Trash2 className="mr-1.5 h-3.5 w-3.5" />
            Papelera
          </TabsTrigger>
        </TabsList>

        <TabsContent value="activos">
          <DocumentListPane visibilidad="activos" />
        </TabsContent>
        <TabsContent value="archivados">
          <DocumentListPane visibilidad="archivados" />
        </TabsContent>
        <TabsContent value="papelera">
          <DocumentListPane visibilidad="papelera" />
        </TabsContent>
      </Tabs>
    </section>
  );
}

function DocumentListPane({ visibilidad }: { visibilidad: Visibilidad }) {
  const { data, isLoading, error } = useDocumentos(visibilidad);

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-smnyl-danger/30 bg-smnyl-danger-soft p-6 text-sm">
        <p className="font-medium text-smnyl-danger">No se pudieron cargar los documentos</p>
        <p className="mt-1 text-smnyl-text-muted">
          Verifica que la API esté corriendo en{" "}
          <code className="bg-white px-1.5 py-0.5 rounded text-xs">
            localhost:8001
          </code>
          . Detalle: {(error as Error).message}
        </p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return <EmptyPane visibilidad={visibilidad} />;
  }

  return (
    <div className="space-y-3">
      {data.map((doc) => (
        <DocumentCard
          key={doc.id}
          doc={doc}
          modo={visibilidad === "todos" ? "activos" : visibilidad}
        />
      ))}
    </div>
  );
}

function EmptyPane({ visibilidad }: { visibilidad: Visibilidad }) {
  const contenido = {
    activos: {
      icon: FileText,
      titulo: "Aún no tienes documentos activos",
      descripcion:
        "Crea un documento desde cero con las 28 secciones del template oficial NYL, importa un .docx existente, o inicia una Ficha Prophet.",
    },
    archivados: {
      icon: Archive,
      titulo: "Sin documentos archivados",
      descripcion:
        "Los documentos que archives aparecerán aquí. Archivar no borra: el documento se preserva fuera de la vista principal y puedes desarchivarlo cuando lo necesites.",
    },
    papelera: {
      icon: Trash2,
      titulo: "Papelera vacía",
      descripcion:
        "Los documentos enviados a papelera se eliminan automáticamente tras 30 días si no los restauras. Mientras tanto puedes recuperarlos desde aquí.",
    },
    todos: {
      icon: FileText,
      titulo: "Sin documentos",
      descripcion: "",
    },
  }[visibilidad];

  const Icon = contenido.icon;

  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-smnyl-border bg-smnyl-bg-soft/50 px-6 py-16 text-center">
      <Icon className="h-10 w-10 text-smnyl-text-muted/60 mb-4" />
      <h3 className="font-display text-lg font-semibold text-smnyl-text mb-2">
        {contenido.titulo}
      </h3>
      <p className="max-w-md text-sm text-smnyl-text-muted leading-relaxed">
        {contenido.descripcion}
      </p>
    </div>
  );
}
