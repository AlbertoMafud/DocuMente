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
  Apendice,
  Brecha,
  CapituloMRM,
  CrearDocumentoRequest,
  Documento,
  DocumentoListItem,
  EditarMetadataRequest,
  EstadoDocumento,
  EventoAuditoria,
  IniciarEntrevistaResponse,
  RolSignoff,
  Seccion,
  TemplateInfo,
  TurnoEntrevista,
  Version,
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

  cambiarEstado: (id: string, destino: EstadoDocumento, actor = "default") =>
    request<Documento>(`/documentos/${id}/estado`, {
      method: "POST",
      body: JSON.stringify({ destino, actor }),
    }),

  signoff: (id: string, rol: RolSignoff, actor = "default") =>
    request<Documento>(`/documentos/${id}/signoff`, {
      method: "POST",
      body: JSON.stringify({ rol, actor }),
    }),
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

// ===== Entrevista LLM =====

export const entrevistaApi = {
  iniciar: (docId: string, sid: string) =>
    request<IniciarEntrevistaResponse>(
      `/documentos/${docId}/entrevista/${encodeURIComponent(sid)}/iniciar`,
      { method: "POST" },
    ),

  responder: (docId: string, sid: string, respuesta: string, actor = "default") =>
    request<TurnoEntrevista>(
      `/documentos/${docId}/entrevista/${encodeURIComponent(sid)}/responder`,
      {
        method: "POST",
        body: JSON.stringify({ respuesta, actor }),
      },
    ),

  estado: (docId: string, sid: string) =>
    request<IniciarEntrevistaResponse>(
      `/documentos/${docId}/entrevista/${encodeURIComponent(sid)}/estado`,
    ),

  descartar: (docId: string, sid: string) =>
    request<{ ok: boolean; mensaje: string }>(
      `/documentos/${docId}/entrevista/${encodeURIComponent(sid)}`,
      { method: "DELETE" },
    ),
};

// ===== Versiones =====

export const versionesApi = {
  listar: (docId: string) =>
    request<Version[]>(`/documentos/${docId}/versiones`),

  crear: (docId: string, comentario = "", actor = "default") =>
    request<Version>(`/documentos/${docId}/versiones`, {
      method: "POST",
      body: JSON.stringify({ comentario, actor }),
    }),

  obtener: (versionId: string) => request<Version>(`/versiones/${versionId}`),
};

// ===== Apéndices =====

export const apendicesApi = {
  listar: (docId: string) =>
    request<Apendice[]>(`/documentos/${docId}/apendices`),

  async adjuntarTabla(
    docId: string,
    sid: string,
    archivo: File,
    titulo_base: string,
  ): Promise<Apendice[]> {
    const fd = new FormData();
    fd.append("archivo", archivo);
    fd.append("titulo_base", titulo_base);
    const headers: Record<string, string> = {};
    if (API_TOKEN) headers.Authorization = `Bearer ${API_TOKEN}`;
    const res = await fetch(
      `${API_URL}/documentos/${docId}/secciones/${encodeURIComponent(sid)}/apendices/tabla`,
      { method: "POST", body: fd, headers },
    );
    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new APIError(res.status, detail);
    }
    return await res.json();
  },

  async adjuntarPdf(
    docId: string,
    sid: string,
    archivo: File,
    titulo: string,
  ): Promise<Apendice> {
    const fd = new FormData();
    fd.append("archivo", archivo);
    fd.append("titulo", titulo);
    const headers: Record<string, string> = {};
    if (API_TOKEN) headers.Authorization = `Bearer ${API_TOKEN}`;
    const res = await fetch(
      `${API_URL}/documentos/${docId}/secciones/${encodeURIComponent(sid)}/apendices/pdf`,
      { method: "POST", body: fd, headers },
    );
    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new APIError(res.status, detail);
    }
    return await res.json();
  },

  adjuntarFormula: (docId: string, sid: string, latex_source: string, titulo: string) =>
    request<Apendice>(
      `/documentos/${docId}/secciones/${encodeURIComponent(sid)}/apendices/formula`,
      {
        method: "POST",
        body: JSON.stringify({ latex_source, titulo }),
      },
    ),

  borrar: (docId: string, apendiceId: string) =>
    request<{ ok: boolean; mensaje: string }>(
      `/documentos/${docId}/apendices/${apendiceId}`,
      { method: "DELETE" },
    ),
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
