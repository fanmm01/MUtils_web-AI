import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

const here = (path: string): string => fileURLToPath(new URL(path, import.meta.url));

// One config, two library builds:
// - `vite build` emits dist/qa-widget.js, an ES module for bundlers.
// - `vite build --mode iife` emits dist/qa-widget.iife.js, a classic script that
//   exposes window.QAWidget and auto-mounts from its data attributes.
// The shared SDK is bundled from source, so no SDK build step is required first.
export default defineConfig(({ mode }) => {
  const iife = mode === "iife";
  return {
    resolve: {
      alias: { "@qa/client": here("../Clients/typescript/src/index.ts") },
    },
    build: {
      outDir: "dist",
      emptyOutDir: !iife,
      sourcemap: true,
      lib: iife
        ? {
            entry: here("src/loader.ts"),
            formats: ["iife"],
            name: "QAWidget",
            fileName: () => "qa-widget.iife.js",
          }
        : {
            entry: here("src/index.ts"),
            formats: ["es"],
            fileName: () => "qa-widget.js",
          },
    },
  };
});
