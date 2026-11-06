/**
 * In-memory fake of the P2-A1 management API for front-end tests (never part of
 * a build). Shapes come from the generated SDK types; the rules the admin UI
 * depends on mirror the real server: ETag / revision / expected-active checks
 * return 409, upload size or digest mismatches 422, confirm re-checks the
 * preview hash and file set, jobs stay queued until runWorker(), mirror
 * removals happen only after a complete, successful upload, and a content edit
 * rebuilds the whole base into a ready version reported as `version_id`.
 */

import {
  createClient,
  type ChangeReceipt,
  type Client,
  type Document,
  type ImportPreview,
  type Issue,
  type Job,
  type JobFileDiagnostic,
  type KnowledgeBase,
  type ManifestFile,
  type QAPair,
  type Revision,
  type Snapshot,
  type SnapshotState,
  type Source,
  type SourceManifest,
} from "@qa/client";

export const FAKE_API = "http://fake.test";

export interface Call {
  method: string;
  path: string;
  query: URLSearchParams;
  headers: Record<string, string>;
  body: unknown;
  signal: AbortSignal | null;
}

/** Request bodies are whatever the UI sent; each handler checks what it needs. */
type Body = any;
interface Reply {
  status: number;
  body?: unknown;
}
type Handler = (match: string[], query: URLSearchParams, body: Body, raw: ArrayBuffer | null, headers: Record<string, string>) => Reply | Promise<Reply>;
interface StoredDocument {
  doc: Document;
  revisions: Revision[];
  sourceId: string | null;
  path: string | null;
}
interface Batch {
  sourceId: string;
  selection: Body;
  declared: Map<string, ManifestFile>;
  received: Map<string, string>;
  done: boolean;
}

export interface FakeState {
  kbs: Map<string, KnowledgeBase>;
  sources: Map<string, Source>;
  roots: string[];
  /** Files a server-side authorized root would scan, per source id. */
  rootFiles: Map<string, ManifestFile[]>;
  batches: Map<string, Batch>;
  /** Latest completed upload manifest per source (what the server rescans). */
  uploads: Map<string, SourceManifest>;
  /** Manifest of the last successful import per source (the diff baseline). */
  baselines: Map<string, SourceManifest>;
  previews: Map<string, { preview: ImportPreview; manifest: SourceManifest; mode: string; sourceId: string }>;
  jobs: Map<string, { job: Job; payload: Body; events: Array<{ id: number; event: string; data: Body }> }>;
  versions: Map<string, Snapshot>;
  documents: Map<string, StoredDocument>;
  qa: Map<string, QAPair>;
  /** null: the feedback routes answer 501 like the P2 server. */
  issues: Issue[] | null;
  /** Bytes whose text contains this marker fail to parse in runWorker(). */
  corruptMarker: string;
}

let sequence = 0;
const nextId = (prefix: string): string => `${prefix}_${String(++sequence).padStart(4, "0")}`;
const clock = (): string => new Date(Date.UTC(2026, 10, 6, 0, 0, sequence++)).toISOString();

function error(status: number, code: string, message: string, details: Array<{ field?: string; reason: string }> = []): Reply {
  return { status, body: { error: { code, message, details } } };
}
const notFound = (what: string): Reply => error(404, "NOT_FOUND", `${what} was not found`);
const conflict = (expected: string, actual: string): Reply => error(409, "CONFLICT", `expected ${expected}, found ${actual}`);
const invalid = (field: string, reason: string): Reply => error(422, "VALIDATION_FAILED", "request validation failed", [{ field, reason }]);

function page<T>(items: T[], key: (item: T) => string, query: URLSearchParams): Reply {
  const sorted = [...items].sort((a, b) => (key(a) < key(b) ? -1 : 1));
  const cursor = query.get("cursor");
  const start = cursor ? sorted.findIndex((item) => key(item) > cursor) : 0;
  const limit = Number(query.get("limit") ?? 50);
  const slice = start < 0 ? [] : sorted.slice(start, start + limit);
  const more = start >= 0 && start + limit < sorted.length;
  return { status: 200, body: { items: slice, next_cursor: more ? key(slice[slice.length - 1] as T) : null } };
}

async function sha256(data: ArrayBuffer): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}
export interface FakeApi {
  client: Client;
  calls: Call[];
  state: FakeState;
  /** Answer the next request to `METHOD /path` (exact path) with this error. */
  failNext(
    method: string,
    path: string,
    status: number,
    code: string,
    message?: string,
    details?: Array<{ field?: string; reason: string }>,
  ): void;
  /** Keep the next matching request pending until the returned release() is called. */
  hold(method: string, path: string): () => void;
  /** Execute queued jobs like qa-worker; returns the processed job ids. */
  runWorker(): string[];
  seedKB(name: string): KnowledgeBase;
  seedDocument(kbId: string, title: string, text: string, sourceId?: string | null, path?: string | null): Document;
  seedVersion(kbId: string, state: SnapshotState, revisions: Record<string, string>, activate?: boolean): Snapshot;
}

export function createFakeApi(): FakeApi {
  const state: FakeState = {
    kbs: new Map(),
    sources: new Map(),
    roots: [],
    rootFiles: new Map(),
    batches: new Map(),
    uploads: new Map(),
    baselines: new Map(),
    previews: new Map(),
    jobs: new Map(),
    versions: new Map(),
    documents: new Map(),
    qa: new Map(),
    issues: null,
    corruptMarker: "%CORRUPT%",
  };
  const calls: Call[] = [];
  const failures: Array<{ key: string; reply: Reply }> = [];
  const holds: Array<{ key: string; gate: Promise<void> }> = [];
  let requestSeq = 0;

  const receipt = (kbId: string, documentId: string | null, jobId: string | null, versionId: string | null = null): ChangeReceipt => ({
    kb_id: kbId,
    document_id: documentId,
    job_id: jobId,
    version_id: versionId,
    requires_publish: true,
  });

  const kbOr404 = (kbId: string): KnowledgeBase | Reply => state.kbs.get(kbId) ?? notFound("knowledge base");
  const isReply = (value: unknown): value is Reply =>
    typeof value === "object" && value !== null && "status" in value && typeof (value as Reply).status === "number";

  const putKB = (kb: KnowledgeBase): KnowledgeBase => {
    state.kbs.set(kb.kb_id, kb);
    return kb;
  };
  const touchKB = (kb: KnowledgeBase, update: Partial<KnowledgeBase>): KnowledgeBase =>
    putKB({ ...kb, ...update, etag: `etag_${++sequence}`, updated_at: clock() });
  /** Server-side rescan of a source: the latest upload batch or the authorized root. */
  const scan = (source: Source): SourceManifest | Reply => {
    if (source.kind === "upload") {
      return state.uploads.get(source.source_id) ?? conflict("a completed upload batch", "no upload has been completed");
    }
    if (!source.root_id || !state.roots.includes(source.root_id)) {
      return invalid("root_id", "source root is not configured on this server");
    }
    return {
      source_id: source.source_id,
      files: state.rootFiles.get(source.source_id) ?? [],
      selection: {},
      scan_scope: "full",
      scan_status: "succeeded",
      complete: true,
      scanned_at: clock(),
    };
  };

  /** Same rules as KBManagement ChangePlanner: only a complete mirror scan removes. */
  const diff = (sourceId: string, manifest: SourceManifest, mode: string) => {
    const before = new Map((state.baselines.get(sourceId)?.files ?? []).map((file) => [file.relative_path, file.digest]));
    const now = new Map((manifest.files ?? []).map((file) => [file.relative_path, file.digest]));
    const added = [...now.keys()].filter((path) => !before.has(path)).sort();
    const modified = [...now.keys()].filter((path) => before.has(path) && before.get(path) !== now.get(path)).sort();
    const unchanged = [...now.keys()].filter((path) => before.get(path) === now.get(path)).sort();
    const complete = mode === "mirror" && manifest.complete && manifest.scan_status === "succeeded";
    const removed = complete ? [...before.keys()].filter((path) => !now.has(path)).sort() : [];
    return { added, modified, unchanged, removed };
  };

  const fingerprint = (kbId: string, manifest: SourceManifest, mode: string): string =>
    JSON.stringify([kbId, manifest.source_id, mode, manifest.selection ?? {}, manifest.complete, manifest.scan_scope,
      manifest.scan_status, [...(manifest.files ?? [])].sort((a, b) => (a.relative_path < b.relative_path ? -1 : 1))]);
  const hashes = new Map<string, string>();
  const previewHash = (kbId: string, manifest: SourceManifest, mode: string): string => {
    const key = fingerprint(kbId, manifest, mode);
    if (!hashes.has(key)) hashes.set(key, `hash_${hashes.size + 1}`);
    return hashes.get(key) as string;
  };

  const sameFiles = (a: SourceManifest, b: SourceManifest): boolean =>
    fingerprint("", a, "") === fingerprint("", b, "");

  const enqueue = (payload: Body, key: string | null): Job => {
    const existing = key ? [...state.jobs.values()].find((entry) => entry.job.idempotency_key === key) : undefined;
    if (existing) return existing.job;
    const job: Job = { job_id: nextId("job"), kind: "import", state: "queued", progress: 0, revision: 0, idempotency_key: key, created_at: clock() };
    state.jobs.set(job.job_id, { job, payload, events: [] });
    return job;
  };
  const emit = (jobId: string, event: string, data: Body = {}): void => {
    const entry = state.jobs.get(jobId);
    if (!entry) return;
    const id = entry.events.length + 1;
    entry.events.push({ id, event, data: { job_id: jobId, seq: id, event, timestamp: clock(), ...data } });
  };
  const finish = (jobId: string, update: Partial<Job>, event: string, data: Body = {}): void => {
    const entry = state.jobs.get(jobId);
    if (!entry) return;
    entry.job = { ...entry.job, ...update, revision: entry.job.revision + 1 };
    emit(jobId, event, data);
  };
  /** Text of uploaded files, by `source_id/relative_path`. */
  const texts = new Map<string, string>();

  const addRevision = (
    kbId: string,
    documentId: string | null,
    title: string,
    text: string,
    kind: "document" | "qa_pair",
    sourceId: string | null,
    path: string | null,
  ): StoredDocument => {
    const id = documentId ?? nextId(kind === "qa_pair" ? "qa" : "doc");
    const existing = state.documents.get(id);
    const revision: Revision = {
      revision_id: nextId("rev"),
      document_id: id,
      parent_revision_id: existing?.doc.latest_revision_id ?? null,
      content_kind: kind,
      relative_path: path,
      source_id: sourceId,
      normalized_text: text,
      diagnostics: [],
      created_at: clock(),
    };
    const doc: Document = { document_id: id, kb_id: kbId, title, content_kind: kind, latest_revision_id: revision.revision_id, deleted: false, updated_at: clock() };
    const stored: StoredDocument = { doc, revisions: [...(existing?.revisions ?? []), revision], sourceId, path };
    state.documents.set(id, stored);
    return stored;
  };
  const byPath = (sourceId: string, path: string): StoredDocument | undefined =>
    [...state.documents.values()].find((item) => item.sourceId === sourceId && item.path === path && !item.doc.deleted);

  /** Like ContentRebuilder: every active document and QA pair of the base, synchronously, never published. */
  const rebuildAll = (kbId: string): string | null => {
    const revisions: Record<string, string> = {};
    for (const item of state.documents.values()) {
      if (item.doc.kb_id === kbId && !item.doc.deleted) revisions[item.doc.document_id] = item.doc.latest_revision_id;
    }
    if (Object.keys(revisions).length === 0) return null;
    const version: Snapshot = {
      version_id: nextId("ver"), kb_id: kbId, parent_version_id: state.kbs.get(kbId)?.active_version_id ?? null, state: "ready",
      document_revisions: revisions, keyword_profile: "zh-bm25-v1", keyword_index_ref: "idx", vector_index: "absent", created_at: clock(),
    };
    state.versions.set(version.version_id, version);
    return version.version_id;
  };

  const execute = (jobId: string, payload: Body): void => {
    finish(jobId, { state: "running" }, "job.progress", { progress: 0 });
    const kb = state.kbs.get(payload.kb_id);
    const manifest = payload.manifest as SourceManifest;
    const change = diff(payload.source_id, manifest, payload.mode);
    const base = kb?.active_version_id ?? null;
    if (base && change.added.length + change.modified.length + change.removed.length === 0) {
      state.baselines.set(payload.source_id, manifest);
      finish(jobId, { state: "succeeded", progress: 1, result_version_id: base }, "job.completed", { progress: 1 });
      return;
    }
    const revisions: Record<string, string> = {};
    const diagnostics: JobFileDiagnostic[] = [];
    for (const path of change.unchanged) {
      const doc = byPath(payload.source_id, path);
      if (doc) revisions[doc.doc.document_id] = doc.doc.latest_revision_id;
    }
    // Like A1's _index_source_base: content outside this source's delta (manual documents,
    // QA pairs, other sources, this source's paths not in the manifest) is carried forward.
    const replaced = new Set([...change.added, ...change.modified, ...change.removed, ...change.unchanged]);
    for (const item of state.documents.values()) {
      if (item.doc.kb_id !== payload.kb_id || item.doc.deleted) continue;
      if (item.sourceId === payload.source_id && item.path !== null && replaced.has(item.path)) continue;
      revisions[item.doc.document_id] = item.doc.latest_revision_id;
    }
    for (const path of [...change.added, ...change.modified]) {
      const text = texts.get(`${payload.source_id}/${path}`) ?? `${path} 的内容`;
      if (text.includes(state.corruptMarker)) {
        diagnostics.push({ relative_path: path, status: "failed", message: "PARSE_FAILED: file is corrupt" });
        continue;
      }
      const existing = byPath(payload.source_id, path);
      const title = path.split("/").pop() ?? path;
      const stored = addRevision(payload.kb_id, existing?.doc.document_id ?? null, title, text, "document", payload.source_id, path);
      // Like the real build, only failed or skipped files get a diagnostic.
      revisions[stored.doc.document_id] = stored.doc.latest_revision_id;
    }
    for (const path of change.removed) {
      const doc = byPath(payload.source_id, path);
      if (doc) doc.doc = { ...doc.doc, deleted: true };
    }
    if (Object.keys(revisions).length === 0) {
      finish(jobId, { state: "failed", error_code: "IMPORT_FAILED", diagnostics }, "job.failed", { diagnostic: "no indexable content in the selected scope" });
      return;
    }
    const version: Snapshot = {
      version_id: nextId("ver"), kb_id: payload.kb_id, parent_version_id: base, state: "ready",
      document_revisions: revisions, keyword_profile: "zh-bm25-v1", keyword_index_ref: "idx", vector_index: "absent", created_at: clock(),
    };
    state.versions.set(version.version_id, version);
    state.baselines.set(payload.source_id, manifest);
    finish(jobId, { state: "succeeded", progress: 1, result_version_id: version.version_id, diagnostics }, "job.completed", { progress: 1 });
  };
  const routes: Array<[string, RegExp, Handler]> = [
    ["GET", /^\/v1\/capabilities$/, () => ({
      status: 200,
      body: {
        mode: "operational", schema_version: 2,
        implemented: ["health", "readiness", "capabilities", "knowledge", "content", "imports", "sources", "versions", "jobs"],
        unimplemented: ["search", "ask", "sessions", "feedback", "selection", "models", "widget"],
        selection_limits: { max_candidate_kbs: 20, max_selected_kbs: 3 },
      },
    })],
    ["GET", /^\/v1\/kbs$/, (_m, query) => page([...state.kbs.values()], (kb) => kb.kb_id, query)],
    ["POST", /^\/v1\/kbs$/, (_m, _q, body) => {
      if (typeof body?.name !== "string" || !body.name) return invalid("name", "String should have at least 1 character");
      const kb = putKB({
        kb_id: nextId("kb"), name: body.name, description: body.description ?? "", domain_tags: body.domain_tags ?? [],
        routing_examples: body.routing_examples ?? [], active_version_id: null, etag: `etag_${++sequence}`, updated_at: clock(),
      });
      return { status: 201, body: kb };
    }],
    ["GET", /^\/v1\/kbs\/([^/]+)$/, ([id]) => {
      const kb = kbOr404(id as string);
      return isReply(kb) ? kb : { status: 200, body: kb };
    }],
    ["PATCH", /^\/v1\/kbs\/([^/]+)$/, ([id], query, body) => {
      const kb = kbOr404(id as string);
      if (isReply(kb)) return kb;
      const expected = query.get("expected_etag");
      if (expected && expected !== kb.etag) return conflict(`etag ${expected}`, `etag ${kb.etag}`);
      const update: Partial<KnowledgeBase> = {};
      for (const key of ["name", "description", "domain_tags", "routing_examples"] as const) {
        if (body?.[key] !== undefined && body[key] !== null) update[key] = body[key];
      }
      return { status: 200, body: touchKB(kb, update) };
    }],
    ["DELETE", /^\/v1\/kbs\/([^/]+)$/, ([id], query) => {
      const kb = kbOr404(id as string);
      if (isReply(kb)) return kb;
      // Like KBService.delete: only an empty base without versions can be deleted.
      if (kb.active_version_id) return conflict("knowledge base without an active version", `active version ${kb.active_version_id}`);
      if ([...state.sources.values()].some((source) => source.kb_id === kb.kb_id)) {
        return conflict("a knowledge base without sources", "sources still exist");
      }
      if ([...state.documents.values()].some((item) => item.doc.kb_id === kb.kb_id && !item.doc.deleted)) {
        return conflict("a knowledge base without documents", "documents still exist");
      }
      if ([...state.versions.values()].some((version) => version.kb_id === kb.kb_id)) {
        return conflict("a knowledge base without versions", "versions still exist");
      }
      const expected = query.get("expected_etag");
      if (expected && expected !== kb.etag) return conflict(`etag ${expected}`, `etag ${kb.etag}`);
      state.kbs.delete(kb.kb_id);
      return { status: 202, body: null };
    }],
    ["GET", /^\/v1\/kbs\/([^/]+)\/sources$/, ([id]) => {
      const kb = kbOr404(id as string);
      if (isReply(kb)) return kb;
      const items = [...state.sources.values()].filter((source) => source.kb_id === kb.kb_id);
      return { status: 200, body: items.sort((a, b) => (a.source_id < b.source_id ? -1 : 1)) };
    }],
    ["POST", /^\/v1\/kbs\/([^/]+)\/sources$/, ([id], _q, body) => {
      if (body?.kb_id !== id) return invalid("kb_id", "must match the URL");
      if (state.sources.has(body.source_id)) return invalid("source_id", "already exists");
      const source: Source = { ...body, created_at: clock() };
      state.sources.set(source.source_id, source);
      return { status: 201, body: source };
    }],
    ["GET", /^\/v1\/source-roots$/, () => ({ status: 200, body: [...state.roots].sort() })],
    ["POST", /^\/v1\/uploads$/, (_m, _q, body) => {
      const source = state.sources.get(body?.source_id);
      if (!source || source.kind !== "upload") return invalid("source_id", "is not an upload source");
      const batchId = nextId("batch");
      const declared = new Map<string, ManifestFile>((body.files ?? []).map((file: ManifestFile) => [file.relative_path, file]));
      state.batches.set(batchId, { sourceId: source.source_id, selection: body.selection ?? {}, declared, received: new Map(), done: false });
      return { status: 202, body: { batch_id: batchId, source_id: source.source_id } };
    }],
    ["PUT", /^\/v1\/uploads\/([^/]+)\/files$/, async ([id], query, _body, raw) => {
      const batch = state.batches.get(id as string);
      if (!batch) return notFound("upload batch");
      if (batch.done) return invalid("batch_id", "is already complete");
      const path = query.get("relative_path") ?? "";
      if (path.startsWith("/") || path.split("/").includes("..")) return invalid("relative_path", "must stay inside the upload root");
      const declared = batch.declared.get(path);
      if (!declared) return invalid("relative_path", "was not declared in the manifest");
      const bytes = raw ?? new ArrayBuffer(0);
      if (bytes.byteLength !== declared.size) return invalid("relative_path", "size differs from the manifest");
      const digest = await sha256(bytes);
      if (digest !== declared.digest) return invalid("relative_path", "digest differs from the manifest");
      batch.received.set(path, digest);
      texts.set(`${batch.sourceId}/${path}`, new TextDecoder().decode(bytes));
      return { status: 202, body: null };
    }],
    ["POST", /^\/v1\/uploads\/([^/]+)\/complete$/, ([id]) => {
      const batch = state.batches.get(id as string);
      if (!batch) return notFound("upload batch");
      batch.done = true;
      const selection = batch.selection ?? {};
      const restricted = Boolean(selection.include_globs?.length || selection.exclude_globs?.length || selection.relative_paths?.length);
      const missing = [...batch.declared.keys()].some((path) => !batch.received.has(path));
      const manifest: SourceManifest = {
        source_id: batch.sourceId,
        files: [...batch.declared.values()].filter((file) => batch.received.has(file.relative_path)),
        selection,
        scan_scope: restricted ? "partial" : "full",
        scan_status: missing ? "failed" : "succeeded",
        complete: !missing && !restricted,
        scanned_at: clock(),
      };
      state.uploads.set(batch.sourceId, manifest);
      return { status: 202, body: manifest };
    }],
    ["POST", /^\/v1\/kbs\/([^/]+)\/imports\/preview$/, ([id], _q, body) => {
      if (body?.kb_id !== id) return invalid("kb_id", "must match the URL");
      const kb = kbOr404(id as string);
      if (isReply(kb)) return kb;
      const source = state.sources.get(body.source_id);
      if (!source) return notFound("source");
      if (source.kb_id !== kb.kb_id) return invalid("source_id", "does not belong to the requested knowledge base");
      const manifest = scan(source);
      if (isReply(manifest)) return manifest;
      const mode = body.mode ?? "merge";
      const change = diff(source.source_id, manifest, mode);
      const preview: ImportPreview = {
        preview_id: nextId("prev"), kb_id: kb.kb_id, preview_hash: previewHash(kb.kb_id, manifest, mode),
        added: change.added, modified: change.modified, removed: change.removed, conflicts: [], created_at: clock(),
      };
      state.previews.set(`${kb.kb_id}/${source.source_id}/${preview.preview_hash}`, { preview, manifest, mode, sourceId: source.source_id });
      return { status: 202, body: preview };
    }],
    ["POST", /^\/v1\/kbs\/([^/]+)\/imports$/, ([id], _q, body) => {
      if (body?.kb_id !== id) return invalid("kb_id", "must match the URL");
      const recorded = state.previews.get(`${id}/${body.source_id}/${body.expected_preview_hash}`);
      if (!recorded) return notFound("import preview");
      const mode = body.mode ?? "merge";
      if (recorded.mode !== mode) return conflict(`preview mode ${recorded.mode}`, `request mode ${mode}`);
      const source = state.sources.get(body.source_id);
      if (!source) return notFound("source");
      const manifest = scan(source);
      if (isReply(manifest)) return manifest;
      if (!sameFiles(recorded.manifest, manifest)) return conflict("the previewed file set", "a different file set was submitted");
      if (manifest.scan_status !== "succeeded") return invalid("manifest", "source scan did not succeed");
      const payload = { kind: "import", kb_id: id, source_id: source.source_id, mode, manifest };
      const job = enqueue(payload, body.expected_preview_hash);
      return { status: 202, body: receipt(id as string, null, job.job_id) };
    }],
    ["POST", /^\/v1\/sources\/([^/]+)\/sync$/, ([id]) => {
      const source = state.sources.get(id as string);
      if (!source) return notFound("source");
      const manifest = scan(source);
      if (isReply(manifest)) return manifest;
      if (manifest.scan_status !== "succeeded") return conflict("a successful scan", "the source scan failed");
      const job = enqueue({ kind: "import", kb_id: source.kb_id, source_id: source.source_id, mode: "merge", manifest }, null);
      return { status: 202, body: receipt(source.kb_id, null, job.job_id) };
    }],
    ["GET", /^\/v1\/jobs\/([^/]+)$/, ([id]) => {
      const entry = state.jobs.get(id as string);
      return entry ? { status: 200, body: entry.job } : notFound("job");
    }],
    ["POST", /^\/v1\/jobs\/([^/]+)\/cancel$/, ([id]) => {
      const entry = state.jobs.get(id as string);
      if (!entry) return notFound("job");
      // Like A1: a queued job is cancelled at once, a running one only cancel_requested.
      const current = entry.job.state ?? "queued";
      if (current === "cancel_requested") return { status: 200, body: entry.job };
      if (current === "queued") {
        finish(entry.job.job_id, { state: "cancelled" }, "job.cancelled");
        return { status: 200, body: entry.job };
      }
      if (current !== "running") return conflict("a queued or running job", `state ${current}`);
      entry.job = { ...entry.job, state: "cancel_requested", revision: entry.job.revision + 1 };
      return { status: 200, body: entry.job };
    }],
    ["GET", /^\/v1\/jobs\/([^/]+)\/events$/, ([id], _q, _b, _r, headers) => {
      const entry = state.jobs.get(id as string);
      if (!entry) return notFound("job");
      const after = Number(headers["last-event-id"] ?? 0);
      return { status: 200, body: entry.events.filter((event) => event.id > after) };
    }],
    ["GET", /^\/v1\/kbs\/([^/]+)\/versions$/, ([id]) => {
      const kb = kbOr404(id as string);
      if (isReply(kb)) return kb;
      const items = [...state.versions.values()].filter((version) => version.kb_id === kb.kb_id);
      return { status: 200, body: items.sort((a, b) => ((a.created_at ?? "") < (b.created_at ?? "") ? -1 : 1)) };
    }],
    ["GET", /^\/v1\/kbs\/([^/]+)\/version-diff$/, ([id], query) => {
      const left = state.versions.get(query.get("left") ?? "");
      const right = state.versions.get(query.get("right") ?? "");
      if (!left || !right || left.kb_id !== id || right.kb_id !== id) return notFound("comparable versions");
      const l = left.document_revisions ?? {};
      const r = right.document_revisions ?? {};
      return {
        status: 200,
        body: {
          left: left.version_id,
          right: right.version_id,
          added: Object.keys(r).filter((doc) => !(doc in l)).sort(),
          modified: Object.keys(r).filter((doc) => doc in l && l[doc] !== r[doc]).sort(),
          removed: Object.keys(l).filter((doc) => !(doc in r)).sort(),
        },
      };
    }],
    ["POST", /^\/v1\/versions\/([^/]+)\/publish$/, ([id], _q, body) => activate(id as string, null, body?.expected_active_version_id ?? null)],
    ["POST", /^\/v1\/kbs\/([^/]+)\/rollback$/, ([id], _q, body) =>
      activate(body?.target_version_id, id as string, body?.expected_active_version_id ?? null)],
    ["GET", /^\/v1\/kbs\/([^/]+)\/documents$/, ([id], query) => {
      const kb = kbOr404(id as string);
      if (isReply(kb)) return kb;
      const docs = [...state.documents.values()].filter((item) => item.doc.kb_id === kb.kb_id && !item.doc.deleted).map((item) => item.doc);
      return page(docs, (doc) => doc.document_id, query);
    }],
    ["POST", /^\/v1\/kbs\/([^/]+)\/documents$/, ([id], _q, body) => {
      if (body?.kb_id !== id) return invalid("kb_id", "must match the URL");
      if (!body.title) return invalid("title", "String should have at least 1 character");
      const stored = addRevision(id as string, null, body.title, body.text ?? "", "document", null, body.relative_path ?? null);
      return { status: 202, body: receipt(id as string, stored.doc.document_id, null, rebuildAll(id as string)) };
    }],
    ["GET", /^\/v1\/documents\/([^/]+)$/, ([id], query) => {
      const stored = state.documents.get(id as string);
      if (!stored) return notFound("document");
      const wanted = query.get("revision_id");
      const revision = wanted ? stored.revisions.find((item) => item.revision_id === wanted) : stored.revisions.at(-1);
      return revision ? { status: 200, body: { document: stored.doc, revision } } : notFound("revision");
    }],
    ["PATCH", /^\/v1\/documents\/([^/]+)$/, ([id], _q, body) => {
      const stored = state.documents.get(id as string);
      if (!stored || stored.doc.deleted) return notFound("document");
      if (!body?.expected_revision_id) return invalid("expected_revision_id", "is required to edit");
      if (body.expected_revision_id !== stored.doc.latest_revision_id) {
        return conflict(`revision ${body.expected_revision_id}`, `revision ${stored.doc.latest_revision_id}`);
      }
      addRevision(stored.doc.kb_id, stored.doc.document_id, body.title, body.text ?? "", stored.doc.content_kind ?? "document", stored.sourceId, body.relative_path ?? stored.path);
      return { status: 200, body: receipt(stored.doc.kb_id, stored.doc.document_id, null, rebuildAll(stored.doc.kb_id)) };
    }],
    ["DELETE", /^\/v1\/documents\/([^/]+)$/, ([id], query) => {
      const stored = state.documents.get(id as string);
      if (!stored || stored.doc.deleted) return notFound("document");
      const expected = query.get("expected_revision_id");
      if (expected && expected !== stored.doc.latest_revision_id) return conflict(`revision ${expected}`, `revision ${stored.doc.latest_revision_id}`);
      stored.doc = { ...stored.doc, deleted: true };
      return { status: 200, body: receipt(stored.doc.kb_id, stored.doc.document_id, null, rebuildAll(stored.doc.kb_id)) };
    }],
    ["GET", /^\/v1\/kbs\/([^/]+)\/qa-pairs$/, ([id], query) => {
      const kb = kbOr404(id as string);
      if (isReply(kb)) return kb;
      return page([...state.qa.values()].filter((pair) => pair.kb_id === kb.kb_id && !pair.deleted), (pair) => pair.qa_id, query);
    }],
    ["POST", /^\/v1\/kbs\/([^/]+)\/qa-pairs$/, ([id], _q, body) => {
      if (body?.kb_id !== id) return invalid("kb_id", "must match the URL");
      return putQA(id as string, null, body);
    }],
    ["GET", /^\/v1\/qa-pairs\/([^/]+)$/, ([id]) => {
      const pair = state.qa.get(id as string);
      return pair && !pair.deleted ? { status: 200, body: pair } : notFound("qa pair");
    }],
    ["PATCH", /^\/v1\/qa-pairs\/([^/]+)$/, ([id], _q, body) => putQA(body?.kb_id, id as string, body)],
    ["DELETE", /^\/v1\/qa-pairs\/([^/]+)$/, ([id], query) => {
      const pair = state.qa.get(id as string);
      if (!pair || pair.deleted) return notFound("qa pair");
      const expected = query.get("expected_revision_id");
      if (expected && expected !== pair.revision_id) return conflict(`revision ${expected}`, `revision ${pair.revision_id}`);
      state.qa.set(pair.qa_id, { ...pair, deleted: true });
      const stored = state.documents.get(pair.qa_id);
      if (stored) stored.doc = { ...stored.doc, deleted: true };
      return { status: 200, body: receipt(pair.kb_id, pair.qa_id, null, rebuildAll(pair.kb_id)) };
    }],
    ["GET", /^\/v1\/issues$/, (_m, query) => {
      if (state.issues === null) return error(501, "FEATURE_NOT_IMPLEMENTED", "'feedback' is not implemented in the scaffold build");
      const wanted = query.get("status");
      return { status: 200, body: state.issues.filter((issue) => !wanted || (issue.status ?? "open") === wanted) };
    }],
  ];
  /** Publish (kbScope null) or roll back; the active pointer moves only if `expected` still holds. */
  function activate(versionId: string, kbScope: string | null, expected: string | null): Reply {
    const version = state.versions.get(versionId);
    if (!version || (kbScope && version.kb_id !== kbScope)) return notFound("version");
    if (!["ready", "published"].includes(version.state ?? "draft")) return conflict("a ready version", `state ${version.state}`);
    const kb = state.kbs.get(version.kb_id);
    if (!kb) return notFound("knowledge base");
    if ((kb.active_version_id ?? null) !== expected) {
      return conflict(`active version ${expected ?? "none"}`, `active version ${kb.active_version_id ?? "none"}`);
    }
    touchKB(kb, { active_version_id: version.version_id });
    const published: Snapshot = { ...version, state: "published" };
    state.versions.set(versionId, published);
    return { status: 200, body: published };
  }

  function putQA(kbId: string, qaId: string | null, body: Body): Reply {
    if (!body?.question || !body?.answer) return invalid("question", "question and answer are required");
    const existing = qaId ? state.qa.get(qaId) : undefined;
    if (qaId && (!existing || existing.deleted)) return notFound("qa pair");
    if (existing && !body.expected_revision_id) return invalid("expected_revision_id", "is required to edit");
    if (existing && body.expected_revision_id !== existing.revision_id) {
      return conflict(`revision ${body.expected_revision_id}`, `revision ${existing.revision_id}`);
    }
    const stored = addRevision(kbId, existing?.qa_id ?? null, String(body.question).slice(0, 200), `问：${body.question}\n答：${body.answer}`, "qa_pair", null, null);
    const pair: QAPair = {
      qa_id: stored.doc.document_id, kb_id: kbId, question: body.question, answer: body.answer,
      revision_id: stored.doc.latest_revision_id, deleted: false, updated_at: clock(),
    };
    state.qa.set(pair.qa_id, pair);
    return { status: existing ? 200 : 202, body: receipt(kbId, pair.qa_id, null, rebuildAll(kbId)) };
  }

  const fetchImpl = async (input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> => {
    const url = new URL(String(input));
    const method = (init.method ?? "GET").toUpperCase();
    const headers: Record<string, string> = {};
    for (const [name, value] of Object.entries((init.headers ?? {}) as Record<string, string>)) headers[name.toLowerCase()] = value;
    const raw = init.body instanceof Blob ? await init.body.arrayBuffer() : null;
    const body = typeof init.body === "string" ? JSON.parse(init.body) : undefined;
    calls.push({ method, path: url.pathname, query: url.searchParams, headers, body, signal: init.signal ?? null });
    const key = `${method} ${url.pathname}`;
    const held = holds.findIndex((item) => item.key === key);
    if (held >= 0) {
      const [{ gate }] = holds.splice(held, 1) as [{ key: string; gate: Promise<void> }];
      await new Promise<void>((resolve, reject) => {
        void gate.then(resolve);
        init.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")), { once: true });
      });
    }
    const failed = failures.findIndex((item) => item.key === key);
    let reply: Reply;
    if (failed >= 0) {
      reply = (failures.splice(failed, 1)[0] as { reply: Reply }).reply;
    } else {
      const route = routes.find(([m, pattern]) => m === method && pattern.test(url.pathname));
      const match = route ? (url.pathname.match(route[1]) ?? []).slice(1) : [];
      reply = route
        ? await route[2](match, url.searchParams, body, raw, headers)
        : error(501, "FEATURE_NOT_IMPLEMENTED", `'${url.pathname}' is not implemented in the fake`);
    }
    const requestId = `req-${++requestSeq}`;
    const payload = reply.status >= 400 && reply.body && typeof reply.body === "object" ? { ...reply.body, request_id: requestId } : reply.body;
    return new Response(reply.status === 204 ? null : JSON.stringify(payload ?? null), {
      status: reply.status,
      headers: { "Content-Type": "application/json", "X-Request-ID": requestId },
    });
  };
  return {
    client: createClient({ baseUrl: FAKE_API, fetch: fetchImpl }),
    calls,
    state,
    failNext(method, path, status, code, message = "injected failure", details = []) {
      failures.push({ key: `${method.toUpperCase()} ${path}`, reply: error(status, code, message, details) });
    },
    hold(method, path) {
      let release!: () => void;
      const gate = new Promise<void>((resolve) => {
        release = resolve;
      });
      holds.push({ key: `${method.toUpperCase()} ${path}`, gate });
      return () => release();
    },
    runWorker() {
      const queued = [...state.jobs.values()].filter((entry) => entry.job.state === "queued");
      for (const entry of queued) execute(entry.job.job_id, entry.payload);
      return queued.map((entry) => entry.job.job_id);
    },
    seedKB(name) {
      return putKB({
        kb_id: nextId("kb"), name, description: "", domain_tags: [], routing_examples: [],
        active_version_id: null, etag: `etag_${++sequence}`, updated_at: clock(),
      });
    },
    seedDocument(kbId, title, text, sourceId = null, path = null) {
      return addRevision(kbId, null, title, text, "document", sourceId, path).doc;
    },
    seedVersion(kbId, versionState, revisions, activateIt = false) {
      const kb = state.kbs.get(kbId);
      const version: Snapshot = {
        version_id: nextId("ver"), kb_id: kbId, parent_version_id: kb?.active_version_id ?? null, state: versionState,
        document_revisions: revisions, keyword_profile: "zh-bm25-v1", keyword_index_ref: "idx", vector_index: "absent", created_at: clock(),
      };
      state.versions.set(version.version_id, version);
      if (activateIt && kb) touchKB(kb, { active_version_id: version.version_id });
      return version;
    },
  };
}
