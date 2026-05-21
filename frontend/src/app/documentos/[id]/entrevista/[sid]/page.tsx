/**
 * Entrevista LLM por sección — chat con DocuMente para llenar la sección.
 *
 * Si no hay estado previo: muestra CTA "Iniciar entrevista" → llama
 * POST /entrevista/iniciar. Si ya hay estado: rehidrata el chat.
 *
 * El send dispara POST /entrevista/responder. El borrador final aparece
 * al cerrar la sección.
 */
"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Send,
  Sparkles,
  Loader2,
  RotateCcw,
  CheckCircle2,
} from "lucide-react";
import { toast } from "sonner";

import type { MensajeEntrevista } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import {
  useDescartarEntrevista,
  useDocumento,
  useEstadoEntrevista,
  useIniciarEntrevista,
  useResponderPregunta,
  useSeccion,
} from "@/lib/api/hooks";

import { ChatBubble } from "@/components/entrevista/chat-bubble";

export default function EntrevistaPage() {
  const { id, sid } = useParams<{ id: string; sid: string }>();
  const router = useRouter();
  const sidDecoded = decodeURIComponent(sid);

  const docQuery = useDocumento(id);
  const seccionQuery = useSeccion(id, sidDecoded);
  const estadoQuery = useEstadoEntrevista(id, sidDecoded);

  const iniciar = useIniciarEntrevista();
  const responder = useResponderPregunta();
  const descartar = useDescartarEntrevista();

  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll al último mensaje cuando llega nueva data
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [estadoQuery.data?.mensajes?.length]);

  if (docQuery.isLoading || seccionQuery.isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }

  if (!docQuery.data || !seccionQuery.data) {
    return (
      <p className="text-sm text-smnyl-danger">No se pudo cargar la sección.</p>
    );
  }

  const seccion = seccionQuery.data;
  const mensajes: MensajeEntrevista[] = estadoQuery.data?.mensajes ?? [];
  const seccionCerrada = estadoQuery.data?.turno?.seccion_cerrada ?? false;
  const noHayEntrevista = estadoQuery.isError || (!estadoQuery.data && !estadoQuery.isLoading);

  function handleSend() {
    if (!input.trim() || responder.isPending) return;
    const respuesta = input;
    setInput("");
    responder.mutate(
      { docId: id, sid: sidDecoded, respuesta },
      {
        onError: (err) => {
          toast.error(`Error: ${(err as Error).message}`);
          setInput(respuesta);  // restaura el input si falló
        },
      },
    );
  }

  function handleIniciar() {
    iniciar.mutate(
      { docId: id, sid: sidDecoded },
      {
        onError: (err) => {
          const msg = (err as Error).message;
          if (msg.includes("503") || msg.toLowerCase().includes("llm")) {
            toast.error(
              "LLM no configurado. Define ANTHROPIC_API_KEY en el backend para iniciar entrevistas.",
            );
          } else {
            toast.error(`Error: ${msg}`);
          }
        },
      },
    );
  }

  function handleDescartar() {
    if (!confirm("¿Descartar la entrevista en curso? Perderás el progreso de esta sesión.")) {
      return;
    }
    descartar.mutate({ docId: id, sid: sidDecoded });
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] space-y-4">
      {/* Header */}
      <div className="space-y-3 shrink-0">
        <Button variant="ghost" size="sm" asChild>
          <Link href={`/documentos/${id}`}>
            <ArrowLeft className="mr-1 h-3.5 w-3.5" />
            Volver al dashboard
          </Link>
        </Button>
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="h-4 w-4 text-smnyl-primary" />
              <span className="text-xs font-bold uppercase tracking-wider text-smnyl-primary">
                Entrevista con DocuMente
              </span>
            </div>
            <h1 className="font-display text-2xl font-semibold text-smnyl-text leading-tight">
              {seccion.numero} {seccion.nombre}
            </h1>
            {seccion.intencion && (
              <p className="text-sm text-smnyl-text-muted mt-1 max-w-2xl">
                {seccion.intencion}
              </p>
            )}
          </div>
          {!noHayEntrevista && (
            <Button variant="outline" size="sm" onClick={handleDescartar}>
              <RotateCcw className="mr-1 h-3.5 w-3.5" />
              Reiniciar
            </Button>
          )}
        </div>
      </div>

      {/* Chat area */}
      {noHayEntrevista ? (
        <EmptyState
          onIniciar={handleIniciar}
          loading={iniciar.isPending}
          preguntasGuia={seccion.preguntas_guia}
        />
      ) : (
        <Card className="flex-1 flex flex-col overflow-hidden">
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-4 bg-smnyl-bg-soft/30"
          >
            {mensajes.length === 0 ? (
              <p className="text-sm italic text-smnyl-text-muted text-center mt-8">
                Cargando primera pregunta…
              </p>
            ) : (
              mensajes.map((m, i) => <ChatBubble key={i} mensaje={m} />)
            )}
            {responder.isPending && (
              <div className="flex justify-start animate-fade-in">
                <div className="bg-smnyl-accent-soft/50 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="text-[0.65rem] font-bold uppercase tracking-wider mb-1 opacity-70">
                    DocuMente
                  </div>
                  <div className="flex gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-smnyl-primary/60 animate-pulse" />
                    <span
                      className="w-2 h-2 rounded-full bg-smnyl-primary/60 animate-pulse"
                      style={{ animationDelay: "150ms" }}
                    />
                    <span
                      className="w-2 h-2 rounded-full bg-smnyl-primary/60 animate-pulse"
                      style={{ animationDelay: "300ms" }}
                    />
                  </div>
                </div>
              </div>
            )}
            {seccionCerrada && (
              <div className="mt-6 rounded-lg border border-smnyl-success-dark/30 bg-smnyl-success-soft p-4 animate-fade-in">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-smnyl-success-dark shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-smnyl-success-dark mb-1">
                      Sección cerrada
                    </p>
                    <p className="text-xs text-smnyl-text-muted mb-3">
                      DocuMente generó un borrador y lo guardó en la sección. Puedes
                      revisarlo y editarlo manualmente desde el dashboard.
                    </p>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => router.push(`/documentos/${id}`)}
                      >
                        Volver al dashboard
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          router.push(
                            `/documentos/${id}/secciones/${encodeURIComponent(sidDecoded)}`,
                          )
                        }
                      >
                        Revisar borrador
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {!seccionCerrada && (
            <div className="border-t border-smnyl-border p-3 bg-white">
              <div className="flex gap-2 items-end">
                <Textarea
                  rows={2}
                  placeholder="Escribe tu respuesta… (Enter para enviar, Shift+Enter para nueva línea)"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  className="flex-1 font-body resize-none min-h-[60px]"
                  disabled={responder.isPending}
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || responder.isPending}
                  size="default"
                  className="shrink-0"
                >
                  {responder.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function EmptyState({
  onIniciar,
  loading,
  preguntasGuia,
}: {
  onIniciar: () => void;
  loading: boolean;
  preguntasGuia: string[];
}) {
  return (
    <Card className="flex-1 flex flex-col items-center justify-center p-10 text-center animate-fade-in">
      <div className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-smnyl-accent-soft/40 text-smnyl-primary mb-4">
        <Sparkles className="h-7 w-7" />
      </div>
      <h2 className="font-display text-xl font-semibold text-smnyl-text mb-2">
        Empieza la entrevista
      </h2>
      <p className="text-sm text-smnyl-text-muted max-w-md mb-6">
        DocuMente te hará preguntas guiadas para llenar esta sección. Al cerrar la
        conversación, generará un borrador formal que podrás revisar y editar.
      </p>

      {preguntasGuia.length > 0 && (
        <div className="mb-6 max-w-md text-left">
          <p className="text-xs font-semibold uppercase tracking-wider text-smnyl-text-muted mb-2">
            Algunas preguntas que cubriremos
          </p>
          <ul className="space-y-1.5">
            {preguntasGuia.slice(0, 4).map((p, i) => (
              <li
                key={i}
                className="text-sm text-smnyl-text leading-snug flex gap-2"
              >
                <span className="text-smnyl-primary shrink-0">•</span>
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <Button size="lg" onClick={onIniciar} disabled={loading}>
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        Iniciar entrevista
      </Button>
    </Card>
  );
}
