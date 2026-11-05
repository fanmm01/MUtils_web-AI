// Run a dependency's CLI with the current Node binary instead of an npm .bin
// shim. On Windows, cmd.exe treats "&" in the shim's absolute path as a command
// separator, and this repository's path contains "&".
//
// Usage: node scripts/run-bin.mjs <package> <bin> [args...]
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";

const [pkg, bin, ...args] = process.argv.slice(2);
if (!pkg || !bin) {
  console.error("usage: node scripts/run-bin.mjs <package> <bin> [args...]");
  process.exit(2);
}

const require = createRequire(import.meta.url);
const dir = (require.resolve.paths(pkg) ?? [])
  .map((base) => join(base, pkg))
  .find((candidate) => existsSync(join(candidate, "package.json")));
if (!dir) {
  console.error(`run-bin: cannot find package ${pkg}; run npm ci first`);
  process.exit(1);
}

const manifest = JSON.parse(readFileSync(join(dir, "package.json"), "utf8"));
const entry = typeof manifest.bin === "string" ? manifest.bin : manifest.bin?.[bin];
if (!entry) {
  console.error(`run-bin: package ${pkg} has no bin named ${bin}`);
  process.exit(1);
}

const result = spawnSync(process.execPath, [join(dir, entry), ...args], { stdio: "inherit" });
process.exit(result.status ?? 1);
