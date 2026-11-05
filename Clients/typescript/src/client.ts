/**
 * Small typed HTTP client for the Q&A assistant API.
 *
 * A browser cannot set arbitrary request headers or read a bearer token from
 * nowhere: the host injects a credential getter. Endpoints are fixed by the
 * application; a caller can never pass a provider URL or secret through here.
 */

import type {
  AskResponse,
  Id,
  InferenceSelection,
  Job,
  ModelRef,
  Page,
  RetrievalSelection,
  SSEEvent,
  Session,
  ApiErrorBody,
  ErrorDetail,
  Hit,
  KnowledgeBase,
  InstallPreview,
  Answer,
  Citation,
} from "./types.js";

export class QAError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: ErrorDetail[];
  readonly requestId?: string;

  constructor(
    code: string,
    message: string,
    status: number,
    details: ErrorDetail[] = [],
    requestId?: string,
  ) {
    super(message);
    this.name = "QAError";
    this.code = code;
    this.status = status;
    this.details = details;
    this.requestId = requestId;
  }
}

export interface ClientOptions {
  baseUrl: string;
  /** Host-injected credential source; never persisted by the client. */
  getCredential?: () => string | null | Promise<string | null>;
  fetch?: typeof fetch;
  timeoutMs?: number;
}

export interface RequestOptions {
  signal?: AbortSignal;
  idempotencyKey?: string;
  query?: Record<string, string | number | boolean | null | undefined>;
}

export interface Client {
  health(): Promise<{ status: string; mode: string }>;
  capabilities(): Promise<Record<string, unknown>>;

  createKB(body: Partial<KnowledgeBase>): Promise<KnowledgeBase>;
  listKBs(query?: Record<string, string | number>): Promise<Page<KnowledgeBase>>;
  getKB(kbId: Id): Promise<KnowledgeBase>;
  updateKB(kbId: Id, body: Partial<KnowledgeBase>): Promise<KnowledgeBase>;
  deleteKB(kbId: Id, expectedEtag?: string): Promise<void>;

  getKnowledgeCatalog(): Promise<Page<Record<string, unknown>>>;
  previewSelection(body: Record<string, unknown>): Promise<Record<string, unknown>>;
  getSessionSelection(sessionId: Id): Promise<Record<string, unknown>>;
  setSessionSelection(
    sessionId: Id,
    body: { selection: RetrievalSelection; expected_scope_revision: number },
  ): Promise<Session>;

  search(body: {
    question: string;
    selection?: RetrievalSelection | null;
    inference?: InferenceSelection | null;
    top_k?: number;
  }, options?: RequestOptions): Promise<{ hits: Hit[] }>;

  ask(body: {
    question: string;
    session_id?: Id | null;
    selection?: RetrievalSelection | null;
    inference?: InferenceSelection | null;
  }, options?: RequestOptions): Promise<AskResponse>;

  createSession(body: {
    selection?: RetrievalSelection | null;
    inference?: InferenceSelection | null;
  }): Promise<Session>;
  getHistory(sessionId: Id): Promise<unknown[]>;
  submitAnswer(
    sessionId: Id,
    body: {
      question: string;
      selection?: RetrievalSelection | null;
      inference?: InferenceSelection | null;
    },
    options?: RequestOptions,
  ): Promise<AskResponse>;
  getAnswer(answerId: Id): Promise<Answer>;
  cancelAnswer(answerId: Id): Promise<Answer>;
  getCitation(answerId: Id, citationId: Id): Promise<Citation>;

  submitFeedback(answerId: Id, body: { rating: "like" | "dislike"; comment?: string }): Promise<unknown>;
  listIssues(query?: Record<string, string>): Promise<unknown[]>;

  modelCapabilities(): Promise<Record<string, unknown>>;
  discoverRuntimes(targetIds: Id[]): Promise<Record<string, unknown>>;
  listRuntimes(): Promise<unknown[]>;
  listModels(query?: Record<string, string | number>): Promise<Page<ModelRef>>;
  listProfiles(): Promise<Page<Record<string, unknown>>>;
  getProfile(profileId: Id, revision?: Id): Promise<Record<string, unknown>>;
  putProfile(profileId: Id, body: Record<string, unknown>): Promise<Record<string, unknown>>;
  disableProfile(profileId: Id, body: { expected_revision: Id }): Promise<Record<string, unknown>>;
  previewInstall(body: { target_id: Id; model_ref: string }): Promise<InstallPreview>;
  confirmInstall(
    body: { preview_id: Id; preview_hash: string; confirmed: true },
    options?: RequestOptions,
  ): Promise<Job>;
  verifyModel(modelId: Id, body: { roles: string[] }, options?: RequestOptions): Promise<Job>;

  getJob(jobId: Id): Promise<Job>;
  cancelJob(jobId: Id): Promise<Job>;
  getSessionInference(sessionId: Id): Promise<Record<string, unknown>>;
  setSessionInference(
    sessionId: Id,
    body: { inference: InferenceSelection; expected_inference_revision: number },
  ): Promise<Record<string, unknown>>;

  /** Raw transport for SSE helpers and tests; still goes through auth+errors. */
  request<T>(method: string, path: string, init?: {
    body?: unknown;
    options?: RequestOptions;
    rawBody?: BodyInit;
  }): Promise<T>;

  /** Authenticated streaming response (SSE). Rejects non-2xx with ``QAError``. */
  stream(
    path: string,
    init?: { signal?: AbortSignal; headers?: Record<string, string> },
  ): Promise<Response>;
}

export function createClient(options: ClientOptions): Client {
  const doFetch = options.fetch ?? globalThis.fetch?.bind(globalThis);
  if (!doFetch) throw new Error("no fetch implementation is available");
  const baseUrl = options.baseUrl.replace(/\/+$/, "");
  const timeoutMs = options.timeoutMs ?? 30_000;

  async function authHeaders(): Promise<Record<string, string>> {
    const credential = options.getCredential ? await options.getCredential() : null;
    return credential ? { Authorization: `Bearer ${credential}` } : {};
  }

  async function request<T>(
    method: string,
    path: string,
    init: { body?: unknown; options?: RequestOptions; rawBody?: BodyInit } = {},
  ): Promise<T> {
    const { options: reqOptions = {}, body, rawBody } = init;
    const url = new URL(baseUrl + path);
    for (const [key, value] of Object.entries(reqOptions.query ?? {})) {
      if (value !== undefined && value !== null) url.searchParams.set(key, String(value));
    }
    const headers: Record<string, string> = {
      Accept: "application/json",
      ...(await authHeaders()),
    };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (reqOptions.idempotencyKey) headers["Idempotency-Key"] = reqOptions.idempotencyKey;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    if (reqOptions.signal) {
      reqOptions.signal.addEventListener("abort", () => controller.abort(), { once: true });
    }
    try {
      const response = await doFetch(url.toString(), {
        method,
        headers,
        body: rawBody ?? (body === undefined ? undefined : JSON.stringify(body)),
        signal: controller.signal,
      });
      const requestId = response.headers.get("X-Request-ID") ?? undefined;
      const text = await response.text();
      const payload: unknown = text ? safeJson(text) : null;
      if (!response.ok) throw toError(response.status, payload, requestId);
      return payload as T;
    } finally {
      clearTimeout(timer);
    }
  }

  const call = <T>(method: string, path: string, body?: unknown, reqOptions?: RequestOptions) =>
    request<T>(method, path, { body, options: reqOptions });

  async function stream(
    path: string,
    init: { signal?: AbortSignal; headers?: Record<string, string> } = {},
  ): Promise<Response> {
    const headers = {
      Accept: "text/event-stream",
      ...(await authHeaders()),
      ...(init.headers ?? {}),
    };
    const response = await doFetch(baseUrl + path, {
      method: "GET",
      headers,
      signal: init.signal,
    });
    if (!response.ok) {
      const text = await response.text();
      throw toError(
        response.status,
        text ? safeJson(text) : null,
        response.headers.get("X-Request-ID") ?? undefined,
      );
    }
    return response;
  }

  return {
    request,
    stream,
    health: () => call("GET", "/healthz"),
    capabilities: () => call("GET", "/v1/capabilities"),

    createKB: (body) => call("POST", "/v1/kbs", body),
    listKBs: (query) => request("GET", "/v1/kbs", { options: { query } }),
    getKB: (kbId) => call("GET", `/v1/kbs/${encodeURIComponent(kbId)}`),
    updateKB: (kbId, body) => call("PATCH", `/v1/kbs/${encodeURIComponent(kbId)}`, body),
    deleteKB: async (kbId, expectedEtag) => {
      await request("DELETE", `/v1/kbs/${encodeURIComponent(kbId)}`, {
        options: { query: { expected_etag: expectedEtag } },
      });
    },

    getKnowledgeCatalog: () => call("GET", "/v1/knowledge-catalog"),
    previewSelection: (body) => call("POST", "/v1/knowledge-selection/preview", body),
    getSessionSelection: (sessionId) =>
      call("GET", `/v1/sessions/${encodeURIComponent(sessionId)}/selection`),
    setSessionSelection: (sessionId, body) =>
      call("PATCH", `/v1/sessions/${encodeURIComponent(sessionId)}/selection`, body),

    search: (body, reqOptions) => call("POST", "/v1/search", body, reqOptions),
    ask: (body, reqOptions) => call("POST", "/v1/ask", body, reqOptions),
    createSession: (body) => call("POST", "/v1/sessions", body),
    getHistory: (sessionId) => call("GET", `/v1/sessions/${encodeURIComponent(sessionId)}/history`),
    submitAnswer: (sessionId, body, reqOptions) =>
      call("POST", `/v1/sessions/${encodeURIComponent(sessionId)}/answers`, body, reqOptions),
    getAnswer: (answerId) => call("GET", `/v1/answers/${encodeURIComponent(answerId)}`),
    cancelAnswer: (answerId) => call("POST", `/v1/answers/${encodeURIComponent(answerId)}/cancel`),
    getCitation: (answerId, citationId) =>
      call(
        "GET",
        `/v1/answers/${encodeURIComponent(answerId)}/citations/${encodeURIComponent(citationId)}`,
      ),

    submitFeedback: (answerId, body) =>
      call("POST", `/v1/answers/${encodeURIComponent(answerId)}/feedback`, body),
    listIssues: (query) => request("GET", "/v1/issues", { options: { query } }),

    modelCapabilities: () => call("GET", "/v1/models/capabilities"),
    discoverRuntimes: (targetIds) => call("POST", "/v1/models/discovery", { target_ids: targetIds }),
    listRuntimes: () => call("GET", "/v1/models/runtimes"),
    listModels: (query) => request("GET", "/v1/models", { options: { query } }),
    listProfiles: () => call("GET", "/v1/inference-profiles"),
    getProfile: (profileId, revision) =>
      request("GET", `/v1/inference-profiles/${encodeURIComponent(profileId)}`, {
        options: { query: { revision } },
      }),
    putProfile: (profileId, body) =>
      call("PUT", `/v1/inference-profiles/${encodeURIComponent(profileId)}`, body),
    disableProfile: (profileId, body) =>
      call("POST", `/v1/inference-profiles/${encodeURIComponent(profileId)}/disable`, body),
    previewInstall: (body) => call("POST", "/v1/model-installs/preview", body),
    confirmInstall: (body, reqOptions) => call("POST", "/v1/model-installs", body, reqOptions),
    verifyModel: (modelId, body, reqOptions) =>
      call("POST", `/v1/models/${encodeURIComponent(modelId)}/verifications`, body, reqOptions),

    getJob: (jobId) => call("GET", `/v1/jobs/${encodeURIComponent(jobId)}`),
    cancelJob: (jobId) => call("POST", `/v1/jobs/${encodeURIComponent(jobId)}/cancel`),
    getSessionInference: (sessionId) =>
      call("GET", `/v1/sessions/${encodeURIComponent(sessionId)}/inference`),
    setSessionInference: (sessionId, body) =>
      call("PATCH", `/v1/sessions/${encodeURIComponent(sessionId)}/inference`, body),
  };
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function toError(status: number, payload: unknown, requestId?: string): QAError {
  const body = payload as Partial<ApiErrorBody> | null;
  if (body && typeof body === "object" && "error" in body && body.error) {
    return new QAError(
      body.error.code,
      body.error.message,
      status,
      body.error.details ?? [],
      body.request_id ?? requestId,
    );
  }
  return new QAError("INTERNAL_ERROR", "unrecognized error payload", status, [], requestId);
}

export type { SSEEvent };
