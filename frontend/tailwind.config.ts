/**
 * Tailwind config — tokens SMNYL portados desde src/ui/theme.py.
 *
 * Single source of truth visual: este archivo define la paleta y typography
 * que consumen tanto Tailwind utilities (`bg-smnyl-primary`, `text-smnyl-text`)
 * como las CSS variables expuestas en globals.css (consumidas por shadcn/ui).
 *
 * Cuando theme.py cambie, este archivo debe actualizarse en paralelo. La
 * fuente canónica sigue siendo docs/BRAND_GUIDELINES.md.
 */
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "1.5rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // CSS variables shadcn-compatible (consumidas por componentes shadcn).
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Tokens SMNYL crudos (espejo exacto de SMNYL_COLORS en theme.py).
        smnyl: {
          primary: "#0079c2",
          "primary-dark": "#0a385e",
          bg: "#ffffff",
          "bg-soft": "#f4f5f6",
          text: "#0a3c53",
          "text-muted": "#565656",
          border: "#bdc1c2",
          success: "#4b8b7f",
          "success-dark": "#264640",
          "success-soft": "#e8f0ee",
          warning: "#ce7046",
          "warning-dark": "#544235",
          "warning-soft": "#fdf4ee",
          danger: "#754a62",
          "danger-soft": "#fdf2f6",
          info: "#2e86af",
          "info-dark": "#0a385e",
          "info-soft": "#eef6fb",
          "accent-soft": "#b2d4e4",
        },
      },
      fontFamily: {
        // Mismas fuentes que theme.py — nativas Windows/Mac, sin @import.
        display: ['Georgia', '"Times New Roman"', "serif"],
        body: ['Tahoma', '"Segoe UI"', "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        "smnyl-sm": "0 1px 2px rgba(10, 60, 83, 0.05), 0 1px 1px rgba(10, 60, 83, 0.03)",
        "smnyl-md": "0 4px 12px rgba(10, 60, 83, 0.08), 0 2px 4px rgba(10, 60, 83, 0.04)",
        "smnyl-lg": "0 16px 40px rgba(10, 60, 83, 0.14), 0 4px 8px rgba(10, 60, 83, 0.06)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 200ms ease-out",
        "accordion-up": "accordion-up 200ms ease-out",
        "fade-in": "fade-in 200ms ease-out",
      },
      transitionTimingFunction: {
        // Curva premium estándar (Material Design ease-out)
        "out-smooth": "cubic-bezier(0.4, 0, 0.2, 1)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
