/**
 * Skeleton loader — placeholders animados mientras llega data del API.
 */
import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-smnyl-bg-soft", className)}
      {...props}
    />
  );
}

export { Skeleton };
