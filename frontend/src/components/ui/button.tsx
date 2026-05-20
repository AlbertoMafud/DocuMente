/**
 * Button — primitive shadcn/ui adaptado a paleta SMNYL.
 *
 * Variantes:
 * - default: primary SMNYL blue, blanco texto
 * - secondary: bg-soft, primary texto
 * - outline: borde primary, primary texto (background blanco)
 * - ghost: sin borde ni bg; hover ligera
 * - destructive: danger SMNYL
 * - link: solo texto subrayado
 */
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md " +
    "text-sm font-medium ring-offset-background " +
    "transition-all duration-200 ease-out " +
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 " +
    "disabled:pointer-events-none disabled:opacity-50 " +
    "[&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-smnyl-primary text-white shadow-smnyl-sm hover:bg-smnyl-primary-dark hover:shadow-smnyl-md hover:-translate-y-px",
        destructive:
          "bg-smnyl-danger text-white shadow-smnyl-sm hover:opacity-90",
        outline:
          "border border-smnyl-primary bg-white text-smnyl-primary shadow-smnyl-sm hover:bg-smnyl-accent-soft/40",
        secondary:
          "bg-smnyl-bg-soft text-smnyl-text hover:bg-smnyl-accent-soft/30",
        ghost: "text-smnyl-text hover:bg-smnyl-bg-soft",
        link: "text-smnyl-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-6 text-base",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
