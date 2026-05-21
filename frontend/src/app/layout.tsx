/**
 * Root layout — provee QueryClient + sidebar+topbar shell.
 *
 * Las rutas que no quieran el shell (ej. /auth/login eventualmente) pueden
 * crear su propio layout en (auth)/layout.tsx con su propio retorno.
 */
import type { Metadata } from "next";

import { Providers } from "@/components/providers";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";

import "./globals.css";

export const metadata: Metadata = {
  title: "DocuMente — SMNYL",
  description:
    "Sistema agéntico de documentación institucional para Seguros Monterrey New York Life.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-background text-foreground antialiased">
        <Providers>
          <div className="flex h-screen w-screen overflow-hidden">
            <Sidebar />
            <div className="flex flex-1 flex-col overflow-hidden">
              <Topbar />
              <main className="flex-1 overflow-y-auto bg-white">
                <div className="mx-auto w-full max-w-7xl px-6 py-8">{children}</div>
              </main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
