/**
 * ChatBubble — burbuja de mensaje en la entrevista LLM.
 *
 * 3 roles: user (azul SMNYL, alineado a la derecha), assistant (accent_soft,
 * izquierda), system_note (warning_soft centrado, para notas de apéndices).
 *
 * Replica el componente Streamlit chat_bubble.py.
 */
"use client";

import type { MensajeEntrevista } from "@/lib/api/types";

interface ChatBubbleProps {
  mensaje: MensajeEntrevista;
}

const ESTILOS = {
  user: {
    container: "justify-end",
    bubble:
      "bg-smnyl-primary text-white rounded-2xl rounded-br-md max-w-[85%] shadow-smnyl-sm",
    label: "Tú",
    labelOpacity: "opacity-85",
  },
  assistant: {
    container: "justify-start",
    bubble:
      "bg-smnyl-accent-soft/50 text-smnyl-text rounded-2xl rounded-bl-md max-w-[85%] shadow-smnyl-sm",
    label: "DocuMente",
    labelOpacity: "opacity-70",
  },
  system_note: {
    container: "justify-center",
    bubble:
      "bg-smnyl-warning-soft text-smnyl-warning-dark rounded-lg max-w-[70%] border border-smnyl-warning-dark/20",
    label: "Sistema",
    labelOpacity: "opacity-70",
  },
} as const;

export function ChatBubble({ mensaje }: ChatBubbleProps) {
  const estilo = ESTILOS[mensaje.rol] ?? ESTILOS.assistant;
  return (
    <div className={`flex ${estilo.container} mb-3 animate-fade-in`}>
      <div className={`${estilo.bubble} px-4 py-3`}>
        <div
          className={`text-[0.65rem] font-bold uppercase tracking-wider mb-1 ${estilo.labelOpacity}`}
        >
          {estilo.label}
        </div>
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {mensaje.contenido}
        </div>
      </div>
    </div>
  );
}
