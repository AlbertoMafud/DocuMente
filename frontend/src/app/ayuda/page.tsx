/**
 * Ayuda — recursos para usuarios + links a docs internos.
 *
 * Esta página da entrada rápida a las cosas que el usuario típicamente
 * busca: cómo crear un doc, cómo usar la entrevista, qué pasa al exportar.
 * Apunta a docs internos cuando aplica.
 */
"use client";

import Link from "next/link";
import {
  HelpCircle,
  FileText,
  Sparkles,
  Upload,
  Download,
  ClipboardList,
  ExternalLink,
} from "lucide-react";

import { Card } from "@/components/ui/card";

interface FAQItem {
  icon: React.ComponentType<{ className?: string }>;
  pregunta: string;
  respuesta: React.ReactNode;
}

const FAQ: FAQItem[] = [
  {
    icon: FileText,
    pregunta: "¿Cómo creo un documento nuevo?",
    respuesta: (
      <>
        En la home, click <strong>Crear nuevo documento</strong>. Eliges entre Model
        Development (28 secciones del template oficial NYL) o Ficha Prophet (12 secciones
        del registro de Modelos Actuariales). Le pones un nombre y listo — DocuMente
        genera la estructura vacía para que la llenes.
      </>
    ),
  },
  {
    icon: Upload,
    pregunta: "¿Cómo importo un .docx que ya tengo?",
    respuesta: (
      <>
        Click <strong>Importar</strong> en el sidebar (o desde la home). Arrastras el
        .docx o .pdf principal y opcionalmente fuentes adicionales (PDFs, Excel, TXT).
        DocuMente lo parsea contra el template, detecta brechas y pre-puebla las
        secciones que pueda.
      </>
    ),
  },
  {
    icon: Sparkles,
    pregunta: "¿Cómo funciona la entrevista con Claude?",
    respuesta: (
      <>
        Desde el dashboard de cualquier documento, click <strong>Entrevistar</strong> en
        una sección vacía o parcial. Claude hace preguntas guiadas; tú respondes en
        lenguaje natural. Cuando la sección queda &ldquo;cerrada&rdquo;, Claude genera
        un borrador formal que puedes revisar y editar.
      </>
    ),
  },
  {
    icon: ClipboardList,
    pregunta: "¿Qué es el audit trail / auditoría?",
    respuesta: (
      <>
        Cada acción sobre un documento (crear, editar, omitir, exportar, archivar,
        firmar) queda registrada inmutablemente. Esto es requisito de MRM §3.5 — la
        ves desde el dashboard del doc → <strong>Auditoría</strong> en los chips
        rápidos del hero.
      </>
    ),
  },
  {
    icon: Download,
    pregunta: "¿Cómo exporto el documento a .docx?",
    respuesta: (
      <>
        Desde el dashboard de un documento, click <strong>Exportar DOCX</strong>. Genera
        un Word con la marca SMNYL completa (paleta, fuentes, tablas con bordes).
        Opciones: traducir a inglés corporativo, polish de coherencia con IA,
        crear versión inmutable.
      </>
    ),
  },
  {
    icon: HelpCircle,
    pregunta: "¿Cuándo debo marcar una sección como omitida?",
    respuesta: (
      <>
        Solo cuando hayas verificado que la sección genuinamente no aplica al modelo
        (ej. &ldquo;Datos&rdquo; en un modelo puramente paramétrico) o no hay
        información disponible. Requiere motivo escrito — no es atajo para saltarse
        secciones. Una sección omitida cuenta como resuelta para la state machine MRM.
      </>
    ),
  },
];

const DOC_LINKS = [
  {
    label: "Guía completa de DocuMente",
    href: "/docs/GUIA_DOCUMENTE.md",
    descripcion: "Documento conceptual + técnico en español sencillo (~2h lectura)",
  },
  {
    label: "Arquitectura técnica",
    href: "/docs/ARQUITECTURA.md",
    descripcion: "Referencia técnica atemporal: capas, stack, decisiones",
  },
  {
    label: "Requisitos MRM",
    href: "/docs/MRM_REQUIREMENTS.md",
    descripcion: "Marco regulatorio interno de gobierno de modelos",
  },
];

export default function AyudaPage() {
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-primary/10 text-smnyl-primary mb-3">
          <HelpCircle className="h-5 w-5" />
        </div>
        <h1 className="font-display text-3xl font-semibold text-smnyl-text mb-2">
          Ayuda
        </h1>
        <p className="text-sm text-smnyl-text-muted max-w-xl">
          Preguntas frecuentes y enlaces a los documentos internos del proyecto.
        </p>
      </div>

      <section>
        <h2 className="font-display text-xl font-semibold text-smnyl-text mb-3">
          Preguntas frecuentes
        </h2>
        <div className="space-y-3">
          {FAQ.map((item, i) => {
            const Icon = item.icon;
            return (
              <Card key={i} className="p-5 animate-fade-in">
                <div className="flex items-start gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-md bg-smnyl-bg-soft text-smnyl-primary shrink-0">
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-smnyl-text mb-1">
                      {item.pregunta}
                    </h3>
                    <p className="text-sm text-smnyl-text-muted leading-relaxed">
                      {item.respuesta}
                    </p>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </section>

      <section>
        <h2 className="font-display text-xl font-semibold text-smnyl-text mb-3">
          Documentación interna
        </h2>
        <div className="space-y-2">
          {DOC_LINKS.map((d) => (
            <Card key={d.href} className="p-4 smnyl-card-hover">
              <Link
                href={d.href}
                target="_blank"
                className="flex items-start gap-3"
              >
                <ExternalLink className="h-4 w-4 text-smnyl-primary mt-1 shrink-0" />
                <div className="flex-1">
                  <p className="font-medium text-smnyl-text">{d.label}</p>
                  <p className="text-xs text-smnyl-text-muted">{d.descripcion}</p>
                </div>
              </Link>
            </Card>
          ))}
        </div>
      </section>

      <section>
        <h2 className="font-display text-xl font-semibold text-smnyl-text mb-3">
          ¿Algo no funciona?
        </h2>
        <Card className="p-5">
          <p className="text-sm text-smnyl-text-muted leading-relaxed">
            Si encuentras un bug o algo no se comporta como esperas, abre un issue en
            el repo de GitHub o avísale a Alberto. Si es urgente y bloquea trabajo,
            mientras tanto puedes usar la versión Streamlit (legacy) en{" "}
            <code className="px-1.5 py-0.5 rounded bg-smnyl-bg-soft text-xs">
              http://localhost:8052
            </code>
            .
          </p>
        </Card>
      </section>
    </div>
  );
}
