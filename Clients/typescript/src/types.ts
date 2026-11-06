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
import type { AnswerEvent, AnswerEventV2, JobEvent, JobEventV2 } from "./generated/events.js";

export type * from "./generated/openapi.js";
export type {
  AnswerEvent,
  AnswerEventV2,
  ErrorCode,
  EventSchemaVersion,
  HttpSchemaVersion,
  JobEvent,
  JobEventType,
  JobEventV2,
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

/** Stable error envelope exported from the server's OpenAPI responses. */
export type ApiErrorBody = import("./generated/openapi.js").APIErrorResponse;
export type ErrorDetail = import("./generated/openapi.js").ErrorDetail;

export type { SSEEvent } from "./sse.js";
