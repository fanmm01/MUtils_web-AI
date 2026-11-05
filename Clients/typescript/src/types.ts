/**
 * Contract-shaped request/response types for the shared HTTP client.
 *
 * These mirror the frozen OpenAPI/SSE schema (``docs/openapi.json``,
 * ``docs/events.schema.json``). Do not hand-maintain a divergent copy: regenerate
 * from those files when the Contract Gate changes them.
 */

export type Id = string;

export type SelectionMode = "explicit" | "auto";
export type InferencePolicy = "local_only" | "configured";
export type AnswerTerminal =
  | "pending"
  | "completed"
  | "refused"
  | "failed"
  | "cancelled";
export type JobState =
  | "queued"
  | "running"
  | "cancel_requested"
  | "succeeded"
  | "failed"
  | "cancelled"
  | "outcome_unknown";

export interface KBTarget {
  kb_id: Id;
  version_id?: Id | null;
}

export interface ExplicitSelection {
  mode: "explicit";
  targets: KBTarget[];
}

export interface AutoSelection {
  mode: "auto";
  candidate_kb_ids?: Id[] | null;
  max_kbs?: number | null;
}

export type RetrievalSelection = ExplicitSelection | AutoSelection;

export interface InferenceSelection {
  profile_id?: Id | null;
  policy?: InferencePolicy;
}

export interface ErrorDetail {
  field?: string | null;
  reason: string;
}

/** Body of every non-2xx JSON response. */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: ErrorDetail[];
  };
  request_id: string;
}

export interface Page<T> {
  items: T[];
  next_cursor: string | null;
}

export interface KnowledgeBase {
  kb_id: Id;
  name: string;
  description: string;
  domain_tags: string[];
  routing_examples: string[];
  active_version_id: Id | null;
  etag: string;
  updated_at: string;
}

export interface Hit {
  kb_id: Id;
  version_id: Id;
  chunk_id: Id;
  text: string;
  score: number;
  locator?: Record<string, unknown> | null;
}

export interface Citation {
  citation_id: Id;
  chunk_id: Id;
  kb_id: Id;
  version_id: Id;
  revision_id: Id;
  quote: string;
  locator?: Record<string, unknown> | null;
  content_hash: string;
  detail_path: string;
}

export interface Answer {
  answer_id: Id;
  session_id: Id;
  question: string;
  status: AnswerTerminal;
  text: string;
  requested_selection?: RetrievalSelection | null;
  resolved_scope?: { scope_id: Id; targets: KBTarget[]; resolved_at: string } | null;
  used_kb_ids: Id[];
  citations: Citation[];
  error_code?: string | null;
  refusal_reason?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface AnswerHandle {
  answer_id: Id;
  session_id: Id;
  status: AnswerTerminal;
  poll_url: string;
  events_url: string;
  retry_after_ms: number;
}

export interface AskResponse {
  answer?: Answer | null;
  handle?: AnswerHandle | null;
}

export interface AnswerEvent {
  schema_version: number;
  answer_id: Id;
  session_id: Id;
  seq: number;
  timestamp: string;
  event:
    | "answer.accepted"
    | "inference.bound"
    | "selection.resolved"
    | "retrieval.completed"
    | "citation.ready"
    | "answer.delta"
    | "answer.completed"
    | "answer.refused"
    | "answer.failed"
    | "answer.cancelled";
  scope_revision?: number | null;
  inference_revision?: number | null;
  binding_id?: Id | null;
  scope_id?: Id | null;
  data: Record<string, unknown>;
}

export interface JobEvent {
  schema_version: number;
  job_id: Id;
  seq: number;
  timestamp: string;
  event: "job.accepted" | "job.progress" | "job.completed" | "job.failed" | "job.cancelled";
  progress?: number | null;
  bytes_downloaded?: number | null;
  total_bytes?: number | null;
  phase?: string | null;
  diagnostic?: string | null;
}

export type SSEEvent = AnswerEvent | JobEvent;

export interface Job {
  job_id: Id;
  kind: "import" | "model_install" | "model_verify";
  state: JobState;
  progress: number;
  revision: number;
  idempotency_key?: string | null;
  result_version_id?: Id | null;
  error_code?: string | null;
  created_at: string;
}

export interface ModelRef {
  model_id: Id;
  runtime_target_id: Id;
  exact_tag: string;
  family?: string | null;
  parameters?: string | null;
  quantization?: string | null;
  size_bytes?: number | null;
  installed: "present" | "absent" | "unknown";
  downloaded: "present" | "absent" | "unknown";
  loaded: "present" | "absent" | "unknown";
  verified_roles: string[];
  identity_status: "resolved" | "unresolved";
  digest?: string | null;
}

export interface InstallPreview {
  preview_id: Id;
  target_id: Id;
  model_ref: string;
  preview_hash: string;
  identity_status: "resolved" | "unresolved";
  size_bytes?: number | null;
  missing_layers?: number | null;
  target_cache?: string | null;
  license_url?: string | null;
  unknown_fields: string[];
  created_at: string;
}

export interface Session {
  session_id: Id;
  principal_id: Id;
  selection: RetrievalSelection;
  scope_revision: number;
  history_policy: "reset_on_scope_change" | "carry_user_questions";
  inference: InferenceSelection;
  inference_revision: number;
  created_at: string;
}
