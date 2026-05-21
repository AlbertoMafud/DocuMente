/**
 * Helper para consumir Server-Sent Events sobre POST multipart.
 *
 * El `EventSource` nativo del browser solo soporta GET y headers
 * limitados — no sirve para nuestro endpoint POST `/documentos/crear-con-fuentes/stream`
 * que recibe form-data con archivos. Usamos `fetch` + lectura del
 * ReadableStream y parsing SSE manual.
 *
 * Cada evento SSE tiene la forma:
 *   event: <type>\n
 *   data: <json>\n
 *   \n
 *
 * Este parser es tolerante a líneas extra, eventos sin payload, y
 * fragmentación TCP (chunks que parten un evento a la mitad).
 */

export interface SseEvent<T = unknown> {
  event: string;
  data: T;
}

/**
 * Abre un POST multipart y devuelve un AsyncIterator de eventos SSE.
 *
 * Uso:
 *   for await (const evt of streamSse(url, formData)) {
 *     if (evt.event === "progress") { ... }
 *   }
 */
export async function* streamSse<T = unknown>(
  url: string,
  body: FormData,
  init: { headers?: Record<string, string>; signal?: AbortSignal } = {},
): AsyncIterableIterator<SseEvent<T>> {
  const res = await fetch(url, {
    method: "POST",
    body,
    headers: { Accept: "text/event-stream", ...(init.headers ?? {}) },
    signal: init.signal,
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`SSE failed ${res.status}: ${detail.slice(0, 500)}`);
  }
  if (!res.body) {
    throw new Error("SSE response sin body");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Eventos separados por línea en blanco (\n\n)
    let sep = buffer.indexOf("\n\n");
    while (sep !== -1) {
      const raw = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const parsed = parseEvent<T>(raw);
      if (parsed) yield parsed;
      sep = buffer.indexOf("\n\n");
    }
  }

  // Drenar buffer final si hay un evento incompleto
  if (buffer.trim()) {
    const parsed = parseEvent<T>(buffer);
    if (parsed) yield parsed;
  }
}

function parseEvent<T>(raw: string): SseEvent<T> | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
    // Ignorar :comment, id:, retry: — no los usamos por ahora
  }
  if (dataLines.length === 0) return null;
  const dataRaw = dataLines.join("\n");
  let data: T;
  try {
    data = JSON.parse(dataRaw) as T;
  } catch {
    // Si no es JSON, pasamos el string crudo como T (caller decide)
    data = dataRaw as unknown as T;
  }
  return { event, data };
}
