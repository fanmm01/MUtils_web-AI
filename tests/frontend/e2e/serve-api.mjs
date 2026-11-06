// Start a throwaway operational backend for the admin E2E run:
//   qa-migrate on a fresh data dir → qa-api (HTTP) + qa-worker (import jobs).
// Playwright starts this as a webServer and stops it after the run.
//
// Chunk sizes are required inputs with no accepted default yet (P2 plan: they
// come from corpus analysis); 120/20 are test-only values for this run, the
// same ones the A1 integration tests use.
import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const repo = fileURLToPath(new URL("../../../", import.meta.url));
const port = process.env.QA_E2E_API_PORT ?? "18765";
const python = join(repo, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
if (!existsSync(python)) {
  console.error(`serve-api: ${python} not found; run \`uv sync --all-packages\` first`);
  process.exit(1);
}

// Deterministic location, wiped at start: a run killed mid-way cannot leak into the next.
const dataDir = join(tmpdir(), `qa-admin-e2e-${port}`);
rmSync(dataDir, { recursive: true, force: true });
mkdirSync(dataDir, { recursive: true });

const env = {
  ...process.env,
  QA_MODE: "operational",
  QA_HOST: "127.0.0.1",
  QA_PORT: port,
  QA_DATA_DIR: dataDir,
  QA_CHUNK_TARGET_TOKENS: "120",
  QA_CHUNK_OVERLAP_TOKENS: "20",
  PYTHONUTF8: "1",
};

const migrate = spawnSync(python, ["-m", "qa_service.migrate"], { env, cwd: repo, stdio: "inherit" });
if (migrate.status !== 0) process.exit(migrate.status ?? 1);

const children = [
  spawn(python, ["-m", "qa_service"], { env, cwd: repo, stdio: "inherit" }),
  spawn(python, ["-m", "qa_service.worker"], { env, cwd: repo, stdio: "inherit" }),
];

let stopping = false;
function stop(code) {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (child.exitCode !== null || child.pid === undefined) continue;
    // The venv python.exe is a launcher with a child interpreter: kill the whole tree.
    if (process.platform === "win32") spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore" });
    else child.kill("SIGTERM");
  }
  process.exit(code);
}
for (const child of children) {
  child.on("exit", (code) => {
    if (!stopping) {
      console.error(`serve-api: a backend process exited (${code}); stopping the others`);
      stop(code ?? 1);
    }
  });
}
for (const signal of ["SIGINT", "SIGTERM", "SIGHUP"]) process.on(signal, () => stop(0));
