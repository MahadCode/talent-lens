import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        surface: "hsl(var(--surface))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        heading: "hsl(var(--heading))",
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground) / 0.5)",
        },
        border: "hsl(var(--border) / 0.12)",
        success: "hsl(var(--success))",
        warning: "hsl(var(--warning))",
        error: "hsl(var(--error))",
        card: "hsl(var(--card))",
        ink: "hsl(var(--heading))",
      },
      borderRadius: {
        DEFAULT: "2px",
        lg: "4px",
        xl: "6px",
        "2xl": "8px",
      },
      boxShadow: {
        soft: "none",
        card: "none",
        glow: "none",
      },
      backgroundImage: {
        "gradient-brand":
          "conic-gradient(from 200deg, #ffb347, #ff8a3d 18%, #ff5a5f 34%, #ff3d8b 50%, #ff5a5f 66%, #ff8a3d 82%, #ffb347)",
        "gradient-mesh":
          "radial-gradient(at 0% 0%, rgb(255 138 61 / 0.12) 0px, transparent 50%), radial-gradient(at 100% 0%, rgb(255 61 139 / 0.1) 0px, transparent 50%)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Schibsted Grotesk", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "IBM Plex Mono", "ui-monospace", "monospace"],
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out",
        "slide-up": "slide-up 0.4s ease-out",
        shimmer: "shimmer 2s linear infinite",
      },
      keyframes: {
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
