/**
 * Stepper visual horizontal — replica el componente Streamlit
 * src/ui/components/stepper.py para mantener consistencia visual
 * en los flujos multi-step (onboarding, brief).
 */
"use client";

import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

interface StepperProps {
  pasos: string[];
  actualIdx: number;
}

export function Stepper({ pasos, actualIdx }: StepperProps) {
  if (pasos.length === 0) return null;

  return (
    <ol className="flex items-center gap-2 animate-fade-in">
      {pasos.map((paso, idx) => {
        const completado = idx < actualIdx;
        const actual = idx === actualIdx;
        return (
          <li key={paso} className="flex items-center gap-2 flex-1">
            <div className="flex items-center gap-2 min-w-0">
              <div
                className={cn(
                  "shrink-0 flex h-8 w-8 items-center justify-center rounded-full",
                  "text-xs font-bold transition-all duration-200 ease-out",
                  completado &&
                    "bg-smnyl-success-dark text-white shadow-smnyl-sm",
                  actual &&
                    "bg-smnyl-primary text-white ring-4 ring-smnyl-primary/15 shadow-smnyl-md",
                  !completado &&
                    !actual &&
                    "bg-white border border-smnyl-border text-smnyl-text-muted",
                )}
              >
                {completado ? <Check className="h-3.5 w-3.5" /> : idx + 1}
              </div>
              <span
                className={cn(
                  "text-sm truncate transition-colors duration-200",
                  actual && "font-medium text-smnyl-text",
                  completado && "text-smnyl-text",
                  !completado && !actual && "text-smnyl-text-muted",
                )}
              >
                {paso}
              </span>
            </div>
            {idx < pasos.length - 1 && (
              <div
                className={cn(
                  "h-px flex-1 transition-colors duration-300",
                  idx < actualIdx ? "bg-smnyl-success-dark" : "bg-smnyl-border",
                )}
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}
