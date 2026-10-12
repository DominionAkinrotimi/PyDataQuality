import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Relative base so the site works at username.github.io/PyDataQuality/ and on a custom domain.
export default defineConfig({
  base: "./",
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
});
