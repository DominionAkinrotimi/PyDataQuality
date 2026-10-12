/** Same "Precision Technical Monochrome" tokens as the app, with a display face for headlines. */
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
        sans: ['"Inter Variable"', "system-ui", "-apple-system", '"Segoe UI"', "sans-serif"],
        display: ['"Inter Tight Variable"', '"Inter Variable"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono Variable"', "ui-monospace", "Consolas", "monospace"],
      },
      keyframes: {
        marquee: { from: { transform: "translateX(0)" }, to: { transform: "translateX(calc(-100% - var(--gap)))" } },
        "marquee-vertical": { from: { transform: "translateY(0)" }, to: { transform: "translateY(calc(-100% - var(--gap)))" } },
      },
      animation: {
        marquee: "marquee var(--duration) infinite linear",
        "marquee-vertical": "marquee-vertical var(--duration) linear infinite",
      },
      maxWidth: { site: "1180px" },
    },
  },
  plugins: [],
};
