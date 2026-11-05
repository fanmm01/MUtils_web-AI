// Run the workspace's TypeScript compiler without going through an npm .bin
// shim. On Windows, cmd.exe treats ``&`` in the shim's absolute path as a
// command separator, so shims break when the repository path contains one.
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const tsc = require.resolve("typescript/bin/tsc");
const result = spawnSync(process.execPath, [tsc, ...process.argv.slice(2)], {
  stdio: "inherit",
});
process.exit(result.status ?? 1);
