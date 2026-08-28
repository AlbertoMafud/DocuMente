/**
 * Editor de una sección del catálogo AI-ready (paso 4 del Template Studio).
 *
 * Cada campo lleva la ayuda de su regla correspondiente de
 * docs/TEMPLATE_AIREADY_RULES.md, porque de la calidad de estos campos
 * depende que las entrevistas del template nuevo se sientan hechas por un
 * experto y no por un formulario.
 */
"use client";

import { Lock } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { SeccionCatalogoDinamica, TipoContenido } from "@/lib/api/types";

interface Props {
  seccion: SeccionCatalogoDinamica;
  onChange: (seccion: SeccionCatalogoDinamica) => void;
}

/** Convierte una lista a texto con una entrada por línea, y de vuelta. */
function aLineas(valores: string[]): string {
  return valores.join("\n");
}
function desdeLineas(texto: string): string[] {
  return texto
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
}

function AyudaRegla({ children }: { children: React.ReactNode }) {
  return <p className="text-2xs text-smnyl-text-muted leading-relaxed">{children}</p>;
}

export function SeccionEditor({ seccion, onChange }: Props) {
  const set = <K extends keyof SeccionCatalogoDinamica>(
    campo: K,
    valor: SeccionCatalogoDinamica[K],
  ) => onChange({ ...seccion, [campo]: valor });

  return (
    <div className="space-y-5">
      {/* Identidad de la sección */}
      <div className="grid grid-cols-1 sm:grid-cols-[7rem_1fr] gap-3">
        <div className="space-y-2">
          <Label htmlFor="numero">Número</Label>
          <Input
            id="numero"
            value={seccion.numero}
            onChange={(e) => set("numero", e.target.value)}
            placeholder="4.1"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="nombre">Nombre de la sección</Label>
          <Input
            id="nombre"
            value={seccion.nombre}
            onChange={(e) => set("nombre", e.target.value)}
            placeholder="Controles clave"
          />
        </div>
      </div>

      <div className="rounded-md border border-smnyl-border bg-smnyl-bg-soft/40 px-3 py-2">
        <div className="flex items-center gap-2 text-2xs text-smnyl-text-muted">
          <Lock className="h-3 w-3 shrink-0" aria-hidden="true" />
          <span>
            Identificador permanente:{" "}
            <code className="font-mono text-smnyl-text">{seccion.id}</code>
          </span>
        </div>
        <AyudaRegla>
          No cambia nunca, aunque renombres o reordenes la sección: es como el sistema
          recuerda su contenido, su entrevista y su historial.
        </AyudaRegla>
      </div>

      {/* Intención — el campo más importante */}
      <div className="space-y-2">
        <Label htmlFor="intencion">Qué conocimiento captura</Label>
        <Textarea
          id="intencion"
          value={seccion.intencion}
          onChange={(e) => set("intencion", e.target.value)}
          rows={3}
          placeholder="Descripción del problema que el modelo resuelve, incluyendo las restricciones bajo las que se diseñó."
        />
        <AyudaRegla>
          Di qué debe saberse después de leer la sección, no qué formato tiene. Prueba: tapa
          el nombre y lee solo esto — ¿un experto sabría qué contarte?
        </AyudaRegla>
      </div>

      {/* Preguntas guía */}
      <div className="space-y-2">
        <Label htmlFor="preguntas">Preguntas guía (una por línea)</Label>
        <Textarea
          id="preguntas"
          value={aLineas(seccion.preguntas_guia)}
          onChange={(e) => set("preguntas_guia", desdeLineas(e.target.value))}
          rows={4}
          placeholder={"¿Qué enfoques alternativos consideraste y por qué los descartaste?\n¿Qué supuestos podrían necesitar revisión?"}
        />
        <AyudaRegla>
          Las que haría un especialista del área, no un formulario. Las mejores persiguen el
          porqué, las decisiones descartadas y las dudas del experto.
        </AyudaRegla>
      </div>

      {/* Aliases */}
      <div className="space-y-2">
        <Label htmlFor="aliases">Nombres alternativos (uno por línea)</Label>
        <Textarea
          id="aliases"
          value={aLineas(seccion.aliases)}
          onChange={(e) => set("aliases", desdeLineas(e.target.value))}
          rows={3}
          placeholder={"objetivo\nobjetivo del modelo\npropósito"}
        />
        <AyudaRegla>
          Cómo titulan esta sección los documentos que ya existen. Cada nombre alternativo es
          una importación que funciona en lugar de una sección que queda vacía.
        </AyudaRegla>
      </div>

      {/* Tipo de contenido + obligatoriedad */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label>Forma del contenido</Label>
          <Select
            value={seccion.tipo_contenido}
            onValueChange={(v) => set("tipo_contenido", v as TipoContenido)}
          >
            <SelectTrigger aria-label="Forma del contenido">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="texto">Texto — explicación y contexto</SelectItem>
              <SelectItem value="tabla">Tabla — renglones que se repiten</SelectItem>
              <SelectItem value="campos">Campos — ficha de datos sueltos</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Obligatoriedad</Label>
          <Select
            value={seccion.obligatoria ? "si" : "no"}
            onValueChange={(v) => set("obligatoria", v === "si")}
          >
            <SelectTrigger aria-label="Obligatoriedad">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="si">Obligatoria</SelectItem>
              <SelectItem value="no">Opcional</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {seccion.tipo_contenido === "tabla" && (
        <div className="space-y-2">
          <Label htmlFor="schema">Columnas de la tabla (una por línea)</Label>
          <Textarea
            id="schema"
            value={aLineas(seccion.schema_tabla)}
            onChange={(e) => set("schema_tabla", desdeLineas(e.target.value))}
            rows={3}
            placeholder={"persona\nrol\narea"}
            className={cn(seccion.schema_tabla.length === 0 && "border-smnyl-danger")}
          />
          <AyudaRegla>
            Sin columnas declaradas la sección no se puede validar ni exportar como tabla.
          </AyudaRegla>
        </div>
      )}
    </div>
  );
}
