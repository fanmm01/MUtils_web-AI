// Generate the SDK's contract types from the frozen Contract Gate artifacts.
//
//   node scripts/generate-types.mjs          rewrite src/generated/*.ts
//   node scripts/generate-types.mjs --check  exit 1 when a generated file is stale
//
// Sources: docs/openapi.json (HTTP) and docs/events.schema.json (SSE answer/job
// events and the error-code table). The SDK must not hand-maintain another copy
// of these shapes; `npm run typecheck` runs --check first, so a contract change
// without regeneration fails the front-end gate.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import openapiTS, { astToString } from "openapi-typescript";

const here = dirname(fileURLToPath(import.meta.url));
const packageDir = join(here, "..");
const repo = join(packageDir, "..", "..");
const outDir = join(packageDir, "src", "generated");
const sources = {
  openapi: join(repo, "docs", "openapi.json"),
  events: join(repo, "docs", "events.schema.json"),
};

const OPTIONS = {
  silent: true,
  // Keep exactly the schema's `required` lists: a defaulted field stays optional.
  defaultNonNullable: false,
  rootTypes: true,
  rootTypesNoSchemaPrefix: true,
  // Keep the contract's own names (KBTarget, QAPair, Page_KnowledgeBase_).
  rootTypesKeepCasing: true,
};

function header(source) {
  const from = relative(repo, source).replaceAll("\\", "/");
  return [
    "/**",
    ` * GENERATED from ${from} by Clients/typescript/scripts/generate-types.mjs.`,
    " * Do not edit. Regenerate with `npm run gen:types -w @qa/client`;",
    " * `npm run typecheck` fails while this file is stale.",
    " */",
    "",
    "",
  ].join("\n");
}

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

/** Wrap the event JSON Schemas in an OpenAPI document so one generator emits them. */
function eventsDocument(events) {
  const schemas = {};
  const hoist = (name, schema) => {
    const { $defs = {}, ...rest } = schema;
    for (const [defName, def] of Object.entries($defs)) {
      if (defName in schemas) throw new Error(`events schema: duplicate $defs name ${defName}`);
      schemas[defName] = def;
    }
    if (name in schemas) throw new Error(`events schema: duplicate schema name ${name}`);
    schemas[name] = rest;
  };
  hoist("AnswerEvent", events.answer_event);
  hoist("JobEvent", events.job_event);
  const rewritten = JSON.parse(
    JSON.stringify(schemas).replaceAll('"#/$defs/', '"#/components/schemas/'),
  );
  return {
    openapi: "3.1.0",
    info: { title: "Q&A assistant events", version: String(events.schema_version) },
    paths: {},
    components: { schemas: rewritten },
  };
}

function literalUnion(values) {
  return [...values].sort().map((value) => JSON.stringify(value)).join(" | ");
}

async function render() {
  const openapi = readJson(sources.openapi);
  const events = readJson(sources.events);
  const httpTypes = astToString(await openapiTS(openapi, OPTIONS));
  const eventTypes = astToString(await openapiTS(eventsDocument(events), OPTIONS));
  const extras = [
    "",
    "/** Stable error codes (events.schema.json `error_codes`). */",
    `export type ErrorCode = ${literalUnion(Object.keys(events.error_codes))};`,
    "/** SSE event schema version and HTTP contract version of the frozen artifacts. */",
    `export type EventSchemaVersion = ${JSON.stringify(events.schema_version)};`,
    `export type HttpSchemaVersion = ${JSON.stringify(events.http_schema_version)};`,
    "",
  ].join("\n");
  return {
    "openapi.ts": header(sources.openapi) + httpTypes,
    "events.ts": header(sources.events) + eventTypes + extras,
  };
}

const normalize = (text) => text.replaceAll("\r\n", "\n");
const files = await render();
const check = process.argv.includes("--check");
const stale = [];
for (const [name, content] of Object.entries(files)) {
  const target = join(outDir, name);
  const current = existsSync(target) ? normalize(readFileSync(target, "utf8")) : null;
  if (current === normalize(content)) continue;
  if (check) {
    stale.push(relative(repo, target));
    continue;
  }
  mkdirSync(outDir, { recursive: true });
  writeFileSync(target, normalize(content));
  console.log(`generated ${relative(repo, target)}`);
}
if (stale.length > 0) {
  console.error(
    `stale generated contract types: ${stale.join(", ")}\n` +
      "run `npm run gen:types -w @qa/client` and commit the result",
  );
  process.exit(1);
}
if (check) console.log("generated contract types are up to date");
