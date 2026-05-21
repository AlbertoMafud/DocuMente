/**
 * Tipos TypeScript de la API DocuMente — versión "amigable".
 *
 * Estos tipos son los que el frontend usa día a día. Son aliases /
 * re-empaquetados de los tipos autoritarios en `openapi.gen.ts`.
 *
 * **Fuente de verdad:** `openapi.gen.ts` (auto-generada desde la spec
 * OpenAPI del backend). Regenerar con:
 *
 *     npm run gen:api-types     # requiere el backend corriendo en :8001
 *
 * Workflow cuando un schema Python cambia:
 *   1. `npm run gen:api-types` → actualiza `openapi.gen.ts`
 *   2. Diffea `openapi.gen.ts` para ver qué cambió
 *   3. Sincroniza los campos relevantes en este archivo
 *   4. `npm run typecheck` valida que nada se rompió
 */

export type TipoDocumento = "model_development" | "prophet";
export type EstadoDocumento =
  | "draft"
  | "in_review"
  | "approved"
  | "published"
  | "retired";
export type EstadoVisibilidad = "activo" | "archivado" | "papelera";
export type TierRiesgo =
  | "low"
  | "medium_minus"
  | "medium"
  | "high"
  | "very_high"
  | "very_high_plus"
  | "critical";

export type Severidad = "alta" | "media" | "baja";
export type TipoBrecha =
  | "seccion_vacia"
  | "seccion_parcial"
  | "metadata_incompleta"
  | "supuesto_implicito"
  | "limitacion_no_documentada"
  | "validacion_pendiente";

export type Completitud = "vacia" | "parcial" | "completa" | "omitida";

export type TipoEvento =
  | "documento_creado"
  | "documento_importado"
  | "seccion_editada"
  | "seccion_completada"
  | "seccion_omitida"
  | "transicion_estado"
  | "metadata_actualizada"
  | "exportado"
  | "signoff_reviewer"
  | "signoff_fae"
  | "archivado"
  | "desarchivado"
  | "enviado_a_papelera"
  | "restaurado_de_papelera"
  | "eliminado_permanente"
  | "purgado_automatico"
  | "version_creada"
  | "version_restaurada";

export type Visibilidad = "activos" | "archivados" | "papelera" | "todos";

export interface MetadataModelo {
  nombre_modelo: string;
  model_id: string;
  model_class: string;
  profit_center: string;
  fae: string;
  model_owner: string;
  model_developers: string[];
  model_users: string[];
  current_version: string;
  implementation_platform: string;
  financial_impact: string;
  model_status: string;
  target_production_date: string;
  inherent_risk_tier: TierRiesgo | null;
  intended_use: string;
  use_restrictions: string;
  nomenclatura: string;
}

export interface DocumentoListItem {
  id: string;
  user_id: string;
  tipo: TipoDocumento;
  estado: EstadoDocumento;
  visibilidad: EstadoVisibilidad;
  nombre_modelo: string;
  porcentaje_completitud: number;
  porcentaje_resuelto: number;
  n_secciones: number;
  n_secciones_obligatorias: number;
  creado_en: string;
  actualizado_en: string;
  archivado: boolean;
  en_papelera: boolean;
}

export interface Seccion {
  id: string;
  nombre: string;
  numero: string;
  obligatoria: boolean;
  contenido: string | null;
  completitud: Completitud;
  intencion: string;
  preguntas_guia: string[];
  motivo_omision: string | null;
  tiene_contenido: boolean;
}

export interface Documento {
  id: string;
  user_id: string;
  tipo: TipoDocumento;
  estado: EstadoDocumento;
  visibilidad: EstadoVisibilidad;
  metadata_modelo: MetadataModelo;
  secciones: Seccion[];
  porcentaje_completitud: number;
  porcentaje_resuelto: number;
  cobertura_catalogo: number;
  creado_en: string;
  actualizado_en: string;
  archivo_origen: string | null;
  archivado: boolean;
  archivado_en: string | null;
  en_papelera: boolean;
  n_eventos_audit: number;
}

export interface Brecha {
  seccion_id: string;
  tipo: TipoBrecha;
  severidad: Severidad;
  mensaje: string;
  sugerencia: string;
}

export interface EventoAuditoria {
  timestamp: string;
  actor: string;
  tipo: TipoEvento;
  descripcion: string;
  seccion_id: string | null;
  metadata: Record<string, string>;
}

export interface CrearDocumentoRequest {
  tipo?: TipoDocumento;
  nombre_modelo?: string;
  actor?: string;
}

export interface CrearConFuentesResponse {
  documento: Documento;
  fuentes_extraidas: number;
  fuentes_descartadas: string[];
  secciones_prellenadas: number;
  llm_disponible: boolean;
  advertencias: string[];
}

export type EditarMetadataRequest = Partial<MetadataModelo>;

export interface AccionVisibilidadRequest {
  razon?: string;
  actor?: string;
}

export interface OkResponse {
  ok: boolean;
  mensaje: string;
}

export interface CapituloMRM {
  numero: string;
  nombre: string;
  secciones: SeccionCatalogoDTO[];
}

export interface SeccionCatalogoDTO {
  id: string;
  nombre: string;
  numero: string;
  obligatoria: boolean;
  intencion: string;
  preguntas_guia: string[];
}

export interface TemplateInfo {
  tipo: string;
  nombre: string;
  n_secciones: number;
}

export interface MensajeEntrevista {
  rol: "user" | "assistant" | "system_note";
  contenido: string;
}

export interface TurnoEntrevista {
  respuesta_asistente: string;
  seccion_cerrada: boolean;
  borrador: string | null;
  n_mensajes: number;
}

export interface IniciarEntrevistaResponse {
  turno: TurnoEntrevista;
  seccion_id: string;
  mensajes: MensajeEntrevista[];
}

export interface Version {
  id: string;
  documento_id: string;
  numero: number;
  comentario: string;
  creado_en: string;
  hash_contenido: string;
}

export interface Apendice {
  id: string;
  seccion_origen_id: string;
  titulo: string;
  tipo: "tabla" | "pdf" | "formula" | string;
  nombre_archivo_original: string;
  contenido_md: string;
}

export type RolSignoff = "reviewer" | "fae";
