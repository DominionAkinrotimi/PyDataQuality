/**
 * "Precision Technical Monochrome", the app's system, turned inside out: the site sits on the app's
 * ink colour and the app's white surfaces appear on it as sheets of paper. Colour still means
 * only one of four things: problem, warning, passed, information.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#090a0f",
        night: { 1: "#0d0f15", 2: "#12151d", 3: "#1a1e29" },
        fog: "#a3aab8",
        haze: "#8a92a3",
        slate2: "#374151",
        muted: "#525866",
        paper: "#f7f9fd",
        soft: "#f9fafb",
        soft2: "#f3f4f6",
        line: "#e5e7eb",
        line2: "#d1d5db",
        crit: { bg: "#fef2f2", line: "#fca5a5", ink: "#b91c1c", glow: "#f87171" },
        warn: { bg: "#fffbeb", line: "#fcd34d", ink: "#b45309", glow: "#fbbf24" },
        ok: { bg: "#f0fdf4", line: "#86efac", ink: "#15803d", glow: "#4ade80" },
        info: { bg: "#eff6ff", line: "#93c5fd", ink: "#1d4ed8", glow: "#60a5fa" },
      },
      fontFamily: {
        sans: ['"Inter Variable"', "system-ui", "-apple-system", '"Segoe UI"', "sans-serif"],
        display: ['"Inter Tight Variable"', '"Inter Variable"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono Variable"', "ui-monospace", "Consolas", "monospace"],
      },
      maxWidth: { site: "1200px" },
      boxShadow: {
        sheet: "0 50px 100px -30px rgba(0,0,0,0.85), 0 20px 40px -20px rgba(0,0,0,0.7)",
        lift: "0 24px 48px -24px rgba(0,0,0,0.8)",
      },
    },
  },
  plugins: [],
};
