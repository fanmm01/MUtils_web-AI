import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

const here = (path: string): string => fileURLToPath(new URL(path, import.meta.url));

// The dev server proxies API paths to qa-api so the admin UI stays same-origin
// and the API needs no CORS configuration during development.
const apiTarget = process.env.QA_API_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  resolve: {
    alias: { "@qa/client": here("../Clients/typescript/src/index.ts") },
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/v1": apiTarget,
      "/healthz": apiTarget,
      "/readyz": apiTarget,
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: true,
  },
});
