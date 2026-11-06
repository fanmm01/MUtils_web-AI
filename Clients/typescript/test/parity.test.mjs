// OpenAPI parity gate for the shared SDK.
//
// Compile time (`npm run typecheck`): src/generated/* must match docs/*.json and
// every method's path, HTTP method, request body and success body come from the
// generated `paths` type. Run time (this file): every operation of
// docs/openapi.json is reached by an SDK entry point, and every SDK method sends
// its operation's method, path, required query/header parameters and a JSON
// body exactly when the contract declares one.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createClient } from "../src/client.ts";
import { subscribeAnswer, subscribeJob } from "../src/sse.ts";

const openapi = JSON.parse(
  readFileSync(new URL("../../../docs/openapi.json", import.meta.url), "utf8"),
);
const HTTP_METHODS = new Set(["get", "post", "put", "patch", "delete"]);

/** Operations the SDK deliberately does not expose, with the reason. */
const EXCLUDED = {
  issue_ticket_v1_widget_tickets_post:
    "widget tickets are issued by the host's own backend after its identity check (plan §4.10)",
};
/** Operations whose body the contract cannot declare. */
const RAW_BODY = {
  upload_file_v1_uploads__batch_id__files_put:
    "the route reads the raw request stream, which FastAPI does not describe in OpenAPI",
};

const operations = Object.entries(openapi.paths).flatMap(([template, item]) =>
  Object.entries(item)
    .filter(([method]) => HTTP_METHODS.has(method))
    .map(([method, op]) => ({
      id: op.operationId,
      method: method.toUpperCase(),
      template,
      params: (template.match(/\{/g) ?? []).length,
      pattern: new RegExp(
        `^${template
          .split("/")
          .map((part) => (part.startsWith("{") ? "[^/]+" : part.replace(/[.*+?^$()|[\]\\]/g, "\\$&")))
          .join("/")}$`,
      ),
      requiredQuery: (op.parameters ?? []).filter((p) => p.in === "query" && p.required).map((p) => p.name),
      requiredHeaders: (op.parameters ?? []).filter((p) => p.in === "header" && p.required).map((p) => p.name),
      hasBody: Boolean(op.requestBody),
      bodyRequired: Boolean(op.requestBody?.required),
    })),
);

const key = { idempotencyKey: "key-1" };
const selection = { mode: "auto" };
const source = { source_id: "s1", kb_id: "kb1", kind: "upload", display_name: "d", revision: "r1" };
const profile = { name: "p", roles: [] };

/** One sample call per SDK method. Bodies are placeholders: shape is checked by tsc. */
const CALLS = {
  health: (c) => c.health(),
  readiness: (c) => c.readiness(),
  capabilities: (c) => c.capabilities(),
  listKBs: (c) => c.listKBs({ limit: 10 }),
  createKB: (c) => c.createKB({ name: "n" }),
  getKB: (c) => c.getKB("kb1"),
  updateKB: (c) => c.updateKB("kb1", { name: "n" }, "etag-1"),
  deleteKB: (c) => c.deleteKB("kb1", "etag-1"),
  publishKB: (c) => c.publishKB("kb1", {}),
  listDocuments: (c) => c.listDocuments("kb1"),
  createDocument: (c) => c.createDocument("kb1", { kb_id: "kb1", title: "t" }),
  getDocument: (c) => c.getDocument("d1"),
  updateDocument: (c) => c.updateDocument("d1", { kb_id: "kb1", title: "t" }),
  deleteDocument: (c) => c.deleteDocument("d1", "r1"),
  listQA: (c) => c.listQA("kb1"),
  createQA: (c) => c.createQA("kb1", { kb_id: "kb1", question: "q", answer: "a" }),
  getQA: (c) => c.getQA("q1"),
  updateQA: (c) => c.updateQA("q1", { kb_id: "kb1", question: "q", answer: "a" }),
  deleteQA: (c) => c.deleteQA("q1", "r1"),
  listSourceRoots: (c) => c.listSourceRoots(),
  scanSourceRoot: (c) => c.scanSourceRoot("root1"),
  listSources: (c) => c.listSources("kb1"),
  createSource: (c) => c.createSource("kb1", source),
  getSource: (c) => c.getSource("s1"),
  updateSource: (c) => c.updateSource("s1", source),
  deleteSource: (c) => c.deleteSource("s1"),
  syncSource: (c) => c.syncSource("s1", {}),
  beginUpload: (c) => c.beginUpload({ source_id: "s1" }),
  putUploadFile: (c) => c.putUploadFile("b1", "docs/a.md", new Blob(["# a"])),
  completeUpload: (c) => c.completeUpload("b1"),
  previewImport: (c) => c.previewImport("kb1", { kb_id: "kb1", source_id: "s1" }),
  importDocuments: (c) =>
    c.importDocuments("kb1", { kb_id: "kb1", source_id: "s1", expected_preview_hash: "h" }),
  listVersions: (c) => c.listVersions("kb1"),
  getVersion: (c) => c.getVersion("v1"),
  diffVersions: (c) => c.diffVersions("kb1", "v1", "v2"),
  publishVersion: (c) => c.publishVersion("v1", {}),
  rollbackVersion: (c) => c.rollbackVersion("kb1", { target_version_id: "v1" }),
  getJob: (c) => c.getJob("j1"),
  cancelJob: (c) => c.cancelJob("j1"),
  jobEvents: (c) => c.jobEvents("j1", 3),
  getKnowledgeCatalog: (c) => c.getKnowledgeCatalog(),
  previewSelection: (c) => c.previewSelection({ question: "q", selection }),
  getSessionSelection: (c) => c.getSessionSelection("s1"),
  setSessionSelection: (c) =>
    c.setSessionSelection("s1", { selection, expected_scope_revision: 1 }),
  search: (c) => c.search({ question: "q" }),
  ask: (c) => c.ask({ question: "q" }),
  createSession: (c) => c.createSession({}),
  getHistory: (c) => c.getHistory("s1"),
  submitAnswer: (c) => c.submitAnswer("s1", { question: "q" }),
  getAnswer: (c) => c.getAnswer("a1"),
  cancelAnswer: (c) => c.cancelAnswer("a1"),
  getCitation: (c) => c.getCitation("a1", "c1"),
  submitFeedback: (c) => c.submitFeedback("a1", { rating: "like" }),
  listIssues: (c) => c.listIssues({ status: "open" }),
  getIssue: (c) => c.getIssue("i1"),
  resolveIssue: (c) => c.resolveIssue("i1", {}),
  retestIssue: (c) => c.retestIssue("i1", {}),
  modelCapabilities: (c) => c.modelCapabilities(),
  discoverRuntimes: (c) => c.discoverRuntimes(["t1"]),
  listRuntimes: (c) => c.listRuntimes(),
  listModels: (c) => c.listModels(),
  getModel: (c) => c.getModel("m1"),
  listProfiles: (c) => c.listProfiles(),
  createProfile: (c) => c.createProfile(profile),
  getProfile: (c) => c.getProfile("p1"),
  putProfile: (c) => c.putProfile("p1", profile),
  disableProfile: (c) => c.disableProfile("p1", profile),
  getSessionInference: (c) => c.getSessionInference("s1"),
  setSessionInference: (c) =>
    c.setSessionInference("s1", { inference: {}, expected_inference_revision: 1 }),
  previewInstall: (c) => c.previewInstall({ target_id: "t1", model_ref: "m" }),
  confirmInstall: (c) => c.confirmInstall({ preview_id: "p", preview_hash: "h", confirmed: true }, key),
  verifyModel: (c) => c.verifyModel("m1", { roles: ["generator"] }, key),
};
/** Independent method-to-operation mapping; coverage alone cannot detect two swapped SDK methods. */
const EXPECTED_OPERATIONS = {
  health: "health_healthz_get",
  readiness: "readiness_readyz_get",
  capabilities: "capabilities_v1_capabilities_get",
  listKBs: "list_kbs_v1_kbs_get",
  createKB: "create_kb_v1_kbs_post",
  getKB: "get_kb_v1_kbs__kb_id__get",
  updateKB: "update_kb_v1_kbs__kb_id__patch",
  deleteKB: "delete_kb_v1_kbs__kb_id__delete",
  publishKB: "publish_kb_v1_kbs__kb_id__publish_post",
  listDocuments: "list_documents_v1_kbs__kb_id__documents_get",
  createDocument: "create_document_v1_kbs__kb_id__documents_post",
  getDocument: "get_document_v1_documents__document_id__get",
  updateDocument: "update_document_v1_documents__document_id__patch",
  deleteDocument: "delete_document_v1_documents__document_id__delete",
  listQA: "list_qa_v1_kbs__kb_id__qa_pairs_get",
  createQA: "create_qa_v1_kbs__kb_id__qa_pairs_post",
  getQA: "get_qa_v1_qa_pairs__qa_id__get",
  updateQA: "update_qa_v1_qa_pairs__qa_id__patch",
  deleteQA: "delete_qa_v1_qa_pairs__qa_id__delete",
  listSourceRoots: "list_roots_v1_source_roots_get",
  scanSourceRoot: "scan_source_v1_source_roots__root_id__scan_post",
  listSources: "list_sources_v1_kbs__kb_id__sources_get",
  createSource: "create_source_v1_kbs__kb_id__sources_post",
  getSource: "get_source_v1_sources__source_id__get",
  updateSource: "update_source_v1_sources__source_id__patch",
  deleteSource: "delete_source_v1_sources__source_id__delete",
  syncSource: "sync_source_v1_sources__source_id__sync_post",
  beginUpload: "begin_upload_v1_uploads_post",
  putUploadFile: "upload_file_v1_uploads__batch_id__files_put",
  completeUpload: "complete_upload_v1_uploads__batch_id__complete_post",
  previewImport: "preview_import_v1_kbs__kb_id__imports_preview_post",
  importDocuments: "import_documents_v1_kbs__kb_id__imports_post",
  listVersions: "list_versions_v1_kbs__kb_id__versions_get",
  getVersion: "get_version_v1_versions__version_id__get",
  diffVersions: "diff_versions_v1_kbs__kb_id__version_diff_get",
  publishVersion: "publish_version_v1_versions__version_id__publish_post",
  rollbackVersion: "rollback_version_v1_kbs__kb_id__rollback_post",
  getJob: "get_job_v1_jobs__job_id__get",
  cancelJob: "cancel_job_v1_jobs__job_id__cancel_post",
  jobEvents: "job_events_v1_jobs__job_id__events_get",
  getKnowledgeCatalog: "list_retrievable_kbs_v1_knowledge_catalog_get",
  previewSelection: "preview_selection_v1_knowledge_selection_preview_post",
  getSessionSelection: "get_session_selection_v1_sessions__session_id__selection_get",
  setSessionSelection: "update_session_selection_v1_sessions__session_id__selection_patch",
  search: "search_v1_search_post",
  ask: "ask_v1_ask_post",
  createSession: "create_session_v1_sessions_post",
  getHistory: "history_v1_sessions__session_id__history_get",
  submitAnswer: "submit_answer_v1_sessions__session_id__answers_post",
  getAnswer: "get_answer_v1_answers__answer_id__get",
  cancelAnswer: "cancel_answer_v1_answers__answer_id__cancel_post",
  getCitation: "get_citation_v1_answers__answer_id__citations__citation_id__get",
  submitFeedback: "submit_feedback_v1_answers__answer_id__feedback_post",
  listIssues: "list_issues_v1_issues_get",
  getIssue: "get_issue_v1_issues__issue_id__get",
  resolveIssue: "resolve_issue_v1_issues__issue_id__patch",
  retestIssue: "retest_issue_v1_issues__issue_id__retest_post",
  modelCapabilities: "model_capabilities_v1_models_capabilities_get",
  discoverRuntimes: "discover_runtimes_v1_models_discovery_post",
  listRuntimes: "list_runtimes_v1_models_runtimes_get",
  listModels: "list_models_v1_models_get",
  getModel: "get_model_v1_models__model_id__get",
  listProfiles: "list_profiles_v1_inference_profiles_get",
  createProfile: "create_profile_v1_inference_profiles_post",
  getProfile: "get_profile_v1_inference_profiles__profile_id__get",
  putProfile: "update_profile_v1_inference_profiles__profile_id__put",
  disableProfile: "disable_profile_v1_inference_profiles__profile_id__disable_post",
  getSessionInference: "get_session_inference_v1_sessions__session_id__inference_get",
  setSessionInference: "update_session_inference_v1_sessions__session_id__inference_patch",
  previewInstall: "preview_install_v1_model_installs_preview_post",
  confirmInstall: "confirm_install_v1_model_installs_post",
  verifyModel: "verify_model_v1_models__model_id__verifications_post",
  subscribeAnswer: "answer_events_v1_answers__answer_id__events_get",
  subscribeJob: "job_events_v1_jobs__job_id__events_get",
};

/** SSE entry points live in sse.ts and take the client as their first argument. */
const STREAMS = {
  subscribeAnswer: (c) => subscribeAnswer(c, "a1", { onEvent() {}, reconnect: false }),
  subscribeJob: (c) => subscribeJob(c, "j1", { onEvent() {}, reconnect: false }),
};
const SSE_BODY = {
  answer: 'id: 1\ndata: {"answer_id":"a1","session_id":"s1","seq":1,"event":"answer.cancelled"}\n\n',
  job: 'id: 1\ndata: {"job_id":"j1","seq":1,"event":"job.completed"}\n\n',
};

function recorder() {
  const calls = [];
  const fetchImpl = async (url, init = {}) => {
    calls.push({ url: new URL(String(url)), method: init.method ?? "GET", headers: init.headers ?? {}, body: init.body });
    const accept = String((init.headers ?? {}).Accept ?? "");
    if (accept.includes("text/event-stream")) {
      const kind = String(url).includes("/v1/jobs/") ? "job" : "answer";
      return new Response(SSE_BODY[kind], { status: 200, headers: { "content-type": "text/event-stream" } });
    }
    return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
  };
  return { calls, client: createClient({ baseUrl: "http://api.test", fetch: fetchImpl }) };
}

/** The contract operation a recorded request reaches; static segments win over {params}. */
function operationOf(call) {
  const candidates = operations
    .filter((op) => op.method === call.method && op.pattern.test(call.url.pathname))
    .sort((a, b) => a.params - b.params);
  return candidates[0];
}

const headerNames = (headers) => new Set(Object.keys(headers).map((name) => name.toLowerCase()));

test("every SDK method sends its expected contract operation with the required parameters", async () => {
  const invocations = { ...CALLS, ...STREAMS };
  assert.deepEqual(Object.keys(EXPECTED_OPERATIONS).sort(), Object.keys(invocations).sort());
  for (const [name, invoke] of Object.entries(invocations)) {
    const { calls, client } = recorder();
    await invoke(client);
    assert.equal(calls.length, 1, `${name}: expected one request, got ${calls.length}`);
    const [call] = calls;
    const op = operationOf(call);
    assert.ok(op, `${name}: ${call.method} ${call.url.pathname} is not a contract operation`);
    assert.equal(op.id, EXPECTED_OPERATIONS[name], `${name}: wrong contract operation`);
    for (const param of op.requiredQuery) {
      assert.ok(call.url.searchParams.has(param), `${name}: missing required query ${param}`);
    }
    const sent = headerNames(call.headers);
    for (const header of op.requiredHeaders) {
      assert.ok(sent.has(header.toLowerCase()), `${name}: missing required header ${header}`);
    }
    if (op.id in RAW_BODY) {
      assert.ok(call.body instanceof Blob, `${name}: expected a raw file body`);
      assert.equal(call.headers["Content-Type"], "application/octet-stream");
    } else if (op.hasBody) {
      assert.equal(typeof call.body, "string", `${name}: ${op.id} declares a JSON body`);
      assert.equal(call.headers["Content-Type"], "application/json");
    } else {
      assert.equal(call.body, undefined, `${name}: ${op.id} declares no request body`);
    }
  }
});

test("every OpenAPI operation is reached by an SDK entry point or excluded with a reason", async () => {
  const reached = new Set();
  for (const invoke of Object.values({ ...CALLS, ...STREAMS })) {
    const { calls, client } = recorder();
    await invoke(client);
    for (const call of calls) reached.add(operationOf(call)?.id);
  }
  const ids = new Set(operations.map((op) => op.id));
  for (const id of [...Object.keys(EXCLUDED), ...Object.keys(RAW_BODY)]) {
    assert.ok(ids.has(id), `listed operation ${id} no longer exists in docs/openapi.json`);
  }
  const missing = [...ids].filter((id) => !reached.has(id) && !(id in EXCLUDED));
  assert.deepEqual(missing, [], "operations without an SDK method");
  for (const id of Object.keys(EXCLUDED)) {
    assert.ok(!reached.has(id), `${id} is excluded but an SDK method calls it`);
  }
});

test("the parity table lists exactly the SDK's methods", () => {
  const { client } = recorder();
  const methods = Object.keys(client).filter((name) => !["request", "stream"].includes(name));
  assert.deepEqual(methods.sort(), Object.keys(CALLS).sort());
});
