import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The build is committed to the Python package so that `pip install` needs no Node.
// For development run `pdq ui --port 8765 --no-browser` and `npm run dev` side by side.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../pydataquality/static/app",
    emptyOutDir: true,
    assetsDir: "assets",
    sourcemap: false,
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8765",
      "/download": "http://127.0.0.1:8765",
    },
  },
});
