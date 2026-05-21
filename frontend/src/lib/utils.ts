/**
 * Utility helpers compartidos por todos los componentes.
 *
 * `cn`: combina clases Tailwind manejando conflictos (tailwind-merge) y
 * condicionales (clsx). Patrón canónico de shadcn/ui.
 */
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Formatea un timestamp como tiempo relativo en español:
 * "hace 30 segundos" · "hace 5 minutos" · "hace 2 días" · "hace 3 meses".
 *
 * Espejo del helper formato_relativo de src/ui/components/continue_hero.py.
 */
export function tiempoRelativo(iso: string | Date): string {
  const fecha = typeof iso === "string" ? new Date(iso) : iso;
  const segundos = Math.floor((Date.now() - fecha.getTime()) / 1000);
  if (segundos < 60) return "hace unos segundos";
  if (segundos < 3600) {
    const m = Math.floor(segundos / 60);
    return `hace ${m} minuto${m === 1 ? "" : "s"}`;
  }
  if (segundos < 86400) {
    const h = Math.floor(segundos / 3600);
    return `hace ${h} hora${h === 1 ? "" : "s"}`;
  }
  if (segundos < 86400 * 30) {
    const d = Math.floor(segundos / 86400);
    return `hace ${d} día${d === 1 ? "" : "s"}`;
  }
  const meses = Math.floor(segundos / (86400 * 30));
  return `hace ${meses} ${meses === 1 ? "mes" : "meses"}`;
}
