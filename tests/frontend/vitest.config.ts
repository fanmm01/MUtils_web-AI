import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const repo = fileURLToPath(new URL("../../", import.meta.url));

// Rooted at the repository so the run is the same from WebUI/ (npm workspace
// script) or from the repository root.
export default defineConfig({
  root: repo,
  resolve: {
    alias: {
      "@qa/client": `${repo}Clients/typescript/src/index.ts`,
      "@qa/widget": `${repo}WebWidget/src/index.ts`,
    },
  },
  test: {
    include: ["tests/frontend/**/*.spec.ts"],
    environment: "jsdom",
    // import.meta.url is not a file: URL inside the jsdom environment, so the
    // static checks get the repository path from here.
    env: { QA_REPO_ROOT: repo },
  },
});
