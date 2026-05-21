/**
 * Badge — etiquetas pequeñas para estado MRM, severidad de brechas, etc.
 *
 * Variantes SMNYL: estado DRAFT/IN_REVIEW/APPROVED, severidad CRITICA/ATENCION/SUGERENCIA.
 */
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 " +
    "text-xs font-semibold transition-colors " +
    "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 " +
    "uppercase tracking-wider",
  {
    variants: {
      variant: {
        default: "border-transparent bg-smnyl-primary text-white",
        secondary: "border-transparent bg-smnyl-bg-soft text-smnyl-text",
        // Severidad brechas
        critica: "border-smnyl-danger/40 bg-smnyl-danger-soft text-smnyl-danger",
        atencion: "border-smnyl-warning-dark/30 bg-smnyl-warning-soft text-smnyl-warning-dark",
        sugerencia: "border-smnyl-info-dark/30 bg-smnyl-info-soft text-smnyl-info-dark",
        // Estado MRM
        draft: "border-smnyl-text-muted/30 bg-smnyl-bg-soft text-smnyl-text-muted",
        review: "border-smnyl-warning-dark/30 bg-smnyl-warning-soft text-smnyl-warning-dark",
        approved: "border-smnyl-info-dark/30 bg-smnyl-info-soft text-smnyl-info-dark",
        published: "border-smnyl-success-dark/30 bg-smnyl-success-soft text-smnyl-success-dark",
        outline: "border-smnyl-border text-smnyl-text",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
