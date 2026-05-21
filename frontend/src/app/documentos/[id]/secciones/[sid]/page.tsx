/**
 * Editor inline de una sección — textarea markdown + preview en vivo.
 *
 * Layout split: editor a la izquierda, preview a la derecha. Indicador
 * "Guardado hace X" cuando ya existe contenido previo.
 */
"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Save, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useDocumento, useEditarSeccion, useSeccion } from "@/lib/api/hooks";
import { tiempoRelativo } from "@/lib/utils";

export default function EditarSeccionPage() {
  const { id, sid } = useParams<{ id: string; sid: string }>();
  const router = useRouter();
  const docQuery = useDocumento(id);
  const seccionQuery = useSeccion(id, decodeURIComponent(sid));
  const editar = useEditarSeccion();

  const [contenido, setContenido] = useState<string>("");
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (!initialized && seccionQuery.data) {
      setContenido(seccionQuery.data.contenido ?? "");
      setInitialized(true);
    }
  }, [seccionQuery.data, initialized]);

  if (docQuery.isLoading || seccionQuery.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-14 w-full max-w-2xl" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!docQuery.data || !seccionQuery.data) {
    return (
      <div className="rounded-lg border border-smnyl-danger/40 bg-smnyl-danger-soft p-6 max-w-xl">
        <p className="text-sm text-smnyl-danger font-medium">
          No se encontró el documento o la sección.
        </p>
      </div>
    );
  }

  const doc = docQuery.data;
  const seccion = seccionQuery.data;
  const nombre = doc.metadata_modelo.nombre_modelo || "Documento sin nombre";

  function handleSave() {
    editar.mutate(
      { docId: id, sid: decodeURIComponent(sid), contenido },
      {
        onSuccess: () => {
          toast.success("Cambios guardados.");
          router.push(`/documentos/${id}`);
        },
        onError: (err) => toast.error(`Error: ${(err as Error).message}`),
      },
    );
  }

  return (
    <div className="space-y-5">
      <Button variant="ghost" size="sm" asChild>
        <Link href={`/documentos/${id}`}>
          <ArrowLeft className="mr-1 h-3.5 w-3.5" />
          Volver al dashboard
        </Link>
      </Button>

      <div className="animate-fade-in">
        <div className="flex items-baseline gap-3 flex-wrap mb-1">
          <h1 className="font-display text-3xl font-semibold text-smnyl-text">
            {seccion.numero} {seccion.nombre}
          </h1>
          {seccion.contenido && doc.actualizado_en && (
            <span className="text-xs italic text-smnyl-text-muted">
              · Guardado {tiempoRelativo(doc.actualizado_en)}
            </span>
          )}
        </div>
        <p className="text-sm text-smnyl-text-muted">
          <span className="font-medium text-smnyl-text">{nombre}</span> ·{" "}
          {seccion.intencion || "Edita el contenido en markdown. El preview se actualiza en vivo."}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 animate-fade-in">
        <div className="space-y-2">
          <Label>Editor (markdown)</Label>
          <Textarea
            value={contenido}
            onChange={(e) => setContenido(e.target.value)}
            rows={22}
            placeholder="Escribe el contenido en markdown — **negritas**, *cursivas*, listas con `- `, tablas con pipes…"
            className="font-mono text-sm leading-relaxed"
          />
          <div className="text-xs text-smnyl-text-muted flex justify-between">
            <span>{contenido.length} caracteres</span>
            <span>
              {contenido.length === 0
                ? "Estado: vacía"
                : contenido.length < 200
                  ? "Estado: parcial (<200 chars)"
                  : "Estado: completa"}
            </span>
          </div>
        </div>

        <div className="space-y-2">
          <Label>Preview en vivo</Label>
          <Card className="p-5 min-h-[480px] prose prose-sm max-w-none overflow-auto">
            {contenido.trim() ? (
              <pre className="whitespace-pre-wrap text-sm font-body leading-relaxed text-smnyl-text">
                {contenido}
              </pre>
            ) : (
              <p className="text-sm italic text-smnyl-text-muted">
                (sin contenido — el preview se actualiza al escribir)
              </p>
            )}
          </Card>
        </div>
      </div>

      <div className="flex gap-3 pt-4">
        <Button size="lg" onClick={handleSave} disabled={editar.isPending}>
          {editar.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Guardar cambios
        </Button>
        <Button variant="ghost" size="lg" asChild>
          <Link href={`/documentos/${id}`}>Cancelar</Link>
        </Button>
      </div>
    </div>
  );
}
