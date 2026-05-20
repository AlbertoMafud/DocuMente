import * as React from "react";

import { cn } from "@/lib/utils";

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-smnyl-border bg-white",
          "px-3 py-2 text-sm ring-offset-background",
          "placeholder:text-smnyl-text-muted/60",
          "transition-all duration-200 ease-out font-mono",
          "focus-visible:outline-none focus-visible:border-smnyl-primary " +
            "focus-visible:ring-2 focus-visible:ring-smnyl-primary/15",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
Textarea.displayName = "Textarea";

export { Textarea };
