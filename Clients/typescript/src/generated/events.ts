/**
 * GENERATED from docs/events.schema.json by Clients/typescript/scripts/generate-types.mjs.
 * Do not edit. Regenerate with `npm run gen:types -w @qa/client`;
 * `npm run typecheck` fails while this file is stale.
 */

export type paths = Record<string, never>;
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AnswerEvent */
        AnswerEvent: {
            /** Answer Id */
            answer_id: string;
            /**
             * Binding Id
             * @default null
             */
            binding_id?: string | null;
            /** Data */
            data?: {
                [key: string]: unknown;
            };
            /**
             * Event
             * @enum {string}
             */
            event: "answer.accepted" | "inference.bound" | "selection.resolved" | "retrieval.completed" | "citation.ready" | "answer.delta" | "answer.completed" | "answer.refused" | "answer.failed" | "answer.cancelled";
            /**
             * Inference Revision
             * @default null
             */
            inference_revision?: number | null;
            /**
             * Schema Version
             * @default 1
             * @constant
             */
            schema_version?: 1;
            /**
             * Scope Id
             * @default null
             */
            scope_id?: string | null;
            /**
             * Scope Revision
             * @default null
             */
            scope_revision?: number | null;
            /** Seq */
            seq: number;
            /** Session Id */
            session_id: string;
            /**
             * Timestamp
             * Format: date-time
             */
            timestamp?: string;
        };
        /**
         * JobEventType
         * @enum {string}
         */
        JobEventType: "job.accepted" | "job.progress" | "job.completed" | "job.failed" | "job.cancelled";
        /** JobEvent */
        JobEvent: {
            /**
             * Bytes Downloaded
             * @default null
             */
            bytes_downloaded?: number | null;
            /**
             * Diagnostic
             * @default null
             */
            diagnostic?: string | null;
            event: components["schemas"]["JobEventType"];
            /** Job Id */
            job_id: string;
            /**
             * Phase
             * @default null
             */
            phase?: string | null;
            /**
             * Progress
             * @default null
             */
            progress?: number | null;
            /**
             * Schema Version
             * @default 1
             * @constant
             */
            schema_version?: 1;
            /** Seq */
            seq: number;
            /**
             * Timestamp
             * Format: date-time
             */
            timestamp?: string;
            /**
             * Total Bytes
             * @default null
             */
            total_bytes?: number | null;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type AnswerEvent = components['schemas']['AnswerEvent'];
export type JobEventType = components['schemas']['JobEventType'];
export type JobEvent = components['schemas']['JobEvent'];
export type $defs = Record<string, never>;
export type operations = Record<string, never>;

/** Stable error codes (events.schema.json `error_codes`). */
export type ErrorCode = "CONFLICT" | "EVIDENCE_INSUFFICIENT" | "FEATURE_NOT_IMPLEMENTED" | "GONE" | "INFERENCE_POLICY_VIOLATION" | "INTERNAL_ERROR" | "MODEL_CAPABILITY_MISSING" | "MODEL_CHANGED" | "MODEL_UNAVAILABLE" | "NOT_FOUND" | "PERMISSION_DENIED" | "PROVIDER_UNAVAILABLE" | "RATE_LIMITED" | "UNAUTHENTICATED" | "VALIDATION_FAILED";
/** SSE event schema version and HTTP contract version of the frozen artifacts. */
export type EventSchemaVersion = 1;
export type HttpSchemaVersion = 2;
