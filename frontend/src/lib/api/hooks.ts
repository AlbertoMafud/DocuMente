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
  auditoriaApi,
  brechasApi,
  documentosApi,
  seccionesApi,
  templatesApi,
} from "./client";
import type {
  AccionVisibilidadRequest,
  CrearDocumentoRequest,
  EditarMetadataRequest,
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
