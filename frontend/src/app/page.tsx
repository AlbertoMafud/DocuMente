/**
 * Home page — punto de entrada de DocuMente.
 *
 * Lógica:
 * - Si hay un documento activo en draft/in_review más reciente → ContinueHero
 *   con CTAs secundarios pequeños abajo.
 * - Si no hay actividad reciente → WelcomeHero con 3 CTAs grandes.
 * - En ambos casos, debajo: lista de documentos con tabs.
 */
"use client";

import Link from "next/link";
import { FilePlus2, Upload, Sparkles } from "lucide-react";

import { useDocumentos } from "@/lib/api/hooks";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

import { ContinueHero } from "@/components/home/continue-hero";
import { WelcomeHero } from "@/components/home/welcome-hero";
import { DocumentList } from "@/components/home/document-list";

export default function HomePage() {
  const { data: activos, isLoading } = useDocumentos("activos");

  const enProgreso = activos
    ?.filter((d) => d.estado === "draft" || d.estado === "in_review")
    .sort(
      (a, b) =>
        new Date(b.actualizado_en).getTime() -
        new Date(a.actualizado_en).getTime(),
    )[0];

  return (
    <div className="space-y-4">
      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : enProgreso ? (
        <>
          <ContinueHero doc={enProgreso} />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 max-w-2xl">
            <Button variant="outline" size="sm" asChild>
              <Link href="/documentos/crear">
                <FilePlus2 className="mr-1.5 h-3.5 w-3.5" />
                Crear nuevo
              </Link>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/importar">
                <Upload className="mr-1.5 h-3.5 w-3.5" />
                Importar .docx
              </Link>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/prophet">
                <Sparkles className="mr-1.5 h-3.5 w-3.5" />
                Ficha Prophet
              </Link>
            </Button>
          </div>
        </>
      ) : (
        <WelcomeHero />
      )}

      <DocumentList />
    </div>
  );
}
