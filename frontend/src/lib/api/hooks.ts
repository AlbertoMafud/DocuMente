/**
 * Hooks de TanStack Query para la API DocuMente.
 *
 * Cada hook envuelve un endpoint del cliente con keys consistentes para
 * que invalidations + optimistic updates sean predecibles.
 */
"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  apendicesApi,
  auditoriaApi,
  brechasApi,
  documentosApi,
  entrevistaApi,
  seccionesApi,
  templatesApi,
  versionesApi,
} from "./client";
import type {
  AccionVisibilidadRequest,
  CrearDocumentoRequest,
  EditarMetadataRequest,
  EstadoDocumento,
  RolSignoff,
  Visibilidad,
} from "./types";

export const qk = {
  documentos: (visibilidad: Visibilidad = "activos") =>
    ["documentos", visibilidad] as const,
  documento: (id: string) => ["documentos", id] as const,
  brechas: (docId: string) => ["documentos", docId, "brechas"] as const,
  auditoria: (docId: string) => ["documentos", docId, "auditoria"] as const,
  secciones: (docId: string) => ["documentos", docId, "secciones"] as const,
  seccion: (docId: string, sid: string) =>
    ["documentos", docId, "secciones", sid] as const,
  entrevistaEstado: (docId: string, sid: string) =>
    ["documentos", docId, "entrevista", sid] as const,
  versiones: (docId: string) => ["documentos", docId, "versiones"] as const,
  apendices: (docId: string) => ["documentos", docId, "apendices"] as const,
  capitulosMRM: () => ["templates", "mrm", "capitulos"] as const,
  templates: () => ["templates"] as const,
};

export function useDocumentos(visibilidad: Visibilidad = "activos") {
  return useQuery({
    queryKey: qk.documentos(visibilidad),
    queryFn: () => documentosApi.listar(visibilidad),
    staleTime: 30_000,
  });
}

export function useDocumento(id: string) {
  return useQuery({
    queryKey: qk.documento(id),
    queryFn: () => documentosApi.obtener(id),
    enabled: !!id,
  });
}

export function useBrechas(docId: string) {
  return useQuery({
    queryKey: qk.brechas(docId),
    queryFn: () => brechasApi.listar(docId),
    enabled: !!docId,
  });
}

export function useAuditoria(docId: string) {
  return useQuery({
    queryKey: qk.auditoria(docId),
    queryFn: () => auditoriaApi.listar(docId),
    enabled: !!docId,
  });
}

export function useSecciones(docId: string) {
  return useQuery({
    queryKey: qk.secciones(docId),
    queryFn: () => seccionesApi.listar(docId),
    enabled: !!docId,
  });
}

export function useSeccion(docId: string, sid: string) {
  return useQuery({
    queryKey: qk.seccion(docId, sid),
    queryFn: () => seccionesApi.obtener(docId, sid),
    enabled: !!docId && !!sid,
  });
}

export function useCapitulosMRM() {
  return useQuery({
    queryKey: qk.capitulosMRM(),
    queryFn: () => templatesApi.capitulosMRM(),
    staleTime: 5 * 60_000,
  });
}

// ===== Mutations =====

export function useCrearDocumento() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CrearDocumentoRequest) => documentosApi.crear(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documentos"] });
    },
  });
}

export function useCrearDocumentoConFuentes() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      nombre_modelo,
      fuentes,
      actor = "default",
      describir_imagenes = false,
    }: {
      nombre_modelo: string;
      fuentes: File[];
      actor?: string;
      describir_imagenes?: boolean;
    }) =>
      documentosApi.crearConFuentes(
        nombre_modelo,
        fuentes,
        actor,
        describir_imagenes,
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documentos"] });
    },
  });
}

export function useArchivar() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload?: AccionVisibilidadRequest }) =>
      documentosApi.archivar(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documentos"] }),
  });
}

export function useDesarchivar() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => documentosApi.desarchivar(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documentos"] }),
  });
}

export function useEnviarAPapelera() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload?: AccionVisibilidadRequest }) =>
      documentosApi.enviarAPapelera(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documentos"] }),
  });
}

export function useRestaurar() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => documentosApi.restaurar(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documentos"] }),
  });
}

export function useEditarMetadata() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: EditarMetadataRequest }) =>
      documentosApi.editarMetadata(id, payload),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["documentos"] });
      qc.setQueryData(qk.documento(data.id), data);
    },
  });
}

export function useEditarSeccion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      docId,
      sid,
      contenido,
    }: {
      docId: string;
      sid: string;
      contenido: string;
    }) => seccionesApi.editar(docId, sid, contenido),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: qk.documento(vars.docId) });
      qc.invalidateQueries({ queryKey: qk.brechas(vars.docId) });
      qc.invalidateQueries({ queryKey: qk.secciones(vars.docId) });
      qc.invalidateQueries({ queryKey: qk.seccion(vars.docId, vars.sid) });
    },
  });
}

// ===== State machine + signoffs =====

export function useCambiarEstado() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, destino }: { id: string; destino: EstadoDocumento }) =>
      documentosApi.cambiarEstado(id, destino),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["documentos"] });
      qc.setQueryData(qk.documento(data.id), data);
      qc.invalidateQueries({ queryKey: qk.auditoria(data.id) });
    },
  });
}

export function useRegistrarSignoff() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, rol }: { id: string; rol: RolSignoff }) =>
      documentosApi.signoff(id, rol),
    onSuccess: (data) => {
      qc.setQueryData(qk.documento(data.id), data);
      qc.invalidateQueries({ queryKey: qk.auditoria(data.id) });
    },
  });
}

// ===== Entrevista =====

export function useEstadoEntrevista(docId: string, sid: string) {
  return useQuery({
    queryKey: qk.entrevistaEstado(docId, sid),
    queryFn: () => entrevistaApi.estado(docId, sid),
    enabled: !!docId && !!sid,
    retry: false,  // 404 si no hay entrevista activa — no reintentar
  });
}

export function useIniciarEntrevista() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ docId, sid }: { docId: string; sid: string }) =>
      entrevistaApi.iniciar(docId, sid),
    onSuccess: (data, vars) => {
      qc.setQueryData(qk.entrevistaEstado(vars.docId, vars.sid), data);
    },
  });
}

export function useResponderPregunta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      docId,
      sid,
      respuesta,
    }: {
      docId: string;
      sid: string;
      respuesta: string;
    }) => entrevistaApi.responder(docId, sid, respuesta),
    onSuccess: (_data, vars) => {
      // Re-fetch del estado para tener el historial completo
      qc.invalidateQueries({ queryKey: qk.entrevistaEstado(vars.docId, vars.sid) });
      qc.invalidateQueries({ queryKey: qk.documento(vars.docId) });
      qc.invalidateQueries({ queryKey: qk.brechas(vars.docId) });
      qc.invalidateQueries({ queryKey: qk.secciones(vars.docId) });
    },
  });
}

export function useDescartarEntrevista() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ docId, sid }: { docId: string; sid: string }) =>
      entrevistaApi.descartar(docId, sid),
    onSuccess: (_data, vars) => {
      qc.removeQueries({ queryKey: qk.entrevistaEstado(vars.docId, vars.sid) });
    },
  });
}

// ===== Versiones =====

export function useVersiones(docId: string) {
  return useQuery({
    queryKey: qk.versiones(docId),
    queryFn: () => versionesApi.listar(docId),
    enabled: !!docId,
  });
}

export function useCrearVersion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ docId, comentario }: { docId: string; comentario: string }) =>
      versionesApi.crear(docId, comentario),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: qk.versiones(vars.docId) });
      qc.invalidateQueries({ queryKey: qk.documento(vars.docId) });
    },
  });
}

// ===== Apéndices =====

export function useApendices(docId: string) {
  return useQuery({
    queryKey: qk.apendices(docId),
    queryFn: () => apendicesApi.listar(docId),
    enabled: !!docId,
  });
}

export function useAdjuntarTabla() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      docId,
      sid,
      archivo,
      titulo_base,
    }: {
      docId: string;
      sid: string;
      archivo: File;
      titulo_base: string;
    }) => apendicesApi.adjuntarTabla(docId, sid, archivo, titulo_base),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: qk.apendices(vars.docId) });
      qc.invalidateQueries({ queryKey: qk.documento(vars.docId) });
    },
  });
}

export function useAdjuntarPdf() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      docId,
      sid,
      archivo,
      titulo,
    }: {
      docId: string;
      sid: string;
      archivo: File;
      titulo: string;
    }) => apendicesApi.adjuntarPdf(docId, sid, archivo, titulo),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: qk.apendices(vars.docId) });
      qc.invalidateQueries({ queryKey: qk.documento(vars.docId) });
    },
  });
}

export function useAdjuntarFormula() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      docId,
      sid,
      latex_source,
      titulo,
    }: {
      docId: string;
      sid: string;
      latex_source: string;
      titulo: string;
    }) => apendicesApi.adjuntarFormula(docId, sid, latex_source, titulo),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: qk.apendices(vars.docId) });
      qc.invalidateQueries({ queryKey: qk.documento(vars.docId) });
    },
  });
}

export function useBorrarApendice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ docId, apendiceId }: { docId: string; apendiceId: string }) =>
      apendicesApi.borrar(docId, apendiceId),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: qk.apendices(vars.docId) });
      qc.invalidateQueries({ queryKey: qk.documento(vars.docId) });
    },
  });
}
