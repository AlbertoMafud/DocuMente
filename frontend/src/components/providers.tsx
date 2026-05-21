/**
 * Providers raíz — TanStack Query + Sonner toaster.
 *
 * Se monta una sola vez en el layout root. El QueryClient se crea con
 * useState para evitar recreación en cada render (anti-pattern común).
 */
"use client";

import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      }),
  );
  return (
    <QueryClientProvider client={client}>
      {children}
      <Toaster
        position="bottom-right"
        richColors
        toastOptions={{
          className: "font-body",
        }}
      />
    </QueryClientProvider>
  );
}
