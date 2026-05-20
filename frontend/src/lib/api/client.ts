/**
 * Cliente fetch tipado de la API DocuMente.
 *
 * Lee `NEXT_PUBLIC_API_URL` (default http://localhost:8001) y `NEXT_PUBLIC_API_TOKEN`
 * (opcional — solo si la API tiene gate activo).
 *
 * No usa ninguna lib externa (axios, ofetch) — `fetch` nativo es suficiente,
 * tipado es lo único crítico aquí.
 */
import type {
  AccionVisibilidadRequest,
  Brecha,
  CapituloMRM,
  CrearDocumentoRequest,
  Documento,
  DocumentoListItem,
  EditarMetadataRequest,
  EventoAuditoria,
  Seccion,
  TemplateInfo,
  Visibilidad,
} from "./types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const API_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN ?? "";

export class APIError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public payload?: unknown,
  ) {
    super(`API ${status}: ${detail}`);
    this.name = "APIError";
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = `${API_URL}${path}`;
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type") && init?.body && typeof init.body === "string") {
    headers.set("Content-Type", "application/json");
  }
  if (API_TOKEN && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${API_TOKEN}`);
  }

  const res = await fetch(url, { ...init, headers, cache: "no-store" });
  if (!res.ok) {
    let payload: unknown = null;
    let detail = res.statusText;
    try {
      payload = await res.json();
      if (
        typeof payload === "object" &&
        payload !== null &&
        "detail" in payload
      ) {
        detail = String((payload as { detail: unknown }).detail);
      }
    } catch {
      // body wasn't JSON, leave detail as statusText
    }
    throw new APIError(res.status, detail, payload);
  }

  // Algunos endpoints (export DOCX) devuelven binarios — el caller usa res.blob().
  // request<T>() asume JSON; usar requestBlob() para descargas.
  if (res.status === 204) return undefined as unknown as T;
  return (await res.json()) as T;
}

async function requestBlob(path: string, init?: RequestInit): Promise<Blob> {
  const url = `${API_URL}${path}`;
  const headers = new Headers(init?.headers);
  if (API_TOKEN && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${API_TOKEN}`);
  }
  const res = await fetch(url, { ...init, headers });
  if (!res.ok) {
    throw new APIError(res.status, res.statusText);
  }
  return await res.blob();
}

// ===== Documentos =====

export const documentosApi = {
  listar: (visibilidad: Visibilidad = "activos") =>
    request<DocumentoListItem[]>(`/documentos?visibilidad=${visibilidad}`),

  obtener: (id: string) => request<Documento>(`/documentos/${id}`),

  crear: (payload: CrearDocumentoRequest) =>
    request<Documento>(`/documentos`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  editarMetadata: (id: string, payload: EditarMetadataRequest) =>
    request<Documento>(`/documentos/${id}/metadata`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  archivar: (id: string, payload: AccionVisibilidadRequest = {}) =>
    request<DocumentoListItem>(`/documentos/${id}/archivar`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  desarchivar: (id: string) =>
    request<DocumentoListItem>(`/documentos/${id}/desarchivar`, { method: "POST" }),

  enviarAPapelera: (id: string, payload: AccionVisibilidadRequest = {}) =>
    request<DocumentoListItem>(`/documentos/${id}/papelera`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  restaurar: (id: string) =>
    request<DocumentoListItem>(`/documentos/${id}/restaurar`, { method: "POST" }),
};

// ===== Secciones =====

export const seccionesApi = {
  listar: (docId: string) => request<Seccion[]>(`/documentos/${docId}/secciones`),

  obtener: (docId: string, seccionId: string) =>
    request<Seccion>(`/documentos/${docId}/secciones/${seccionId}`),

  editar: (docId: string, seccionId: string, contenido: string) =>
    request<Seccion>(`/documentos/${docId}/secciones/${seccionId}`, {
      method: "PUT",
      body: JSON.stringify({ contenido }),
    }),
};

// ===== Brechas + Auditoría =====

export const brechasApi = {
  listar: (docId: string) => request<Brecha[]>(`/documentos/${docId}/brechas`),
};

export const auditoriaApi = {
  listar: (docId: string, limit = 200) =>
    request<EventoAuditoria[]>(`/documentos/${docId}/auditoria?limit=${limit}`),
};

// ===== Templates / Catálogos =====

export const templatesApi = {
  listar: () => request<TemplateInfo[]>(`/templates`),

  capitulosMRM: () => request<CapituloMRM[]>(`/templates/mrm/capitulos`),
};

// ===== Export =====

export const exportarApi = {
  docx: (docId: string, body: Record<string, unknown> = {}) =>
    requestBlob(`/documentos/${docId}/exportar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};

// ===== Importar (multipart) =====

export const importarApi = {
  async docx(ancla: File, fuentes: File[] = [], actor = "default"): Promise<Documento> {
    const fd = new FormData();
    fd.append("ancla", ancla);
    for (const f of fuentes) fd.append("fuentes", f);
    fd.append("actor", actor);
    // No seteamos Content-Type — el browser pone el boundary correcto.
    const headers: Record<string, string> = {};
    if (API_TOKEN) headers.Authorization = `Bearer ${API_TOKEN}`;
    const res = await fetch(`${API_URL}/documentos/importar`, {
      method: "POST",
      body: fd,
      headers,
    });
    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new APIError(res.status, detail);
    }
    return (await res.json()) as Documento;
  },
};

// ===== Prophet =====

export const prophetApi = {
  async detectar(archivo: File): Promise<{
    modelos: { nombre: string; fila_idx: number; profit_center?: string }[];
    advertencias: string[];
  }> {
    const fd = new FormData();
    fd.append("archivo", archivo);
    const headers: Record<string, string> = {};
    if (API_TOKEN) headers.Authorization = `Bearer ${API_TOKEN}`;
    const res = await fetch(`${API_URL}/prophet/detectar`, {
      method: "POST",
      body: fd,
      headers,
    });
    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new APIError(res.status, detail);
    }
    return await res.json();
  },

  async importar(
    archivo: File,
    fila_idx: number,
    nombre_modelo: string,
    actor = "default",
  ): Promise<Documento> {
    const fd = new FormData();
    fd.append("archivo", archivo);
    fd.append("fila_idx", String(fila_idx));
    fd.append("nombre_modelo", nombre_modelo);
    fd.append("actor", actor);
    const headers: Record<string, string> = {};
    if (API_TOKEN) headers.Authorization = `Bearer ${API_TOKEN}`;
    const res = await fetch(`${API_URL}/prophet/importar`, {
      method: "POST",
      body: fd,
      headers,
    });
    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new APIError(res.status, detail);
    }
    return (await res.json()) as Documento;
  },
};

// ===== Health =====

export const healthApi = {
  ok: () => request<{ status: string; api: string; version: string }>(`/healthz`),
};

export { API_URL };
