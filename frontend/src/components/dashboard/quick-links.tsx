/**
 * QuickLinks — fila de accesos rápidos a sub-páginas del documento.
 *
 * Aparece debajo del hero del dashboard. Cada link va a una página
 * dedicada (Auditoría, Vista previa, Versiones, Apéndices).
 */
"use client";

import Link from "next/link";
import {
  Eye,
  ClipboardList,
  GitBranch,
  Paperclip,
  Brain,
} from "lucide-react";

interface QuickLinksProps {
  documentoId: string;
  nEventos: number;
  nVersiones?: number;
  nApendices?: number;
}

interface QuickLinkProps {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  count?: number;
}

function QuickLink({ href, icon: Icon, label, count }: QuickLinkProps) {
  return (
    <Link
      href={href}
      className="
        group flex items-center gap-2 px-3 py-1.5
        rounded-md text-sm text-smnyl-text-muted
        border border-transparent
        transition-all duration-200 ease-out
        hover:bg-smnyl-bg-soft hover:text-smnyl-text hover:border-smnyl-border
      "
    >
      <Icon className="h-3.5 w-3.5 group-hover:text-smnyl-primary transition-colors" />
      <span>{label}</span>
      {count !== undefined && count > 0 && (
        <span className="rounded-full bg-smnyl-bg-soft group-hover:bg-white px-1.5 py-0.5 text-[0.65rem] font-semibold text-smnyl-text-muted">
          {count}
        </span>
      )}
    </Link>
  );
}

export function QuickLinks({
  documentoId,
  nEventos,
}: QuickLinksProps) {
  return (
    <div className="flex flex-wrap gap-1 -mt-2">
      <QuickLink
        href={`/documentos/${documentoId}/vista-previa`}
        icon={Eye}
        label="Vista previa"
      />
      <QuickLink
        href={`/documentos/${documentoId}/auditoria`}
        icon={ClipboardList}
        label="Auditoría"
        count={nEventos}
      />
      <QuickLink
        href={`/documentos/${documentoId}/versiones`}
        icon={GitBranch}
        label="Versiones"
      />
      <QuickLink
        href={`/documentos/${documentoId}/apendices`}
        icon={Paperclip}
        label="Apéndices"
      />
      <QuickLink
        href={`/documentos/${documentoId}/onboarding`}
        icon={Brain}
        label="Onboarding"
      />
    </div>
  );
}
