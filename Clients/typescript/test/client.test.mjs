import assert from "node:assert/strict";
import { createClient, QAError } from "../src/client.ts";

const calls = [];
const fakeFetch = async (url, init) => {
  calls.push({ url: String(url), init });
  if (String(url).endsWith("/healthz")) {
    return new Response(JSON.stringify({ status: "ok", mode: "scaffold" }), {
      status: 200,
      headers: { "content-type": "application/json", "X-Request-ID": "req-1" },
    });
  }
  if (String(url).endsWith("/v1/ask")) {
    return new Response(
      JSON.stringify({
        error: { code: "FEATURE_NOT_IMPLEMENTED", message: "not yet", details: [] },
        request_id: "req-2",
      }),
      { status: 501, headers: { "content-type": "application/json", "X-Request-ID": "req-2" } },
    );
  }
  return new Response(
    JSON.stringify({
      answer_id: "a1",
      session_id: "s1",
      question: "q",
      status: "pending",
      text: "",
      used_kb_ids: [],
      citations: [],
      created_at: "2026-01-01T00:00:00Z",
    }),
    { status: 200, headers: { "content-type": "application/json" } },
  );
};

const client = createClient({ baseUrl: "http://127.0.0.1:8000", fetch: fakeFetch });

const health = await client.health();
assert.equal(health.status, "ok");
assert.equal(calls[0].url, "http://127.0.0.1:8000/healthz");

await assert.rejects(
  () => client.ask({ question: "hello" }),
  (error) => {
    assert.ok(error instanceof QAError);
    assert.equal(error.code, "FEATURE_NOT_IMPLEMENTED");
    assert.equal(error.status, 501);
    assert.equal(error.requestId, "req-2");
    assert.deepEqual(error.details, []);
    return true;
  },
);

await client.getKB("kb /1");
assert.equal(calls.at(-1).url, "http://127.0.0.1:8000/v1/kbs/kb%20%2F1");

const authCalls = [];
const authed = createClient({
  baseUrl: "http://127.0.0.1:8000",
  getCredential: () => "token-value",
  fetch: async (url, init) => {
    authCalls.push(init);
    return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
  },
});
await authed.getKB("kb");
assert.equal(authCalls[0].headers.Authorization, "Bearer token-value");

const install = { preview_id: "p1", preview_hash: "h", confirmed: true };
const beforeJobs = authCalls.length;
assert.throws(() => authed.confirmInstall(install), /Idempotency-Key is required/);
assert.throws(
  () => authed.verifyModel("m1", { roles: ["generator"] }, { idempotencyKey: " " }),
  /Idempotency-Key is required/,
);
assert.equal(authCalls.length, beforeJobs);
await authed.confirmInstall(install, { idempotencyKey: "install-key" });
await authed.verifyModel("m1", { roles: ["generator"] }, { idempotencyKey: "verify-key" });
assert.equal(authCalls.at(-2).headers["Idempotency-Key"], "install-key");
assert.equal(authCalls.at(-1).headers["Idempotency-Key"], "verify-key");

console.log("typescript scaffold tests passed");
