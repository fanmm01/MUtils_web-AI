/**
 * Public contract types of the shared SDK.
 *
 * Request, response and event shapes are GENERATED from the frozen Contract Gate
 * artifacts (`docs/openapi.json`, `docs/events.schema.json`) into
 * `./generated/`; `npm run typecheck` fails while they are stale. Only the few
 * shapes those artifacts do not describe are written here, each marked with
 * the reason.
 */

import type { CreateSession } from "./generated/openapi.js";
import type { AnswerEvent, JobEvent } from "./generated/events.js";

export type * from "./generated/openapi.js";
export type {
  AnswerEvent,
  ErrorCode,
  EventSchemaVersion,
  HttpSchemaVersion,
  JobEvent,
  JobEventType,
} from "./generated/events.js";

/** Opaque server-generated identifier. */
export type Id = string;

/**
 * The shared `explicit | auto` selector. OpenAPI inlines this union in every
 * request schema instead of naming it; it is taken from `CreateSession` so it
 * cannot diverge.
 */
export type RetrievalSelection = NonNullable<CreateSession["selection"]>;
export type SelectionMode = RetrievalSelection["mode"];

/**
 * Error envelope of every non-2xx JSON response (`qa_contracts.errors.APIErrorResponse`).
 * Written here because `docs/openapi.json` does not export that model: its
 * routes only declare FastAPI's 422 `HTTPValidationError`, which the server
 * never sends (it rewrites validation errors into this envelope).
 */
export interface ErrorDetail {
  field?: string | null;
  reason: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: ErrorDetail[];
  };
  request_id: string;
}

/** An event delivered by an SSE stream; answer and job events share the parser. */
export type SSEEvent = AnswerEvent | JobEvent;
