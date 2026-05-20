/**
 * GovernanceCard — card del dashboard con state machine + signoffs.
 *
 * Muestra estado actual del doc + acciones de transición disponibles +
 * registro de firmas (Reviewer/FAE). Las transiciones inválidas las
 * rechaza el backend con 409; aquí se muestra toast con la razón.
 */
"use client";

import { useState } from "react";
import Link from "next/link";
import { ShieldCheck, History, Loader2 } from "lucide-react";
import { toast } from "sonner";

import type { Documento, EstadoDocumento, RolSignoff } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useCambiarEstado, useRegistrarSignoff } from "@/lib/api/hooks";

interface GovernanceCardProps {
  documento: Documento;
}

const TRANSICIONES: Record<EstadoDocumento, EstadoDocumento[]> = {
  draft: ["in_review"],
  in_review: ["draft", "approved"],
  approved: ["published"],
  published: ["retired"],
  retired: [],
};

const ESTADO_LABEL: Record<EstadoDocumento, string> = {
  draft: "Borrador",
  in_review: "En Revisión",
  approved: "Aprobado",
  published: "Publicado",
  retired: "Retirado",
};

function transicionLabel(destino: EstadoDocumento): string {
  return `Pasar a ${ESTADO_LABEL[destino]}`;
}

export function GovernanceCard({ documento }: GovernanceCardProps) {
  const cambiarEstado = useCambiarEstado();
  const signoff = useRegistrarSignoff();

  const candidatos = TRANSICIONES[documento.estado];
  const enRevision = documento.estado === "in_review";

  function handleTransicion(destino: EstadoDocumento) {
    cambiarEstado.mutate(
      { id: documento.id, destino },
      {
        onSuccess: () =>
          toast.success(`Estado cambiado a ${ESTADO_LABEL[destino]}.`),
        onError: (err) => {
          const detail = (err as Error).message;
          toast.error(`Transición rechazada: ${detail}`);
        },
      },
    );
  }

  function handleSignoff(rol: RolSignoff) {
    signoff.mutate(
      { id: documento.id, rol },
      {
        onSuccess: () =>
          toast.success(
            `Sign-off ${rol === "reviewer" ? "Reviewer" : "FAE"} registrado.`,
          ),
        onError: (err) => toast.error(`Error: ${(err as Error).message}`),
      },
    );
  }

  return (
    <Card className="p-5 animate-fade-in">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="h-4 w-4 text-smnyl-primary" />
            <h3 className="font-display text-lg font-semibold text-smnyl-text">
              Gobernanza
            </h3>
          </div>
          <p className="text-xs text-smnyl-text-muted">
            {documento.n_eventos_audit} evento(s) en el audit trail.{" "}
            <Link
              href={`/documentos/${documento.id}/auditoria`}
              className="text-smnyl-primary hover:underline inline-flex items-center gap-1"
            >
              Ver auditoría completa
              <History className="h-3 w-3" />
            </Link>
          </p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Transiciones */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-smnyl-text-muted mb-2">
            Ciclo de vida MRM
          </p>
          {candidatos.length === 0 ? (
            <p className="text-sm italic text-smnyl-text-muted">
              Sin transiciones disponibles desde {ESTADO_LABEL[documento.estado]}.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {candidatos.map((destino) => {
                const isPrimary = destino === "in_review" || destino === "approved" || destino === "published";
                return (
                  <Button
                    key={destino}
                    variant={isPrimary ? "default" : "outline"}
                    size="sm"
                    disabled={cambiarEstado.isPending}
                    onClick={() => handleTransicion(destino)}
                  >
                    {cambiarEstado.isPending && (
                      <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
                    )}
                    {transicionLabel(destino)}
                  </Button>
                );
              })}
            </div>
          )}
        </div>

        {/* Sign-offs — solo en in_review */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-smnyl-text-muted mb-2">
            Sign-offs
          </p>
          {enRevision ? (
            <SignoffButtons
              onSignoff={handleSignoff}
              loading={signoff.isPending}
            />
          ) : (
            <p className="text-sm italic text-smnyl-text-muted">
              Solo disponibles cuando el documento está En Revisión.
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}

function SignoffButtons({
  onSignoff,
  loading,
}: {
  onSignoff: (rol: RolSignoff) => void;
  loading: boolean;
}) {
  const [confirmando, setConfirmando] = useState<RolSignoff | null>(null);
  if (confirmando) {
    return (
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-xs text-smnyl-text-muted">
          Confirmar firma como {confirmando.toUpperCase()}:
        </span>
        <Button
          size="sm"
          disabled={loading}
          onClick={() => {
            onSignoff(confirmando);
            setConfirmando(null);
          }}
        >
          Sí, firmar
        </Button>
        <Button variant="ghost" size="sm" onClick={() => setConfirmando(null)}>
          Cancelar
        </Button>
      </div>
    );
  }
  return (
    <div className="flex flex-wrap gap-2">
      <Button variant="outline" size="sm" onClick={() => setConfirmando("reviewer")}>
        Firmar como Reviewer
      </Button>
      <Button variant="outline" size="sm" onClick={() => setConfirmando("fae")}>
        Firmar como FAE
      </Button>
    </div>
  );
}
