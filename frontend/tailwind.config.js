/** Tokens from the "Precision Technical Monochrome" design system. */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#090a0f",
        slate2: "#374151",
        muted: "#525866",
        canvas: "#f7f9fd",
        soft: "#f9fafb",
        soft2: "#f3f4f6",
        line: "#e5e7eb",
        line2: "#d1d5db",
        crit: { bg: "#fef2f2", line: "#fca5a5", ink: "#b91c1c" },
        warn: { bg: "#fffbeb", line: "#fcd34d", ink: "#b45309" },
        ok: { bg: "#f0fdf4", line: "#86efac", ink: "#15803d" },
        info: { bg: "#eff6ff", line: "#93c5fd", ink: "#1d4ed8" },
      },
      fontFamily: {
        sans: ['"Inter Variable"', "Inter", "system-ui", "-apple-system", '"Segoe UI"', "sans-serif"],
        mono: ['"JetBrains Mono Variable"', '"JetBrains Mono"', "ui-monospace", "Consolas", "monospace"],
      },
      fontSize: {
        caps: ["11px", { lineHeight: "16px", letterSpacing: "0.06em", fontWeight: "600" }],
        sm2: ["13px", { lineHeight: "18px" }],
        base2: ["14px", { lineHeight: "22px", letterSpacing: "-0.005em" }],
        h3: ["16px", { lineHeight: "24px", letterSpacing: "-0.01em", fontWeight: "600" }],
        h2: ["20px", { lineHeight: "28px", letterSpacing: "-0.015em", fontWeight: "600" }],
        h1: ["32px", { lineHeight: "40px", letterSpacing: "-0.025em", fontWeight: "700" }],
        display: ["40px", { lineHeight: "48px", letterSpacing: "-0.03em", fontWeight: "700" }],
        stat: ["28px", { lineHeight: "32px", letterSpacing: "-0.02em", fontWeight: "600" }],
      },
      borderRadius: { DEFAULT: "6px", lg: "8px", xl: "12px" },
    },
  },
  plugins: [],
};
