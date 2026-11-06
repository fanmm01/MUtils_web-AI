/**
 * Typed HTTP client for the Q&A assistant API.
 *
 * Every method is bound to one operation of `docs/openapi.json` through the
 * generated `paths` type: a path, method, request body or success body that
 * differs from the contract fails `tsc`. `test/parity.test.mjs` also checks at
 * run time that every operation has a method and every method calls its
 * operation with the required parameters.
 *
 * A browser cannot set arbitrary request headers or read a bearer token from
 * nowhere: the host injects a credential getter. Endpoints are fixed by the
 * application; a caller can never pass a provider URL or secret through here.
 */

import type { paths } from "./generated/openapi.js";
import type {
  Answer,
  ApiErrorBody,
  AskRequest,
  AskResponse,
  CapabilitiesBody,
  ChangeReceipt,
  CitationDetail,
  CreateKB,
  CreateSession,
  DiscoveryReport,
  DocumentDetail,
  ErrorDetail,
  Feedback,
  FeedbackInput,
  Health,
  Id,
  ImportPreview,
  ImportPreviewRequest,
  ImportRequest,
  InferenceProfile,
  InstallConfirmation,
  InstallPreview,
  InstallRequest,
  Issue,
  IssueResolution,
  Job,
  KnowledgeBase,
  ModelCapabilities,
  ModelRef,
  Page_Document_,
  Page_KBDescriptor_,
  Page_KnowledgeBase_,
  Page_ModelRef_,
  Page_ProfileSummary_,
  Page_QAPair_,
  PublishRequest,
  PutDocument,
  PutInferenceProfile,
  PutQA,
  QAPair,
  Readiness,
  RetestRequest,
  RollbackRequest,
  RuntimeStatus,
  SearchRequest,
  SearchResult,
  Selection,
  SelectionPreviewRequest,
  SelectionResult,
  Session,
  SessionInference,
  SessionSelection,
  Snapshot,
  Source,
  SourceManifest,
  SSEEvent,
  SubmitAnswer,
  Turn,
  UpdateKB,
  UpdateSessionInference,
  UpdateSessionSelection,
  UploadBatch,
  UploadManifest,
  VerifyModelRequest,
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
  /** Per-request timeout; defaults to the client's `timeoutMs`. */
  timeoutMs?: number;
}

export interface IdempotentRequestOptions extends RequestOptions {
  idempotencyKey: string;
}

/* ---- Binding to the generated OpenAPI operations ------------------------- */

type Method = "get" | "post" | "put" | "patch" | "delete";
type Op<P, M> = P extends keyof paths
  ? M extends keyof paths[P]
    ? NonNullable<paths[P][M]>
    : never
  : never;
type PathFor<M extends Method> = {
  [P in keyof paths]-?: [Op<P, M>] extends [never] ? never : P;
}[keyof paths];
type JsonContent<T> = T extends { content: { "application/json": infer B } } ? B : undefined;
type Success<O> = O extends { responses: infer R }
  ? { [S in keyof R]: S extends 200 | 201 | 202 | 204 ? JsonContent<R[S]> : never }[keyof R]
  : never;
type Body<O> = O extends { requestBody?: infer RB } ? JsonContent<RB> : undefined;
type Query<O> = O extends { parameters: { query?: infer Q } } ? Q : undefined;

/** Query parameters of one operation, taken from the generated contract. */
export type OperationQuery<M extends Method, P extends PathFor<M>> = NonNullable<Query<Op<P, M>>>;

interface OpInit<O> {
  path?: Record<string, string>;
  query?: Query<O>;
  body?: Body<O>;
  rawBody?: BodyInit;
  headers?: Record<string, string>;
  options?: RequestOptions;
}

export interface Client {
  health(options?: RequestOptions): Promise<Health>;
  /** 503 is the normal "not ready" answer, so it resolves instead of throwing. */
  readiness(options?: RequestOptions): Promise<Readiness>;
  capabilities(options?: RequestOptions): Promise<CapabilitiesBody>;

  listKBs(query?: OperationQuery<"get", "/v1/kbs">, options?: RequestOptions): Promise<Page_KnowledgeBase_>;
  createKB(body: CreateKB, options?: RequestOptions): Promise<KnowledgeBase>;
  getKB(kbId: Id, options?: RequestOptions): Promise<KnowledgeBase>;
  updateKB(kbId: Id, body: UpdateKB, expectedEtag?: string, options?: RequestOptions): Promise<KnowledgeBase>;
  deleteKB(kbId: Id, expectedEtag?: string, options?: RequestOptions): Promise<void>;
  /** Publish the newest ready version of a knowledge base. */
  publishKB(kbId: Id, body: PublishRequest, options?: RequestOptions): Promise<KnowledgeBase>;

  listDocuments(
    kbId: Id,
    query?: OperationQuery<"get", "/v1/kbs/{kb_id}/documents">,
    options?: RequestOptions,
  ): Promise<Page_Document_>;
  createDocument(kbId: Id, body: PutDocument, options?: RequestOptions): Promise<ChangeReceipt>;
  getDocument(documentId: Id, revisionId?: Id, options?: RequestOptions): Promise<DocumentDetail>;
  updateDocument(documentId: Id, body: PutDocument, options?: RequestOptions): Promise<ChangeReceipt>;
  deleteDocument(documentId: Id, expectedRevisionId?: Id, options?: RequestOptions): Promise<ChangeReceipt>;
  listQA(
    kbId: Id,
    query?: OperationQuery<"get", "/v1/kbs/{kb_id}/qa-pairs">,
    options?: RequestOptions,
  ): Promise<Page_QAPair_>;
  createQA(kbId: Id, body: PutQA, options?: RequestOptions): Promise<ChangeReceipt>;
  getQA(qaId: Id, options?: RequestOptions): Promise<QAPair>;
  updateQA(qaId: Id, body: PutQA, options?: RequestOptions): Promise<ChangeReceipt>;
  deleteQA(qaId: Id, expectedRevisionId?: Id, options?: RequestOptions): Promise<ChangeReceipt>;

  listSourceRoots(options?: RequestOptions): Promise<string[]>;
  scanSourceRoot(rootId: Id, options?: RequestOptions): Promise<SourceManifest>;
  listSources(kbId: Id, options?: RequestOptions): Promise<Source[]>;
  createSource(kbId: Id, body: Source, options?: RequestOptions): Promise<Source>;
  getSource(sourceId: Id, options?: RequestOptions): Promise<Source>;
  updateSource(sourceId: Id, body: Source, options?: RequestOptions): Promise<Source>;
  deleteSource(sourceId: Id, options?: RequestOptions): Promise<void>;
  syncSource(sourceId: Id, body: Selection, options?: RequestOptions): Promise<ChangeReceipt>;

  beginUpload(body: UploadManifest, options?: RequestOptions): Promise<UploadBatch>;
  /** Send one declared file's bytes; the server checks size and digest. */
  putUploadFile(batchId: Id, relativePath: string, data: Blob | ArrayBuffer, options?: RequestOptions): Promise<void>;
  completeUpload(batchId: Id, options?: RequestOptions): Promise<SourceManifest>;
  previewImport(kbId: Id, body: ImportPreviewRequest, options?: RequestOptions): Promise<ImportPreview>;
  importDocuments(kbId: Id, body: ImportRequest, options?: RequestOptions): Promise<ChangeReceipt>;

  listVersions(kbId: Id, options?: RequestOptions): Promise<Snapshot[]>;
  getVersion(versionId: Id, options?: RequestOptions): Promise<Snapshot>;
  /** The contract types the diff body only as an object; callers validate it. */
  diffVersions(kbId: Id, left: Id, right: Id, options?: RequestOptions): Promise<Record<string, unknown>>;
  publishVersion(versionId: Id, body: PublishRequest, options?: RequestOptions): Promise<Snapshot>;
  rollbackVersion(kbId: Id, body: RollbackRequest, options?: RequestOptions): Promise<Snapshot>;

  getJob(jobId: Id, options?: RequestOptions): Promise<Job>;
  cancelJob(jobId: Id, options?: RequestOptions): Promise<Job>;
  /** Persisted job events after `after` (JSON replay; the SSE form is P3). */
  jobEvents(jobId: Id, after?: number, options?: RequestOptions): Promise<Array<Record<string, unknown>>>;

  getKnowledgeCatalog(options?: RequestOptions): Promise<Page_KBDescriptor_>;
  previewSelection(body: SelectionPreviewRequest, options?: RequestOptions): Promise<SelectionResult>;
  getSessionSelection(sessionId: Id, options?: RequestOptions): Promise<SessionSelection>;
  setSessionSelection(
    sessionId: Id,
    body: UpdateSessionSelection,
    options?: RequestOptions,
  ): Promise<SessionSelection>;

  search(body: SearchRequest, options?: RequestOptions): Promise<SearchResult>;
  ask(body: AskRequest, options?: RequestOptions): Promise<AskResponse>;
  createSession(body: CreateSession, options?: RequestOptions): Promise<Session>;
  getHistory(sessionId: Id, options?: RequestOptions): Promise<Turn[]>;
  submitAnswer(sessionId: Id, body: SubmitAnswer, options?: RequestOptions): Promise<AskResponse>;
  getAnswer(answerId: Id, options?: RequestOptions): Promise<Answer>;
  cancelAnswer(answerId: Id, options?: RequestOptions): Promise<Answer>;
  getCitation(answerId: Id, citationId: Id, options?: RequestOptions): Promise<CitationDetail>;

  submitFeedback(answerId: Id, body: FeedbackInput, options?: RequestOptions): Promise<Feedback>;
  listIssues(query?: OperationQuery<"get", "/v1/issues">, options?: RequestOptions): Promise<Issue[]>;
  getIssue(issueId: Id, options?: RequestOptions): Promise<Issue>;
  resolveIssue(issueId: Id, body: IssueResolution, options?: RequestOptions): Promise<Issue>;
  retestIssue(issueId: Id, body: RetestRequest, options?: RequestOptions): Promise<AskResponse>;

  modelCapabilities(options?: RequestOptions): Promise<ModelCapabilities>;
  discoverRuntimes(targetIds: Id[], options?: RequestOptions): Promise<DiscoveryReport>;
  listRuntimes(options?: RequestOptions): Promise<RuntimeStatus[]>;
  listModels(query?: OperationQuery<"get", "/v1/models">, options?: RequestOptions): Promise<Page_ModelRef_>;
  getModel(modelId: Id, options?: RequestOptions): Promise<ModelRef>;
  listProfiles(options?: RequestOptions): Promise<Page_ProfileSummary_>;
  createProfile(body: PutInferenceProfile, options?: RequestOptions): Promise<InferenceProfile>;
  getProfile(profileId: Id, revision?: Id, options?: RequestOptions): Promise<InferenceProfile>;
  putProfile(profileId: Id, body: PutInferenceProfile, options?: RequestOptions): Promise<InferenceProfile>;
  disableProfile(profileId: Id, body: PutInferenceProfile, options?: RequestOptions): Promise<InferenceProfile>;
  getSessionInference(sessionId: Id, options?: RequestOptions): Promise<SessionInference>;
  setSessionInference(
    sessionId: Id,
    body: UpdateSessionInference,
    options?: RequestOptions,
  ): Promise<SessionInference>;
  previewInstall(body: InstallRequest, options?: RequestOptions): Promise<InstallPreview>;
  confirmInstall(body: InstallConfirmation, options: IdempotentRequestOptions): Promise<Job>;
  verifyModel(modelId: Id, body: VerifyModelRequest, options: IdempotentRequestOptions): Promise<Job>;

  /** Raw transport for SSE helpers and tests; still goes through auth+errors. */
  request<T>(method: string, path: string, init?: RawRequestInit): Promise<T>;

  /** Authenticated streaming response (SSE). Rejects non-2xx with ``QAError``. */
  stream(
    path: string,
    init?: { signal?: AbortSignal; headers?: Record<string, string> },
  ): Promise<Response>;
}

export interface RawRequestInit {
  body?: unknown;
  options?: RequestOptions;
  rawBody?: BodyInit;
  headers?: Record<string, string>;
  /** Non-2xx statuses that carry a normal response body for this call. */
  acceptStatus?: number[];
}

/** Upload PUTs carry whole files; allow far more than the JSON default. */
const UPLOAD_TIMEOUT_MS = 10 * 60_000;

export function createClient(options: ClientOptions): Client {
  const doFetch = options.fetch ?? globalThis.fetch?.bind(globalThis);
  if (!doFetch) throw new Error("no fetch implementation is available");
  const baseUrl = options.baseUrl.replace(/\/+$/, "");
  const configuredBase = new URL(baseUrl);
  if (configuredBase.username || configuredBase.password || configuredBase.search || configuredBase.hash) {
    throw new Error("API base URL must not contain credentials, a query or a fragment");
  }
  const timeoutMs = options.timeoutMs ?? 30_000;

  function apiUrl(path: string): URL {
    if (!path.startsWith("/") || path.startsWith("//") || path.includes("\\")) {
      throw new Error("API path must start with one forward slash");
    }
    const url = new URL(baseUrl + path);
    if (url.origin !== configuredBase.origin) {
      throw new Error("API path must stay on the configured origin");
    }
    return url;
  }

  async function authHeaders(signal?: AbortSignal): Promise<Record<string, string>> {
    signal?.throwIfAborted();
    const credential = options.getCredential ? await options.getCredential() : null;
    signal?.throwIfAborted();
    return credential ? { Authorization: `Bearer ${credential}` } : {};
  }

  async function request<T>(method: string, path: string, init: RawRequestInit = {}): Promise<T> {
    const { options: reqOptions = {}, body, rawBody } = init;
    const url = apiUrl(path);
    for (const [key, value] of Object.entries(reqOptions.query ?? {})) {
      if (value !== undefined && value !== null) url.searchParams.set(key, String(value));
    }
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), reqOptions.timeoutMs ?? timeoutMs);
    const onAbort = () => controller.abort();
    if (reqOptions.signal?.aborted) controller.abort();
    else reqOptions.signal?.addEventListener("abort", onAbort, { once: true });
    try {
      const headers: Record<string, string> = {
        Accept: "application/json",
        ...(init.headers ?? {}),
        ...(await authHeaders(controller.signal)),
      };
      if (body !== undefined) headers["Content-Type"] = "application/json";
      if (reqOptions.idempotencyKey) headers["Idempotency-Key"] = reqOptions.idempotencyKey;
      controller.signal.throwIfAborted();
      const response = await doFetch(url.toString(), {
        method,
        headers,
        body: rawBody ?? (body === undefined ? undefined : JSON.stringify(body)),
        signal: controller.signal,
      });
      const requestId = response.headers.get("X-Request-ID") ?? undefined;
      const text = await response.text();
      const payload: unknown = text ? safeJson(text) : null;
      if (!response.ok && !init.acceptStatus?.includes(response.status)) {
        throw toError(response.status, payload, requestId);
      }
      return payload as T;
    } finally {
      clearTimeout(timer);
      reqOptions.signal?.removeEventListener("abort", onAbort);
    }
  }

  /** Call one contract operation; the generated types fix path, body and result. */
  async function op<M extends Method, P extends PathFor<M>>(
    method: M,
    template: P,
    init: OpInit<Op<P, M>> = {},
  ): Promise<Success<Op<P, M>>> {
    const typedQuery = init.query as RequestOptions["query"] | undefined;
    const reqOptions: RequestOptions | undefined =
      typedQuery === undefined
        ? init.options
        : { ...init.options, query: { ...init.options?.query, ...typedQuery } };
    return request<Success<Op<P, M>>>(method.toUpperCase(), fillPath(template, init.path), {
      body: init.body,
      rawBody: init.rawBody,
      headers: init.headers,
      options: reqOptions,
    });
  }

  async function stream(
    path: string,
    init: { signal?: AbortSignal; headers?: Record<string, string> } = {},
  ): Promise<Response> {
    const url = apiUrl(path);
    init.signal?.throwIfAborted();
    const headers = {
      Accept: "text/event-stream",
      ...(await authHeaders(init.signal)),
      ...(init.headers ?? {}),
    };
    init.signal?.throwIfAborted();
    const response = await doFetch(url.toString(), {
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
    health: (o) => op("get", "/healthz", { options: o }),
    readiness: (o) => request<Readiness>("GET", "/readyz", { options: o, acceptStatus: [503] }),
    capabilities: (o) => op("get", "/v1/capabilities", { options: o }),

    listKBs: (query, o) => op("get", "/v1/kbs", { query, options: o }),
    createKB: (body, o) => op("post", "/v1/kbs", { body, options: o }),
    getKB: (kbId, o) => op("get", "/v1/kbs/{kb_id}", { path: { kb_id: kbId }, options: o }),
    updateKB: (kbId, body, expectedEtag, o) =>
      op("patch", "/v1/kbs/{kb_id}", {
        path: { kb_id: kbId },
        query: { expected_etag: expectedEtag },
        body,
        options: o,
      }),
    deleteKB: async (kbId, expectedEtag, o) => {
      await op("delete", "/v1/kbs/{kb_id}", {
        path: { kb_id: kbId },
        query: { expected_etag: expectedEtag },
        options: o,
      });
    },
    publishKB: (kbId, body, o) =>
      op("post", "/v1/kbs/{kb_id}/publish", { path: { kb_id: kbId }, body, options: o }),

    listDocuments: (kbId, query, o) =>
      op("get", "/v1/kbs/{kb_id}/documents", { path: { kb_id: kbId }, query, options: o }),
    createDocument: (kbId, body, o) =>
      op("post", "/v1/kbs/{kb_id}/documents", { path: { kb_id: kbId }, body, options: o }),
    getDocument: (documentId, revisionId, o) =>
      op("get", "/v1/documents/{document_id}", {
        path: { document_id: documentId },
        query: { revision_id: revisionId },
        options: o,
      }),
    updateDocument: (documentId, body, o) =>
      op("patch", "/v1/documents/{document_id}", {
        path: { document_id: documentId },
        body,
        options: o,
      }),
    deleteDocument: (documentId, expectedRevisionId, o) =>
      op("delete", "/v1/documents/{document_id}", {
        path: { document_id: documentId },
        query: { expected_revision_id: expectedRevisionId },
        options: o,
      }),
    listQA: (kbId, query, o) =>
      op("get", "/v1/kbs/{kb_id}/qa-pairs", { path: { kb_id: kbId }, query, options: o }),
    createQA: (kbId, body, o) =>
      op("post", "/v1/kbs/{kb_id}/qa-pairs", { path: { kb_id: kbId }, body, options: o }),
    getQA: (qaId, o) => op("get", "/v1/qa-pairs/{qa_id}", { path: { qa_id: qaId }, options: o }),
    updateQA: (qaId, body, o) =>
      op("patch", "/v1/qa-pairs/{qa_id}", { path: { qa_id: qaId }, body, options: o }),
    deleteQA: (qaId, expectedRevisionId, o) =>
      op("delete", "/v1/qa-pairs/{qa_id}", {
        path: { qa_id: qaId },
        query: { expected_revision_id: expectedRevisionId },
        options: o,
      }),

    listSourceRoots: (o) => op("get", "/v1/source-roots", { options: o }),
    scanSourceRoot: (rootId, o) =>
      op("post", "/v1/source-roots/{root_id}/scan", { path: { root_id: rootId }, options: o }),
    listSources: (kbId, o) =>
      op("get", "/v1/kbs/{kb_id}/sources", { path: { kb_id: kbId }, options: o }),
    createSource: (kbId, body, o) =>
      op("post", "/v1/kbs/{kb_id}/sources", { path: { kb_id: kbId }, body, options: o }),
    getSource: (sourceId, o) =>
      op("get", "/v1/sources/{source_id}", { path: { source_id: sourceId }, options: o }),
    updateSource: (sourceId, body, o) =>
      op("patch", "/v1/sources/{source_id}", { path: { source_id: sourceId }, body, options: o }),
    deleteSource: async (sourceId, o) => {
      await op("delete", "/v1/sources/{source_id}", { path: { source_id: sourceId }, options: o });
    },
    syncSource: (sourceId, body, o) =>
      op("post", "/v1/sources/{source_id}/sync", { path: { source_id: sourceId }, body, options: o }),

    beginUpload: (body, o) => op("post", "/v1/uploads", { body, options: o }),
    putUploadFile: async (batchId, relativePath, data, o) => {
      await op("put", "/v1/uploads/{batch_id}/files", {
        path: { batch_id: batchId },
        query: { relative_path: relativePath },
        rawBody: data,
        headers: { "Content-Type": "application/octet-stream" },
        options: { timeoutMs: UPLOAD_TIMEOUT_MS, ...o },
      });
    },
    completeUpload: (batchId, o) =>
      op("post", "/v1/uploads/{batch_id}/complete", { path: { batch_id: batchId }, options: o }),
    previewImport: (kbId, body, o) =>
      op("post", "/v1/kbs/{kb_id}/imports/preview", { path: { kb_id: kbId }, body, options: o }),
    importDocuments: (kbId, body, o) =>
      op("post", "/v1/kbs/{kb_id}/imports", { path: { kb_id: kbId }, body, options: o }),
    listVersions: (kbId, o) =>
      op("get", "/v1/kbs/{kb_id}/versions", { path: { kb_id: kbId }, options: o }),
    getVersion: (versionId, o) =>
      op("get", "/v1/versions/{version_id}", { path: { version_id: versionId }, options: o }),
    diffVersions: (kbId, left, right, o) =>
      op("get", "/v1/kbs/{kb_id}/version-diff", {
        path: { kb_id: kbId },
        query: { left, right },
        options: o,
      }),
    publishVersion: (versionId, body, o) =>
      op("post", "/v1/versions/{version_id}/publish", {
        path: { version_id: versionId },
        body,
        options: o,
      }),
    rollbackVersion: (kbId, body, o) =>
      op("post", "/v1/kbs/{kb_id}/rollback", { path: { kb_id: kbId }, body, options: o }),

    getJob: (jobId, o) => op("get", "/v1/jobs/{job_id}", { path: { job_id: jobId }, options: o }),
    cancelJob: (jobId, o) =>
      op("post", "/v1/jobs/{job_id}/cancel", { path: { job_id: jobId }, options: o }),
    jobEvents: (jobId, after, o) =>
      op("get", "/v1/jobs/{job_id}/events", {
        path: { job_id: jobId },
        headers: after === undefined ? undefined : { "Last-Event-ID": String(after) },
        options: o,
      }),

    getKnowledgeCatalog: (o) => op("get", "/v1/knowledge-catalog", { options: o }),
    previewSelection: (body, o) =>
      op("post", "/v1/knowledge-selection/preview", { body, options: o }),
    getSessionSelection: (sessionId, o) =>
      op("get", "/v1/sessions/{session_id}/selection", {
        path: { session_id: sessionId },
        options: o,
      }),
    setSessionSelection: (sessionId, body, o) =>
      op("patch", "/v1/sessions/{session_id}/selection", {
        path: { session_id: sessionId },
        body,
        options: o,
      }),
    search: (body, o) => op("post", "/v1/search", { body, options: o }),
    ask: (body, o) => op("post", "/v1/ask", { body, options: o }),
    createSession: (body, o) => op("post", "/v1/sessions", { body, options: o }),
    getHistory: (sessionId, o) =>
      op("get", "/v1/sessions/{session_id}/history", { path: { session_id: sessionId }, options: o }),
    submitAnswer: (sessionId, body, o) =>
      op("post", "/v1/sessions/{session_id}/answers", {
        path: { session_id: sessionId },
        body,
        options: o,
      }),
    getAnswer: (answerId, o) =>
      op("get", "/v1/answers/{answer_id}", { path: { answer_id: answerId }, options: o }),
    cancelAnswer: (answerId, o) =>
      op("post", "/v1/answers/{answer_id}/cancel", { path: { answer_id: answerId }, options: o }),
    getCitation: (answerId, citationId, o) =>
      op("get", "/v1/answers/{answer_id}/citations/{citation_id}", {
        path: { answer_id: answerId, citation_id: citationId },
        options: o,
      }),

    submitFeedback: (answerId, body, o) =>
      op("post", "/v1/answers/{answer_id}/feedback", {
        path: { answer_id: answerId },
        body,
        options: o,
      }),
    listIssues: (query, o) => op("get", "/v1/issues", { query, options: o }),
    getIssue: (issueId, o) =>
      op("get", "/v1/issues/{issue_id}", { path: { issue_id: issueId }, options: o }),
    resolveIssue: (issueId, body, o) =>
      op("patch", "/v1/issues/{issue_id}", { path: { issue_id: issueId }, body, options: o }),
    retestIssue: (issueId, body, o) =>
      op("post", "/v1/issues/{issue_id}/retest", { path: { issue_id: issueId }, body, options: o }),
    modelCapabilities: (o) => op("get", "/v1/models/capabilities", { options: o }),
    discoverRuntimes: (targetIds, o) =>
      op("post", "/v1/models/discovery", { body: { target_ids: targetIds }, options: o }),
    listRuntimes: (o) => op("get", "/v1/models/runtimes", { options: o }),
    listModels: (query, o) => op("get", "/v1/models", { query, options: o }),
    getModel: (modelId, o) =>
      op("get", "/v1/models/{model_id}", { path: { model_id: modelId }, options: o }),
    listProfiles: (o) => op("get", "/v1/inference-profiles", { options: o }),
    createProfile: (body, o) => op("post", "/v1/inference-profiles", { body, options: o }),
    getProfile: (profileId, revision, o) =>
      op("get", "/v1/inference-profiles/{profile_id}", {
        path: { profile_id: profileId },
        query: { revision },
        options: o,
      }),
    putProfile: (profileId, body, o) =>
      op("put", "/v1/inference-profiles/{profile_id}", {
        path: { profile_id: profileId },
        body,
        options: o,
      }),
    disableProfile: (profileId, body, o) =>
      op("post", "/v1/inference-profiles/{profile_id}/disable", {
        path: { profile_id: profileId },
        body,
        options: o,
      }),
    getSessionInference: (sessionId, o) =>
      op("get", "/v1/sessions/{session_id}/inference", {
        path: { session_id: sessionId },
        options: o,
      }),
    setSessionInference: (sessionId, body, o) =>
      op("patch", "/v1/sessions/{session_id}/inference", {
        path: { session_id: sessionId },
        body,
        options: o,
      }),
    previewInstall: (body, o) => op("post", "/v1/model-installs/preview", { body, options: o }),
    confirmInstall: (body, o) => {
      requireIdempotencyKey(o);
      return op("post", "/v1/model-installs", { body, options: o });
    },
    verifyModel: (modelId, body, o) => {
      requireIdempotencyKey(o);
      return op("post", "/v1/models/{model_id}/verifications", {
        path: { model_id: modelId },
        body,
        options: o,
      });
    },
  };
}

function fillPath(template: string, params: Record<string, string> = {}): string {
  return template.replace(/\{([^}]+)\}/g, (_match, name: string) => {
    const value = params[name];
    if (value === undefined) throw new Error(`missing path parameter ${name}`);
    return encodeURIComponent(value);
  });
}

function requireIdempotencyKey(options: RequestOptions | undefined): void {
  if (!options?.idempotencyKey?.trim()) throw new Error("Idempotency-Key is required");
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
