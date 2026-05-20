/**
 * BrandLogo — logo custom de DocuMente.
 *
 * Cerebro estilizado encima de un libro abierto. Representa la propuesta
 * de valor: conocimiento (cerebro) capturado como documento (libro).
 *
 * SVG inline trazado a mano sobre un viewBox 32x32, stroke blanco sobre
 * fondo gradient SMNYL. Escalable a cualquier tamaño manteniendo nitidez.
 */
import { cn } from "@/lib/utils";

interface BrandLogoProps {
  size?: number;
  className?: string;
}

export function BrandLogo({ size = 36, className }: BrandLogoProps) {
  return (
    <div
      className={cn(
        "relative inline-flex items-center justify-center rounded-md",
        "bg-gradient-to-br from-smnyl-primary via-smnyl-primary to-smnyl-primary-dark",
        "shadow-smnyl-sm ring-1 ring-white/10",
        className,
      )}
      style={{ width: size, height: size }}
      aria-label="DocuMente"
    >
      <svg
        viewBox="0 0 32 32"
        fill="none"
        stroke="white"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ width: size * 0.66, height: size * 0.66 }}
        aria-hidden="true"
      >
        {/* Cerebro — hemisferio izquierdo */}
        <path
          d="M13 5
             C 11 5, 9.5 6.2, 9.5 7.8
             C 8.2 8.3, 7.5 9.4, 7.5 10.6
             C 7.5 11.7, 8 12.5, 8.8 13
             C 8.4 13.5, 8.3 14.2, 8.6 14.8
             C 9.1 15.6, 10.2 16, 11.3 15.8
             L 16 15.5
             L 16 5.5
             C 15 5, 14 5, 13 5 Z"
        />
        {/* Cerebro — hemisferio derecho */}
        <path
          d="M19 5
             C 21 5, 22.5 6.2, 22.5 7.8
             C 23.8 8.3, 24.5 9.4, 24.5 10.6
             C 24.5 11.7, 24 12.5, 23.2 13
             C 23.6 13.5, 23.7 14.2, 23.4 14.8
             C 22.9 15.6, 21.8 16, 20.7 15.8
             L 16 15.5
             L 16 5.5
             C 17 5, 18 5, 19 5 Z"
        />
        {/* División central cerebro */}
        <line x1="16" y1="6" x2="16" y2="15.5" strokeOpacity="0.55" />
        {/* Pliegue izquierdo */}
        <path d="M11.5 8.5 Q 13 10, 12 11.5" strokeOpacity="0.55" />
        {/* Pliegue derecho */}
        <path d="M20.5 8.5 Q 19 10, 20 11.5" strokeOpacity="0.55" />

        {/* Libro abierto — lomo central + páginas */}
        <path
          d="M16 19
             L 16 27
             M 16 19
             C 13 17.5, 8 17.5, 4 18.5
             L 4 26
             C 8 25, 13 25, 16 26.5
             C 19 25, 24 25, 28 26
             L 28 18.5
             C 24 17.5, 19 17.5, 16 19 Z"
        />
        {/* Líneas de texto en páginas (sutil) */}
        <line x1="6.5" y1="20.5" x2="13" y2="20" strokeOpacity="0.45" strokeWidth="1" />
        <line x1="6.5" y1="22.5" x2="13" y2="22" strokeOpacity="0.45" strokeWidth="1" />
        <line x1="19" y1="20" x2="25.5" y2="20.5" strokeOpacity="0.45" strokeWidth="1" />
        <line x1="19" y1="22" x2="25.5" y2="22.5" strokeOpacity="0.45" strokeWidth="1" />
      </svg>
    </div>
  );
}
