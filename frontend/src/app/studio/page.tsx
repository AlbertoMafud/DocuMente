/**
 * Template Studio — asistente de 5 pasos (S-C de TEMPLATE_STUDIO_SPEC).
 *
 * Convierte una plantilla "hecha para humanos" (.docx) en una plantilla que
 * el sistema sabe usar para entrevistar: la IA propone la capa AI-ready y el
 * administrador la cura antes de publicar. Nada se publica sin pasar la
 * validación de calidad.
 */
"use client";

import { useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  FileText,
  Layers,
  Plus,
  Sparkles,
  Table2,
  Trash2,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Stepper } from "@/components/ui/stepper";
import { DropZone } from "@/components/upload/dropzone";
import { SeccionEditor } from "@/components/studio/seccion-editor";
import {
  useCrearTemplate,
  useExtraerTemplate,
  useLintTemplate,
  useTemplatesStudio,
  useTransicionarTemplate,
  useActualizarSeccionesTemplate,
} from "@/lib/api/hooks";
import { APIError } from "@/lib/api/client";
import type {
  Extraccion,
  HallazgoLint,
  ResultadoLint,
  SeccionCandidata,
  SeccionCatalogoDinamica,
} from "@/lib/api/types";
import { cn } from "@/lib/utils";

const PASOS = ["Subir", "Estructura", "Propuesta", "Curación", "Publicar"];

function mensajeDeError(e: unknown): string {
  if (e instanceof APIError) return e.detail;
  return "Ocurrió un problema inesperado. Intenta de nuevo.";
}

export default function StudioPage() {
  const [paso, setPaso] = useState(0);

  // Paso 1
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [archivos, setArchivos] = useState<File[]>([]);

  // Resultado de la extracción + propuesta
  const [extraccion, setExtraccion] = useState<Extraccion | null>(null);

  // Paso 4 — catálogo en curación (estado local hasta guardar)
  const [secciones, setSecciones] = useState<SeccionCatalogoDinamica[]>([]);
  const [seleccionada, setSeleccionada] = useState(0);

  // Paso 5
  const [templateId, setTemplateId] = useState<string | null>(null);
  const [lint, setLint] = useState<ResultadoLint | null>(null);
  const [aceptaAdvertencias, setAceptaAdvertencias] = useState(false);
  const [publicado, setPublicado] = useState(false);

  const extraer = useExtraerTemplate();
  const crear = useCrearTemplate();
  const actualizarSecciones = useActualizarSeccionesTemplate();
  const correrLint = useLintTemplate();
  const transicionar = useTransicionarTemplate();
  const publicados = useTemplatesStudio("publicado");

  const ocupado =
    extraer.isPending ||
    crear.isPending ||
    actualizarSecciones.isPending ||
    correrLint.isPending ||
    transicionar.isPending;

  // --- Paso 1 → 2: extraer estructura y pedir propuesta ---
  async function handleExtraer() {
    if (!nombre.trim()) {
      toast.error("Ponle nombre al tipo de documento.");
      return;
    }
    if (archivos.length === 0) {
      toast.error("Sube el archivo .docx de la plantilla.");
      return;
    }
    try {
      const res = await extraer.mutateAsync({
        archivo: archivos[0],
        nombre: nombre.trim(),
        descripcion: descripcion.trim(),
      });
      setExtraccion(res);
      setSecciones(res.propuesta);
      setPaso(1);
    } catch (e) {
      toast.error(mensajeDeError(e));
    }
  }

  // --- Paso 4 → 5: persistir el borrador y validar ---
  async function handleValidar() {
    if (secciones.length === 0) {
      toast.error("El catálogo no puede quedar vacío.");
      return;
    }
    try {
      let id = templateId;
      if (!id) {
        const t = await crear.mutateAsync({
          nombre: nombre.trim(),
          descripcion: descripcion.trim(),
          archivo_origen: archivos[0]?.name ?? null,
          secciones,
        });
        id = t.id;
        setTemplateId(id);
      } else {
        await actualizarSecciones.mutateAsync({ id, secciones });
      }
      const resultado = await correrLint.mutateAsync(id);
      setLint(resultado);
      setAceptaAdvertencias(false);
      setPaso(4);
    } catch (e) {
      toast.error(mensajeDeError(e));
    }
  }

  async function handlePublicar() {
    if (!templateId) return;
    try {
      await transicionar.mutateAsync({
        id: templateId,
        accion: "publicar",
        aceptarAdvertencias: aceptaAdvertencias,
      });
      setPublicado(true);
      toast.success("Plantilla publicada. Ya se puede usar para crear documentos.");
    } catch (e) {
      toast.error(mensajeDeError(e));
    }
  }

  function actualizarSeccion(idx: number, nueva: SeccionCatalogoDinamica) {
    setSecciones((prev) => prev.map((s, i) => (i === idx ? nueva : s)));
  }

  function agregarSeccion() {
    const numero = String(secciones.length + 1);
    setSecciones((prev) => [
      ...prev,
      {
        id: `${numero}.seccion_nueva`,
        numero,
        nombre: "Sección nueva",
        obligatoria: true,
        intencion: "",
        tipo_contenido: "texto",
        schema_tabla: [],
        aliases: [],
        preguntas_guia: [],
      },
    ]);
    setSeleccionada(secciones.length);
  }

  function eliminarSeccion(idx: number) {
    setSecciones((prev) => prev.filter((_, i) => i !== idx));
    setSeleccionada((prev) => Math.max(0, Math.min(prev, secciones.length - 2)));
  }

  const errores = lint?.hallazgos.filter((h) => h.severidad === "error") ?? [];
  const advertencias = lint?.hallazgos.filter((h) => h.severidad === "advertencia") ?? [];

  return (
    <div className="space-y-6">
      <header className="space-y-3">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-smnyl-primary/10 text-smnyl-primary mb-3">
              <Layers className="h-5 w-5" />
            </div>
            <h1 className="font-display text-3xl font-semibold text-smnyl-text">
              Template Studio
            </h1>
            <p className="text-sm text-smnyl-text-muted max-w-2xl mt-2">
              Convierte una plantilla de Word en un tipo de documento que DocuMente sabe
              entrevistar. La IA propone la estructura; tú la revisas antes de publicarla.
            </p>
          </div>
          {publicados.data && publicados.data.length > 0 && (
            <Badge variant="published" className="shrink-0">
              {publicados.data.length} publicada{publicados.data.length === 1 ? "" : "s"}
            </Badge>
          )}
        </div>
        <Stepper pasos={PASOS} actualIdx={paso} />
      </header>

      {/* ---------- Paso 1: Subir ---------- */}
      {paso === 0 && (
        <Card className="p-6 space-y-5 animate-fade-in">
          <div className="space-y-2">
            <Label htmlFor="nombre-template">Nombre del tipo de documento</Label>
            <Input
              id="nombre-template"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ficha de Procedimiento Operativo"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="descripcion-template">Descripción (una línea)</Label>
            <Input
              id="descripcion-template"
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              placeholder="Documenta procedimientos operativos de las áreas de negocio"
            />
          </div>
          <div className="space-y-2">
            <Label>Plantilla de origen (.docx)</Label>
            <DropZone
              accept=".docx"
              files={archivos}
              onChange={setArchivos}
              titulo="Arrastra la plantilla aquí"
              subtitulo="Un .docx con los encabezados del documento — también sirve un ejemplo ya lleno"
            />
          </div>
          <div className="flex justify-end">
            <Button onClick={handleExtraer} disabled={ocupado}>
              {extraer.isPending ? "Analizando la plantilla…" : "Analizar plantilla"}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </Card>
      )}

      {/* ---------- Paso 2: Estructura detectada ---------- */}
      {paso === 1 && extraccion && (
        <Card className="p-6 space-y-4 animate-fade-in">
          <div>
            <h2 className="font-display text-xl text-smnyl-text">Esto es lo que encontré</h2>
            <p className="text-sm text-smnyl-text-muted mt-1">
              Revisa que la lectura del archivo tenga sentido antes de continuar.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <ResumenChip
              icono={<FileText className="h-4 w-4" />}
              valor={extraccion.secciones_detectadas.length}
              etiqueta="encabezados detectados"
            />
            <ResumenChip
              icono={<Table2 className="h-4 w-4" />}
              valor={extraccion.n_tablas}
              etiqueta="tablas en el documento"
            />
          </div>

          {extraccion.advertencias.length > 0 && (
            <ul className="space-y-2">
              {extraccion.advertencias.map((a) => (
                <li
                  key={a}
                  className="flex gap-2 rounded-md bg-smnyl-warning-soft px-3 py-2 text-xs text-smnyl-warning-dark"
                >
                  <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
                  <span>{a}</span>
                </li>
              ))}
            </ul>
          )}

          <ListaDetectadas secciones={extraccion.secciones_detectadas} />

          <NavPasos
            onAtras={() => setPaso(0)}
            onSiguiente={() => setPaso(2)}
            siguienteTexto="Ver la propuesta"
            deshabilitado={ocupado}
          />
        </Card>
      )}

      {/* ---------- Paso 3: Propuesta de la IA ---------- */}
      {paso === 2 && extraccion && (
        <Card className="p-6 space-y-4 animate-fade-in">
          <div>
            <h2 className="font-display text-xl text-smnyl-text flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-smnyl-primary" aria-hidden="true" />
              Propuesta de la IA
            </h2>
            <p className="text-sm text-smnyl-text-muted mt-1">
              {secciones.length} sección{secciones.length === 1 ? "" : "es"} propuesta
              {secciones.length === 1 ? "" : "s"}. En el siguiente paso puedes corregir todo.
            </p>
          </div>

          {extraccion.notas_llm.length > 0 && (
            <div className="rounded-md border border-smnyl-border bg-smnyl-bg-soft/40 p-4 space-y-2">
              <p className="text-2xs uppercase tracking-eyebrow font-bold text-smnyl-text-muted">
                Decisiones que tomó
              </p>
              <ul className="space-y-1.5">
                {extraccion.notas_llm.map((n) => (
                  <li key={n} className="text-xs text-smnyl-text leading-relaxed">
                    • {n}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {secciones.length === 0 ? (
            <div className="rounded-md bg-smnyl-warning-soft px-4 py-3 text-sm text-smnyl-warning-dark">
              La IA no propuso secciones utilizables. Puedes construir el catálogo a mano en el
              siguiente paso.
            </div>
          ) : (
            <ul className="divide-y divide-smnyl-border rounded-md border border-smnyl-border overflow-hidden">
              {secciones.map((s) => (
                <li key={s.id} className="flex items-start gap-3 px-4 py-3 bg-white">
                  <span className="font-mono text-2xs text-smnyl-text-muted pt-0.5 w-10 shrink-0">
                    {s.numero}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-smnyl-text">{s.nombre}</span>
                      {!s.obligatoria && (
                        <Badge variant="outline" className="text-3xs">
                          opcional
                        </Badge>
                      )}
                      {s.tipo_contenido !== "texto" && (
                        <Badge variant="secondary" className="text-3xs">
                          {s.tipo_contenido}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-smnyl-text-muted mt-0.5 line-clamp-2">
                      {s.intencion || "Sin intención declarada"}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}

          <NavPasos
            onAtras={() => setPaso(1)}
            onSiguiente={() => setPaso(3)}
            siguienteTexto="Revisar sección por sección"
            deshabilitado={ocupado}
          />
        </Card>
      )}

      {/* ---------- Paso 4: Curación ---------- */}
      {paso === 3 && (
        <div className="space-y-4 animate-fade-in">
          <div className="grid grid-cols-1 lg:grid-cols-[18rem_1fr] gap-4">
            {/* Lista de secciones */}
            <Card className="p-3 h-fit lg:sticky lg:top-20">
              <div className="flex items-center justify-between px-1 pb-2">
                <span className="text-2xs uppercase tracking-eyebrow font-bold text-smnyl-text-muted">
                  Secciones ({secciones.length})
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={agregarSeccion}
                  aria-label="Agregar sección"
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              <ul className="space-y-0.5 max-h-[60vh] overflow-y-auto">
                {secciones.map((s, i) => (
                  <li key={s.id}>
                    <button
                      type="button"
                      onClick={() => setSeleccionada(i)}
                      className={cn(
                        "w-full text-left rounded-md px-3 py-2 text-sm transition-all duration-200",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-smnyl-primary",
                        i === seleccionada
                          ? "bg-smnyl-primary text-white"
                          : "text-smnyl-text-muted hover:bg-smnyl-bg-soft hover:text-smnyl-text",
                      )}
                    >
                      <span className="font-mono text-3xs opacity-70 mr-2">{s.numero}</span>
                      <span className="truncate">{s.nombre}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </Card>

            {/* Editor */}
            <Card className="p-6">
              {secciones[seleccionada] ? (
                <>
                  <div className="flex items-center justify-between mb-5">
                    <h2 className="font-display text-xl text-smnyl-text">
                      Sección {secciones[seleccionada].numero}
                    </h2>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => eliminarSeccion(seleccionada)}
                      aria-label="Eliminar esta sección"
                      className="text-smnyl-danger"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  <SeccionEditor
                    seccion={secciones[seleccionada]}
                    onChange={(nueva) => actualizarSeccion(seleccionada, nueva)}
                  />
                </>
              ) : (
                <div className="text-center py-12 space-y-3">
                  <p className="text-sm text-smnyl-text-muted">
                    El catálogo está vacío. Agrega la primera sección para empezar.
                  </p>
                  <Button onClick={agregarSeccion}>
                    <Plus className="mr-2 h-4 w-4" />
                    Agregar sección
                  </Button>
                </div>
              )}
            </Card>
          </div>

          <Card className="p-4">
            <NavPasos
              onAtras={() => setPaso(2)}
              onSiguiente={handleValidar}
              siguienteTexto={ocupado ? "Validando…" : "Validar calidad"}
              deshabilitado={ocupado}
            />
          </Card>
        </div>
      )}

      {/* ---------- Paso 5: Validar y publicar ---------- */}
      {paso === 4 && lint && (
        <Card className="p-6 space-y-5 animate-fade-in">
          {publicado ? (
            <div className="text-center py-8 space-y-4">
              <div className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-smnyl-success-soft text-smnyl-success-dark">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <div>
                <h2 className="font-display text-2xl text-smnyl-text">Plantilla publicada</h2>
                <p className="text-sm text-smnyl-text-muted mt-2 max-w-md mx-auto">
                  «{nombre}» ya aparece como tipo de documento al crear uno nuevo. Cualquier
                  persona puede empezar a documentar con ella.
                </p>
              </div>
              <div className="flex justify-center gap-2 pt-2">
                <Button asChild>
                  <Link href="/documentos/crear">Crear un documento</Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link href="/">Volver al inicio</Link>
                </Button>
              </div>
            </div>
          ) : (
            <>
              <div>
                <h2 className="font-display text-xl text-smnyl-text">Validación de calidad</h2>
                <p className="text-sm text-smnyl-text-muted mt-1">
                  Los problemas bloquean la publicación; las advertencias solo piden tu
                  confirmación.
                </p>
              </div>

              {errores.length === 0 && advertencias.length === 0 && (
                <div className="flex items-center gap-3 rounded-md bg-smnyl-success-soft px-4 py-3">
                  <CheckCircle2 className="h-5 w-5 text-smnyl-success-dark shrink-0" />
                  <span className="text-sm text-smnyl-success-dark">
                    Sin observaciones. La plantilla está lista para publicarse.
                  </span>
                </div>
              )}

              {errores.length > 0 && (
                <GrupoHallazgos titulo="Problemas que impiden publicar" hallazgos={errores} />
              )}
              {advertencias.length > 0 && (
                <GrupoHallazgos titulo="Advertencias" hallazgos={advertencias} />
              )}

              {errores.length === 0 && advertencias.length > 0 && (
                <label className="flex items-start gap-2 cursor-pointer rounded-md border border-smnyl-border p-3">
                  <input
                    type="checkbox"
                    checked={aceptaAdvertencias}
                    onChange={(e) => setAceptaAdvertencias(e.target.checked)}
                    className="mt-0.5 h-4 w-4 accent-smnyl-primary"
                  />
                  <span className="text-xs text-smnyl-text-muted leading-relaxed">
                    <span className="font-medium text-smnyl-text">
                      Entiendo las advertencias y quiero publicar
                    </span>
                    <br />
                    Tu aceptación queda registrada en el historial de la plantilla.
                  </span>
                </label>
              )}

              <div className="flex items-center justify-between pt-2">
                <Button variant="ghost" onClick={() => setPaso(3)} disabled={ocupado}>
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Volver a corregir
                </Button>
                <Button
                  onClick={handlePublicar}
                  disabled={
                    ocupado ||
                    errores.length > 0 ||
                    (advertencias.length > 0 && !aceptaAdvertencias)
                  }
                >
                  {transicionar.isPending ? "Publicando…" : "Publicar plantilla"}
                </Button>
              </div>
            </>
          )}
        </Card>
      )}
    </div>
  );
}

// ---------- Piezas auxiliares ----------

function ResumenChip({
  icono,
  valor,
  etiqueta,
}: {
  icono: React.ReactNode;
  valor: number;
  etiqueta: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-md border border-smnyl-border bg-white px-4 py-3">
      <span className="text-smnyl-primary">{icono}</span>
      <span className="font-display text-2xl text-smnyl-text tabular-nums">{valor}</span>
      <span className="text-xs text-smnyl-text-muted">{etiqueta}</span>
    </div>
  );
}

function ListaDetectadas({ secciones }: { secciones: SeccionCandidata[] }) {
  if (secciones.length === 0) {
    return (
      <p className="text-sm text-smnyl-text-muted">
        No se detectaron encabezados. La IA propondrá una estructura solo a partir del texto.
      </p>
    );
  }
  return (
    <ul className="divide-y divide-smnyl-border rounded-md border border-smnyl-border overflow-hidden max-h-80 overflow-y-auto">
      {secciones.map((s, i) => (
        <li
          key={`${s.numero}-${s.titulo}-${i}`}
          className="flex items-center gap-3 bg-white px-4 py-2"
          style={{ paddingLeft: `${1 + (s.nivel - 1) * 1.25}rem` }}
        >
          <span className="font-mono text-3xs text-smnyl-text-muted w-8 shrink-0">
            {s.numero || "—"}
          </span>
          <span className="text-sm text-smnyl-text truncate flex-1">{s.titulo}</span>
          <span className="text-3xs text-smnyl-text-muted shrink-0 tabular-nums">
            {s.n_caracteres} car.
          </span>
        </li>
      ))}
    </ul>
  );
}

function GrupoHallazgos({
  titulo,
  hallazgos,
}: {
  titulo: string;
  hallazgos: HallazgoLint[];
}) {
  const esError = hallazgos[0]?.severidad === "error";
  return (
    <div className="space-y-2">
      <p className="text-2xs uppercase tracking-eyebrow font-bold text-smnyl-text-muted">
        {titulo} ({hallazgos.length})
      </p>
      <ul className="space-y-1.5">
        {hallazgos.map((h, i) => (
          <li
            key={`${h.codigo}-${h.seccion_id ?? "global"}-${i}`}
            className={cn(
              "flex gap-2 rounded-md px-3 py-2 text-xs",
              esError
                ? "bg-smnyl-danger-soft text-smnyl-danger"
                : "bg-smnyl-warning-soft text-smnyl-warning-dark",
            )}
          >
            {esError ? (
              <XCircle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
            ) : (
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
            )}
            <span className="leading-relaxed">{h.mensaje}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function NavPasos({
  onAtras,
  onSiguiente,
  siguienteTexto,
  deshabilitado,
}: {
  onAtras: () => void;
  onSiguiente: () => void;
  siguienteTexto: string;
  deshabilitado: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <Button variant="ghost" onClick={onAtras} disabled={deshabilitado}>
        <ArrowLeft className="mr-2 h-4 w-4" />
        Atrás
      </Button>
      <Button onClick={onSiguiente} disabled={deshabilitado}>
        {siguienteTexto}
        <ArrowRight className="ml-2 h-4 w-4" />
      </Button>
    </div>
  );
}
