/**
 * Configuración — info de la app y settings (placeholder).
 *
 * En esta versión es read-only: muestra qué está configurado y dónde
 * cambiarlo. Cuando agreguemos auth real y preferencias por usuario,
 * esta página crece con forms reales.
 */
"use client";

import Link from "next/link";
import { Settings, ExternalLink, Server, Database, Lock, Sparkles } from "lucide-react";

import { Card } from "@/components/ui/card";
import { healthApi } from "@/lib/api/client";
import { useQuery } from "@tanstack/react-query";

export default function ConfiguracionPage() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.ok,
    refetchInterval: 30_000,
  });

  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-primary/10 text-smnyl-primary mb-3">
          <Settings className="h-5 w-5" />
        </div>
        <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-2">
          Configuración
        </h1>
        <p className="text-sm text-smnyl-text-muted max-w-xl">
          Estado de la app y referencias a settings. Cuando habilitemos Cognito y
          preferencias por usuario, esta página crecerá con forms reales.
        </p>
      </div>

      <Card className="p-5 animate-fade-in">
        <div className="flex items-start gap-3 mb-4">
          <Server className="h-4 w-4 text-smnyl-primary mt-1 shrink-0" />
          <div>
            <h3 className="font-semibold text-smnyl-text">Backend API</h3>
            <p className="text-xs text-smnyl-text-muted">
              FastAPI en{" "}
              <code className="px-1.5 py-0.5 rounded bg-smnyl-bg-soft text-xs">
                {apiUrl}
              </code>
            </p>
            <div className="mt-2 flex items-center gap-2">
              {health.isLoading ? (
                <span className="text-xs text-smnyl-text-muted italic">verificando…</span>
              ) : health.error ? (
                <span className="inline-flex items-center gap-1 text-xs text-smnyl-danger">
                  <span className="h-2 w-2 rounded-full bg-smnyl-danger" />
                  Desconectada
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs text-smnyl-success-dark">
                  <span className="h-2 w-2 rounded-full bg-smnyl-success animate-pulse" />
                  Conectada · v{health.data?.version}
                </span>
              )}
              <Link
                href={`${apiUrl}/docs`}
                target="_blank"
                className="text-xs text-smnyl-primary hover:underline inline-flex items-center gap-1"
              >
                Swagger UI <ExternalLink className="h-3 w-3" />
              </Link>
            </div>
          </div>
        </div>
      </Card>

      <Card className="p-5 animate-fade-in">
        <div className="flex items-start gap-3 mb-4">
          <Database className="h-4 w-4 text-smnyl-primary mt-1 shrink-0" />
          <div>
            <h3 className="font-semibold text-smnyl-text">Persistencia</h3>
            <p className="text-xs text-smnyl-text-muted">
              SQLite local en MVP; PostgreSQL en EC2 una vez migrado. La URI se
              configura en la variable <code className="px-1 py-0.5 rounded bg-smnyl-bg-soft">DATABASE_URL</code>{" "}
              del backend.
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-5 animate-fade-in">
        <div className="flex items-start gap-3 mb-4">
          <Lock className="h-4 w-4 text-smnyl-primary mt-1 shrink-0" />
          <div>
            <h3 className="font-semibold text-smnyl-text">Auth</h3>
            <p className="text-xs text-smnyl-text-muted">
              Bearer token compartido (placeholder pre-Cognito). Cuando habilitemos
              Cognito real, aquí aparecerá información del usuario logueado +
              opciones de logout.
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-5 animate-fade-in">
        <div className="flex items-start gap-3 mb-4">
          <Sparkles className="h-4 w-4 text-smnyl-primary mt-1 shrink-0" />
          <div>
            <h3 className="font-semibold text-smnyl-text">LLM</h3>
            <p className="text-xs text-smnyl-text-muted">
              Anthropic API directo (Claude Sonnet 4.6 + Opus 4.7 + Haiku 4.5). La
              clave vive en <code className="px-1 py-0.5 rounded bg-smnyl-bg-soft">ANTHROPIC_API_KEY</code>{" "}
              en el backend.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
