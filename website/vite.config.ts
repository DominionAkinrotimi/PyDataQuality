import path from "node:path";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Ask the browser for the fonts as soon as it has the page, so the first screen is laid
 * out once, in the right typeface, instead of again when each font arrives.
 */
function preloadFonts(): Plugin {
  return {
    name: "preload-fonts",
    apply: "build",
    transformIndexHtml(_html, ctx) {
      return Object.keys(ctx.bundle ?? {})
        .filter((file) => /(inter(-tight)?|jetbrains-mono)-latin-wght-normal.*\.woff2$/.test(file))
        .map((file) => ({
          tag: "link",
          attrs: { rel: "preload", as: "font", type: "font/woff2", href: `./${file}`, crossorigin: "" },
          injectTo: "head" as const,
        }));
    },
  };
}

// Relative base so the site works at username.github.io/PyDataQuality/ and on a custom domain.
export default defineConfig({
  base: "./",
  plugins: [react(), preloadFonts()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  // The 3D scene is one large file on purpose: it is fetched on its own, after the page has loaded.
  build: { chunkSizeWarningLimit: 900 },
});
