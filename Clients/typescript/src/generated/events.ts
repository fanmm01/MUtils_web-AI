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
        /** Answer */
        AnswerEventV2_Answer: {
            /** Answer Id */
            answer_id: string;
            /** @default null */
            binding?: components["schemas"]["AnswerEventV2_InferenceBinding"] | null;
            /** Citations */
            citations?: components["schemas"]["AnswerEventV2_Citation"][];
            /**
             * Completed At
             * @default null
             */
            completed_at?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            /** @default null */
            effective_inference?: components["schemas"]["AnswerEventV2_EffectiveInference"] | null;
            /** @default null */
            effective_selection?: components["schemas"]["AnswerEventV2_EffectiveSelection"] | null;
            /**
             * Error Code
             * @default null
             */
            error_code?: string | null;
            /** Question */
            question: string;
            /**
             * Refusal Reason
             * @default null
             */
            refusal_reason?: string | null;
            /**
             * Requested Selection
             * @default null
             */
            requested_selection?: (components["schemas"]["AnswerEventV2_ExplicitSelection"] | components["schemas"]["AnswerEventV2_AutoSelection"]) | null;
            /** @default null */
            resolved_scope?: components["schemas"]["AnswerEventV2_ResolvedScope"] | null;
            /** @default null */
            selection_result?: components["schemas"]["AnswerEventV2_SelectionResult"] | null;
            /** Session Id */
            session_id: string;
            /** @default pending */
            status?: components["schemas"]["AnswerEventV2_AnswerTerminal"];
            /**
             * Text
             * @default
             */
            text?: string;
            /** Used Kb Ids */
            used_kb_ids?: string[];
        };
        /**
         * AnswerAcceptedData
         * @description The accepted request fixes revisions before any model is called.
         */
        AnswerEventV2_AnswerAcceptedData: Record<string, never>;
        /** AnswerAcceptedV2 */
        AnswerEventV2_AnswerAcceptedV2: {
            /** Answer Id */
            answer_id: string;
            /** Binding Id */
            binding_id: string | null;
            data: components["schemas"]["AnswerEventV2_AnswerAcceptedData"];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            event: "answer.accepted";
            /** Inference Revision */
            inference_revision: number;
            /**
             * Schema Version
             * @default 2
             * @constant
             */
            schema_version?: 2;
            /** Scope Id */
            scope_id: string | null;
            /** Scope Revision */
            scope_revision: number;
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
        /** AnswerCancelledData */
        AnswerEventV2_AnswerCancelledData: {
            /**
             * Incomplete
             * @default false
             */
            incomplete?: boolean;
            /** Reason */
            reason: string;
        };
        /** AnswerCancelledV2 */
        AnswerEventV2_AnswerCancelledV2: {
            /** Answer Id */
            answer_id: string;
            /** Binding Id */
            binding_id: string | null;
            data: components["schemas"]["AnswerEventV2_AnswerCancelledData"];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            event: "answer.cancelled";
            /** Inference Revision */
            inference_revision: number;
            /**
             * Schema Version
             * @default 2
             * @constant
             */
            schema_version?: 2;
            /** Scope Id */
            scope_id: string | null;
            /** Scope Revision */
            scope_revision: number;
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
        /** AnswerCompletedData */
        AnswerEventV2_AnswerCompletedData: {
            answer: components["schemas"]["AnswerEventV2_Answer"];
        };
        /** AnswerCompletedV2 */
        AnswerEventV2_AnswerCompletedV2: {
            /** Answer Id */
            answer_id: string;
            /** Binding Id */
            binding_id: string | null;
            data: components["schemas"]["AnswerEventV2_AnswerCompletedData"];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            event: "answer.completed";
            /** Inference Revision */
            inference_revision: number;
            /**
             * Schema Version
             * @default 2
             * @constant
             */
            schema_version?: 2;
            /** Scope Id */
            scope_id: string | null;
            /** Scope Revision */
            scope_revision: number;
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
        /** AnswerDeltaData */
        AnswerEventV2_AnswerDeltaData: {
            /** Citation Ids */
            citation_ids: string[];
            /** Sentence Id */
            sentence_id: string;
            /** Text */
            text: string;
        };
        /** AnswerDeltaV2 */
        AnswerEventV2_AnswerDeltaV2: {
            /** Answer Id */
            answer_id: string;
            /** Binding Id */
            binding_id: string | null;
            data: components["schemas"]["AnswerEventV2_AnswerDeltaData"];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            event: "answer.delta";
            /** Inference Revision */
            inference_revision: number;
            /**
             * Schema Version
             * @default 2
             * @constant
             */
            schema_version?: 2;
            /** Scope Id */
            scope_id: string | null;
            /** Scope Revision */
            scope_revision: number;
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
        /** AnswerFailedData */
        AnswerEventV2_AnswerFailedData: {
            /**
             * Incomplete
             * @default false
             */
            incomplete?: boolean;
            /** Reason */
            reason: string;
        };
        /** AnswerFailedV2 */
        AnswerEventV2_AnswerFailedV2: {
            /** Answer Id */
            answer_id: string;
            /** Binding Id */
            binding_id: string | null;
            data: components["schemas"]["AnswerEventV2_AnswerFailedData"];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            event: "answer.failed";
            /** Inference Revision */
            inference_revision: number;
            /**
             * Schema Version
             * @default 2
             * @constant
             */
            schema_version?: 2;
            /** Scope Id */
            scope_id: string | null;
            /** Scope Revision */
            scope_revision: number;
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
        /** AnswerRefusedData */
        AnswerEventV2_AnswerRefusedData: {
            /** Reason */
            reason: string;
        };
        /** AnswerRefusedV2 */
        AnswerEventV2_AnswerRefusedV2: {
            /** Answer Id */
            answer_id: string;
            /** Binding Id */
            binding_id: string | null;
            data: components["schemas"]["AnswerEventV2_AnswerRefusedData"];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            event: "answer.refused";
            /** Inference Revision */
            inference_revision: number;
            /**
             * Schema Version
             * @default 2
             * @constant
             */
            schema_version?: 2;
            /** Scope Id */
            scope_id: string | null;
            /** Scope Revision */
            scope_revision: number;
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
         * AnswerTerminal
         * @enum {string}
         */
        AnswerEventV2_AnswerTerminal: "pending" | "completed" | "refused" | "failed" | "cancelled";
        /** AutoSelection */
        AnswerEventV2_AutoSelection: {
            /**
             * Candidate Kb Ids
             * @default null
             */
            candidate_kb_ids?: string[] | null;
            /**
             * Max Kbs
             * @default null
             */
            max_kbs?: number | null;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            mode: "auto";
        };
        /**
         * CandidateEmbedder
         * @description One candidate snapshot is pinned to its exact embedding role and profile.
         */
        AnswerEventV2_CandidateEmbedder: {
            binding: components["schemas"]["AnswerEventV2_RoleBinding"];
            /** Fingerprint */
            fingerprint: string;
            /** Kb Id */
            kb_id: string;
            /** Version Id */
            version_id: string;
        };
        /** Citation */
        AnswerEventV2_Citation: {
            /** Chunk Id */
            chunk_id: string;
            /** Citation Id */
            citation_id: string;
            /** Content Hash */
            content_hash: string;
            /** Detail Path */
            detail_path: string;
            /** Kb Id */
            kb_id: string;
            /** @default null */
            locator?: components["schemas"]["AnswerEventV2_Locator"] | null;
            /** Quote */
            quote: string;
            /** Revision Id */
            revision_id: string;
            /** Version Id */
            version_id: string;
        };
        /** CitationReadyData */
        AnswerEventV2_CitationReadyData: {
            citation: components["schemas"]["AnswerEventV2_Citation"];
        };
        /** CitationReadyV2 */
        AnswerEventV2_CitationReadyV2: {
            /** Answer Id */
            answer_id: string;
            /** Binding Id */
            binding_id: string | null;
            data: components["schemas"]["AnswerEventV2_CitationReadyData"];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            event: "citation.ready";
            /** Inference Revision */
            inference_revision: number;
            /**
             * Schema Version
             * @default 2
             * @constant
             */
            schema_version?: 2;
            /** Scope Id */
            scope_id: string | null;
            /** Scope Revision */
            scope_revision: number;
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
        /** EffectiveInference */
        AnswerEventV2_EffectiveInference: {
            /**
             * Profile Revision
             * @default null
             */
            profile_revision?: string | null;
            selection: components["schemas"]["AnswerEventV2_InferenceSelection"];
            /**
             * Source
             * @default default
             * @enum {string}
             */
            source?: "request" | "session" | "default";
        };
        /** EffectiveSelection */
        AnswerEventV2_EffectiveSelection: {
            /** Selection */
            selection: components["schemas"]["AnswerEventV2_ExplicitSelection"] | components["schemas"]["AnswerEventV2_AutoSelection"];
            /**
             * Source
             * @default default
             * @enum {string}
             */
            source?: "request" | "session" | "default";
        };
        /**
         * ExecutionLocation
         * @enum {string}
         */
        AnswerEventV2_ExecutionLocation: "local" | "configured_remote";
        /** ExplicitSelection */
        AnswerEventV2_ExplicitSelection: {
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            mode: "explicit";
            /** Targets */
            targets: components["schemas"]["AnswerEventV2_KBTarget"][];
        };
        /** InferenceBinding */
        AnswerEventV2_InferenceBinding: {
            /** Binding Id */
            binding_id: string;
            /** Candidate Embedders */
            candidate_embedders?: components["schemas"]["AnswerEventV2_CandidateEmbedder"][];
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            policy: components["schemas"]["AnswerEventV2_InferencePolicy"];
            /**
             * Profile Revision
             * @default null
             */
            profile_revision?: string | null;
            /** Roles */
            roles?: components["schemas"]["AnswerEventV2_RoleBinding"][];
        };
        /** InferenceBoundData */
        AnswerEventV2_InferenceBoundData: {
            binding: components["schemas"]["AnswerEventV2_InferenceBinding"];
        };
        /** InferenceBoundV2 */
        AnswerEventV2_InferenceBoundV2: {
            /** Answer Id */
            answer_id: string;
            /** Binding Id */
            binding_id: string | null;
            data: components["schemas"]["AnswerEventV2_InferenceBoundData"];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            event: "inference.bound";
            /** Inference Revision */
            inference_revision: number;
            /**
             * Schema Version
             * @default 2
             * @constant
             */
            schema_version?: 2;
            /** Scope Id */
            scope_id: string | null;
            /** Scope Revision */
            scope_revision: number;
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
         * InferencePolicy
         * @enum {string}
         */
        AnswerEventV2_InferencePolicy: "local_only" | "configured";
        /** InferenceSelection */
        AnswerEventV2_InferenceSelection: {
            /** @default local_only */
            policy?: components["schemas"]["AnswerEventV2_InferencePolicy"];
            /**
             * Profile Id
             * @default null
             */
            profile_id?: string | null;
        };
        /**
         * KBTarget
         * @description One knowledge base pinned to an optional immutable version.
         */
        AnswerEventV2_KBTarget: {
            /** Kb Id */
            kb_id: string;
            /**
             * Version Id
             * @default null
             */
            version_id?: string | null;
        };
        /**
         * Locator
         * @description Traceable original position. Never invent a page number a format lacks.
         */
        AnswerEventV2_Locator: {
            /**
             * Cell Range
             * @default null
             */
            cell_range?: string | null;
            /**
             * End Line
             * @default null
             */
            end_line?: number | null;
            /**
             * Heading
             * @default null
             */
            heading?: string | null;
            kind: components["schemas"]["AnswerEventV2_LocatorKind"];
            /**
             * Page
             * @default null
             */
            page?: number | null;
            /**
             * Paragraph
             * @default null
             */
            paragraph?: number | null;
            /**
             * Sheet
             * @default null
             */
            sheet?: string | null;
            /**
             * Start Line
             * @default null
             */
            start_line?: number | null;
        };
        /**
         * LocatorKind
         * @enum {string}
         */
        AnswerEventV2_LocatorKind: "markdown_lines" | "text_lines" | "word_paragraph" | "word_table" | "excel_range" | "pdf_page" | "qa_fields";
        /**
         * ModelIdentity
         * @description An exact tag is an alias; only a resolved digest pins model bytes.
         *
         *     An adapter must compare this identity with a fresh runtime observation before
         *     every call. A mutable tag alone cannot promise reproducible results.
         */
        AnswerEventV2_ModelIdentity: {
            /**
             * Digest
             * @default null
             */
            digest?: string | null;
            /** Exact Tag */
            exact_tag: string;
            /**
             * Identity Status
             * @default unresolved
             * @enum {string}
             */
            identity_status?: "resolved" | "unresolved";
            /** Model Id */
            model_id: string;
            /**
             * Runtime Target Id
             * @default null
             */
            runtime_target_id?: string | null;
        };
        /**
         * ModelRole
         * @enum {string}
         */
        AnswerEventV2_ModelRole: "generator" | "rewriter" | "support_checker" | "reranker" | "embedder" | "token_counter";
        /**
         * PinnedKBTarget
         * @description An authorized KB resolved to its immutable version before retrieval.
         */
        AnswerEventV2_PinnedKBTarget: {
            /** Kb Id */
            kb_id: string;
            /** Version Id */
            version_id: string;
        };
        /** ResolvedScope */
        AnswerEventV2_ResolvedScope: {
            /**
             * Policy Version
             * @default p2-keyword
             */
            policy_version?: string;
            /**
             * Resolved At
             * Format: date-time
             */
            resolved_at?: string;
            /** Scope Id */
            scope_id: string;
            /** Targets */
            targets: components["schemas"]["AnswerEventV2_PinnedKBTarget"][];
        };
        /** RetrievalCompletedData */
        AnswerEventV2_RetrievalCompletedData: {
            /** Hit Count */
            hit_count: number;
        };
        /** RetrievalCompletedV2 */
        AnswerEventV2_RetrievalCompletedV2: {
            /** Answer Id */
            answer_id: string;
            /** Binding Id */
            binding_id: string | null;
            data: components["schemas"]["AnswerEventV2_RetrievalCompletedData"];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            event: "retrieval.completed";
            /** Inference Revision */
            inference_revision: number;
            /**
             * Schema Version
             * @default 2
             * @constant
             */
            schema_version?: 2;
            /** Scope Id */
            scope_id: string | null;
            /** Scope Revision */
            scope_revision: number;
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
        /** RoleBinding */
        AnswerEventV2_RoleBinding: {
            /**
             * Budget Tokens
             * @default null
             */
            budget_tokens?: number | null;
            identity: components["schemas"]["AnswerEventV2_ModelIdentity"];
            /** @default local */
            location?: components["schemas"]["AnswerEventV2_ExecutionLocation"];
            policy: components["schemas"]["AnswerEventV2_InferencePolicy"];
            role: components["schemas"]["AnswerEventV2_ModelRole"];
            /**
             * Runtime Target Id
             * @default null
             */
            runtime_target_id?: string | null;
            /**
             * Timeout Ms
             * @default null
             */
            timeout_ms?: number | null;
        };
        /** SelectionResolvedData */
        AnswerEventV2_SelectionResolvedData: {
            /** @default null */
            resolved_scope?: components["schemas"]["AnswerEventV2_ResolvedScope"] | null;
            result: components["schemas"]["AnswerEventV2_SelectionResult"];
        };
        /** SelectionResolvedV2 */
        AnswerEventV2_SelectionResolvedV2: {
            /** Answer Id */
            answer_id: string;
            /** Binding Id */
            binding_id: string | null;
            data: components["schemas"]["AnswerEventV2_SelectionResolvedData"];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            event: "selection.resolved";
            /** Inference Revision */
            inference_revision: number;
            /**
             * Schema Version
             * @default 2
             * @constant
             */
            schema_version?: 2;
            /** Scope Id */
            scope_id: string | null;
            /** Scope Revision */
            scope_revision: number;
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
        /** SelectionResult */
        AnswerEventV2_SelectionResult: {
            /**
             * Mode
             * @enum {string}
             */
            mode: "explicit" | "auto";
            /**
             * Policy Version
             * @default p2-keyword
             */
            policy_version?: string;
            /**
             * Reason
             * @default
             */
            reason?: string;
            status: components["schemas"]["AnswerEventV2_SelectionStatus"];
            /** Targets */
            targets?: components["schemas"]["AnswerEventV2_PinnedKBTarget"][];
        };
        /**
         * SelectionStatus
         * @enum {string}
         */
        AnswerEventV2_SelectionStatus: "resolved" | "no_match" | "needs_clarification";
        AnswerEventV2: components["schemas"]["AnswerEventV2_AnswerAcceptedV2"] | components["schemas"]["AnswerEventV2_InferenceBoundV2"] | components["schemas"]["AnswerEventV2_SelectionResolvedV2"] | components["schemas"]["AnswerEventV2_RetrievalCompletedV2"] | components["schemas"]["AnswerEventV2_CitationReadyV2"] | components["schemas"]["AnswerEventV2_AnswerDeltaV2"] | components["schemas"]["AnswerEventV2_AnswerCompletedV2"] | components["schemas"]["AnswerEventV2_AnswerRefusedV2"] | components["schemas"]["AnswerEventV2_AnswerFailedV2"] | components["schemas"]["AnswerEventV2_AnswerCancelledV2"];
        /**
         * JobEventV2
         * @description New install/recovery states never overload the persisted v1 event enum.
         */
        JobEventV2: {
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
            /**
             * Event
             * @enum {string}
             */
            event: "job.accepted" | "job.progress" | "job.cancel_requested" | "job.outcome_unknown" | "job.completed" | "job.failed" | "job.cancelled";
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
             * @default 2
             * @constant
             */
            schema_version?: 2;
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
export type AnswerEventV2_Answer = components['schemas']['AnswerEventV2_Answer'];
export type AnswerEventV2_AnswerAcceptedData = components['schemas']['AnswerEventV2_AnswerAcceptedData'];
export type AnswerEventV2_AnswerAcceptedV2 = components['schemas']['AnswerEventV2_AnswerAcceptedV2'];
export type AnswerEventV2_AnswerCancelledData = components['schemas']['AnswerEventV2_AnswerCancelledData'];
export type AnswerEventV2_AnswerCancelledV2 = components['schemas']['AnswerEventV2_AnswerCancelledV2'];
export type AnswerEventV2_AnswerCompletedData = components['schemas']['AnswerEventV2_AnswerCompletedData'];
export type AnswerEventV2_AnswerCompletedV2 = components['schemas']['AnswerEventV2_AnswerCompletedV2'];
export type AnswerEventV2_AnswerDeltaData = components['schemas']['AnswerEventV2_AnswerDeltaData'];
export type AnswerEventV2_AnswerDeltaV2 = components['schemas']['AnswerEventV2_AnswerDeltaV2'];
export type AnswerEventV2_AnswerFailedData = components['schemas']['AnswerEventV2_AnswerFailedData'];
export type AnswerEventV2_AnswerFailedV2 = components['schemas']['AnswerEventV2_AnswerFailedV2'];
export type AnswerEventV2_AnswerRefusedData = components['schemas']['AnswerEventV2_AnswerRefusedData'];
export type AnswerEventV2_AnswerRefusedV2 = components['schemas']['AnswerEventV2_AnswerRefusedV2'];
export type AnswerEventV2_AnswerTerminal = components['schemas']['AnswerEventV2_AnswerTerminal'];
export type AnswerEventV2_AutoSelection = components['schemas']['AnswerEventV2_AutoSelection'];
export type AnswerEventV2_CandidateEmbedder = components['schemas']['AnswerEventV2_CandidateEmbedder'];
export type AnswerEventV2_Citation = components['schemas']['AnswerEventV2_Citation'];
export type AnswerEventV2_CitationReadyData = components['schemas']['AnswerEventV2_CitationReadyData'];
export type AnswerEventV2_CitationReadyV2 = components['schemas']['AnswerEventV2_CitationReadyV2'];
export type AnswerEventV2_EffectiveInference = components['schemas']['AnswerEventV2_EffectiveInference'];
export type AnswerEventV2_EffectiveSelection = components['schemas']['AnswerEventV2_EffectiveSelection'];
export type AnswerEventV2_ExecutionLocation = components['schemas']['AnswerEventV2_ExecutionLocation'];
export type AnswerEventV2_ExplicitSelection = components['schemas']['AnswerEventV2_ExplicitSelection'];
export type AnswerEventV2_InferenceBinding = components['schemas']['AnswerEventV2_InferenceBinding'];
export type AnswerEventV2_InferenceBoundData = components['schemas']['AnswerEventV2_InferenceBoundData'];
export type AnswerEventV2_InferenceBoundV2 = components['schemas']['AnswerEventV2_InferenceBoundV2'];
export type AnswerEventV2_InferencePolicy = components['schemas']['AnswerEventV2_InferencePolicy'];
export type AnswerEventV2_InferenceSelection = components['schemas']['AnswerEventV2_InferenceSelection'];
export type AnswerEventV2_KBTarget = components['schemas']['AnswerEventV2_KBTarget'];
export type AnswerEventV2_Locator = components['schemas']['AnswerEventV2_Locator'];
export type AnswerEventV2_LocatorKind = components['schemas']['AnswerEventV2_LocatorKind'];
export type AnswerEventV2_ModelIdentity = components['schemas']['AnswerEventV2_ModelIdentity'];
export type AnswerEventV2_ModelRole = components['schemas']['AnswerEventV2_ModelRole'];
export type AnswerEventV2_PinnedKBTarget = components['schemas']['AnswerEventV2_PinnedKBTarget'];
export type AnswerEventV2_ResolvedScope = components['schemas']['AnswerEventV2_ResolvedScope'];
export type AnswerEventV2_RetrievalCompletedData = components['schemas']['AnswerEventV2_RetrievalCompletedData'];
export type AnswerEventV2_RetrievalCompletedV2 = components['schemas']['AnswerEventV2_RetrievalCompletedV2'];
export type AnswerEventV2_RoleBinding = components['schemas']['AnswerEventV2_RoleBinding'];
export type AnswerEventV2_SelectionResolvedData = components['schemas']['AnswerEventV2_SelectionResolvedData'];
export type AnswerEventV2_SelectionResolvedV2 = components['schemas']['AnswerEventV2_SelectionResolvedV2'];
export type AnswerEventV2_SelectionResult = components['schemas']['AnswerEventV2_SelectionResult'];
export type AnswerEventV2_SelectionStatus = components['schemas']['AnswerEventV2_SelectionStatus'];
export type AnswerEventV2 = components['schemas']['AnswerEventV2'];
export type JobEventV2 = components['schemas']['JobEventV2'];
export type $defs = Record<string, never>;
export type operations = Record<string, never>;

/** Stable error codes (events.schema.json `error_codes`). */
export type ErrorCode = "CONFLICT" | "EVIDENCE_INSUFFICIENT" | "FEATURE_NOT_IMPLEMENTED" | "GONE" | "INFERENCE_POLICY_VIOLATION" | "INTERNAL_ERROR" | "MODEL_CAPABILITY_MISSING" | "MODEL_CHANGED" | "MODEL_UNAVAILABLE" | "NOT_FOUND" | "PERMISSION_DENIED" | "PROVIDER_UNAVAILABLE" | "RATE_LIMITED" | "UNAUTHENTICATED" | "VALIDATION_FAILED";
/** Persisted event schema versions (old v1 replay and new v2 contract). */
export type EventSchemaVersion = 1 | 2;
export type HttpSchemaVersion = 2;
