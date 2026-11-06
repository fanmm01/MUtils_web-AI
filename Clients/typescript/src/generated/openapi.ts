/**
 * GENERATED from docs/openapi.json by Clients/typescript/scripts/generate-types.mjs.
 * Do not edit. Regenerate with `npm run gen:types -w @qa/client`;
 * `npm run typecheck` fails while this file is stale.
 */

export interface paths {
    "/healthz": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_healthz_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/readyz": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Readiness */
        get: operations["readiness_readyz_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/answers/{answer_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Answer */
        get: operations["get_answer_v1_answers__answer_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/answers/{answer_id}/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Cancel Answer */
        post: operations["cancel_answer_v1_answers__answer_id__cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/answers/{answer_id}/citations/{citation_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Citation */
        get: operations["get_citation_v1_answers__answer_id__citations__citation_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/answers/{answer_id}/events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Answer Events */
        get: operations["answer_events_v1_answers__answer_id__events_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/answers/{answer_id}/feedback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Feedback */
        post: operations["submit_feedback_v1_answers__answer_id__feedback_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/ask": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Ask */
        post: operations["ask_v1_ask_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/capabilities": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Capabilities */
        get: operations["capabilities_v1_capabilities_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/documents/{document_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Document */
        get: operations["get_document_v1_documents__document_id__get"];
        put?: never;
        post?: never;
        /** Delete Document */
        delete: operations["delete_document_v1_documents__document_id__delete"];
        options?: never;
        head?: never;
        /** Update Document */
        patch: operations["update_document_v1_documents__document_id__patch"];
        trace?: never;
    };
    "/v1/inference-profiles": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Profiles */
        get: operations["list_profiles_v1_inference_profiles_get"];
        put?: never;
        /** Create Profile */
        post: operations["create_profile_v1_inference_profiles_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/inference-profiles/{profile_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Profile */
        get: operations["get_profile_v1_inference_profiles__profile_id__get"];
        /** Update Profile */
        put: operations["update_profile_v1_inference_profiles__profile_id__put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/inference-profiles/{profile_id}/disable": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Disable Profile */
        post: operations["disable_profile_v1_inference_profiles__profile_id__disable_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/issues": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Issues */
        get: operations["list_issues_v1_issues_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/issues/{issue_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Issue */
        get: operations["get_issue_v1_issues__issue_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Resolve Issue */
        patch: operations["resolve_issue_v1_issues__issue_id__patch"];
        trace?: never;
    };
    "/v1/issues/{issue_id}/retest": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Retest Issue */
        post: operations["retest_issue_v1_issues__issue_id__retest_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/jobs/{job_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Job */
        get: operations["get_job_v1_jobs__job_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/jobs/{job_id}/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Cancel Job
         * @description Request cancellation without lying about work that is still running.
         *
         *     A queued job has not written anything, so it becomes ``cancelled`` at once.
         *     A running job only enters ``cancel_requested``; the worker confirms the
         *     terminal state at its next safe point, because it may hold a transaction
         *     mid-write. Claiming ``cancelled`` here could hide a snapshot that later
         *     becomes active.
         */
        post: operations["cancel_job_v1_jobs__job_id__cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/jobs/{job_id}/events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Job Events
         * @description Persisted event replay as JSON.
         *
         *     The streaming form is P3; until then a client can poll this endpoint and get
         *     the same persisted events with stable sequence numbers.
         */
        get: operations["job_events_v1_jobs__job_id__events_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/kbs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Kbs */
        get: operations["list_kbs_v1_kbs_get"];
        put?: never;
        /** Create Kb */
        post: operations["create_kb_v1_kbs_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/kbs/{kb_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Kb */
        get: operations["get_kb_v1_kbs__kb_id__get"];
        put?: never;
        post?: never;
        /** Delete Kb */
        delete: operations["delete_kb_v1_kbs__kb_id__delete"];
        options?: never;
        head?: never;
        /** Update Kb */
        patch: operations["update_kb_v1_kbs__kb_id__patch"];
        trace?: never;
    };
    "/v1/kbs/{kb_id}/documents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Documents */
        get: operations["list_documents_v1_kbs__kb_id__documents_get"];
        put?: never;
        /** Create Document */
        post: operations["create_document_v1_kbs__kb_id__documents_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/kbs/{kb_id}/imports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Import Documents */
        post: operations["import_documents_v1_kbs__kb_id__imports_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/kbs/{kb_id}/imports/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Preview Import */
        post: operations["preview_import_v1_kbs__kb_id__imports_preview_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/kbs/{kb_id}/imports/{preview_id}/resolve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Resolve Import Conflicts
         * @description P3 Gate wire contract only; the A1 atomic resolver is not implemented.
         */
        post: operations["resolve_import_conflicts_v1_kbs__kb_id__imports__preview_id__resolve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/kbs/{kb_id}/publish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Publish Kb */
        post: operations["publish_kb_v1_kbs__kb_id__publish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/kbs/{kb_id}/qa-pairs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Qa */
        get: operations["list_qa_v1_kbs__kb_id__qa_pairs_get"];
        put?: never;
        /** Create Qa */
        post: operations["create_qa_v1_kbs__kb_id__qa_pairs_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/kbs/{kb_id}/rollback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Rollback Version */
        post: operations["rollback_version_v1_kbs__kb_id__rollback_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/kbs/{kb_id}/sources": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Sources */
        get: operations["list_sources_v1_kbs__kb_id__sources_get"];
        put?: never;
        /** Create Source */
        post: operations["create_source_v1_kbs__kb_id__sources_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/kbs/{kb_id}/version-diff": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Diff Versions */
        get: operations["diff_versions_v1_kbs__kb_id__version_diff_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/kbs/{kb_id}/versions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Versions */
        get: operations["list_versions_v1_kbs__kb_id__versions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/knowledge-catalog": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Retrievable Kbs */
        get: operations["list_retrievable_kbs_v1_knowledge_catalog_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/knowledge-selection/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Preview Selection */
        post: operations["preview_selection_v1_knowledge_selection_preview_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/model-installs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirm Install */
        post: operations["confirm_install_v1_model_installs_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/model-installs/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Preview Install */
        post: operations["preview_install_v1_model_installs_preview_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/models": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Models */
        get: operations["list_models_v1_models_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/models/capabilities": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Model Capabilities */
        get: operations["model_capabilities_v1_models_capabilities_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/models/discovery": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Discover Runtimes */
        post: operations["discover_runtimes_v1_models_discovery_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/models/runtimes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Runtimes */
        get: operations["list_runtimes_v1_models_runtimes_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/models/{model_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Model */
        get: operations["get_model_v1_models__model_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/models/{model_id}/verifications": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Verify Model */
        post: operations["verify_model_v1_models__model_id__verifications_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/qa-pairs/{qa_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Qa */
        get: operations["get_qa_v1_qa_pairs__qa_id__get"];
        put?: never;
        post?: never;
        /** Delete Qa */
        delete: operations["delete_qa_v1_qa_pairs__qa_id__delete"];
        options?: never;
        head?: never;
        /** Update Qa */
        patch: operations["update_qa_v1_qa_pairs__qa_id__patch"];
        trace?: never;
    };
    "/v1/search": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Search */
        post: operations["search_v1_search_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Session */
        post: operations["create_session_v1_sessions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/sessions/{session_id}/answers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Answer */
        post: operations["submit_answer_v1_sessions__session_id__answers_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/sessions/{session_id}/history": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** History */
        get: operations["history_v1_sessions__session_id__history_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/sessions/{session_id}/inference": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Session Inference */
        get: operations["get_session_inference_v1_sessions__session_id__inference_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Session Inference */
        patch: operations["update_session_inference_v1_sessions__session_id__inference_patch"];
        trace?: never;
    };
    "/v1/sessions/{session_id}/selection": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Session Selection */
        get: operations["get_session_selection_v1_sessions__session_id__selection_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Session Selection */
        patch: operations["update_session_selection_v1_sessions__session_id__selection_patch"];
        trace?: never;
    };
    "/v1/source-roots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Roots */
        get: operations["list_roots_v1_source_roots_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/source-roots/{root_id}/scan": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Scan Source */
        post: operations["scan_source_v1_source_roots__root_id__scan_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/sources/{source_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Source */
        get: operations["get_source_v1_sources__source_id__get"];
        put?: never;
        post?: never;
        /** Delete Source */
        delete: operations["delete_source_v1_sources__source_id__delete"];
        options?: never;
        head?: never;
        /** Update Source */
        patch: operations["update_source_v1_sources__source_id__patch"];
        trace?: never;
    };
    "/v1/sources/{source_id}/sync": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Sync Source */
        post: operations["sync_source_v1_sources__source_id__sync_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/uploads": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Begin Upload */
        post: operations["begin_upload_v1_uploads_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/uploads/{batch_id}/complete": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Complete Upload */
        post: operations["complete_upload_v1_uploads__batch_id__complete_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/uploads/{batch_id}/files": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Upload File */
        put: operations["upload_file_v1_uploads__batch_id__files_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/versions/{version_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Version */
        get: operations["get_version_v1_versions__version_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/versions/{version_id}/publish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Publish Version */
        post: operations["publish_version_v1_versions__version_id__publish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/widget/tickets": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Issue Ticket */
        post: operations["issue_ticket_v1_widget_tickets_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** APIErrorResponse */
        APIErrorResponse: {
            error: components["schemas"]["ErrorBody"];
            /** Request Id */
            request_id: string;
        };
        /** Answer */
        Answer: {
            /** Answer Id */
            answer_id: string;
            binding?: components["schemas"]["InferenceBinding"] | null;
            /** Citations */
            citations?: components["schemas"]["Citation"][];
            /** Completed At */
            completed_at?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            effective_inference?: components["schemas"]["EffectiveInference"] | null;
            effective_selection?: components["schemas"]["EffectiveSelection"] | null;
            /** Error Code */
            error_code?: string | null;
            /** Question */
            question: string;
            /** Refusal Reason */
            refusal_reason?: string | null;
            /** Requested Selection */
            requested_selection?: (components["schemas"]["ExplicitSelection"] | components["schemas"]["AutoSelection"]) | null;
            resolved_scope?: components["schemas"]["ResolvedScope"] | null;
            selection_result?: components["schemas"]["SelectionResult"] | null;
            /** Session Id */
            session_id: string;
            /** @default pending */
            status?: components["schemas"]["AnswerTerminal"];
            /**
             * Text
             * @default
             */
            text?: string;
            /** Used Kb Ids */
            used_kb_ids?: string[];
        };
        /** AnswerHandle */
        AnswerHandle: {
            /** Answer Id */
            answer_id: string;
            /** Events Url */
            events_url: string;
            /** Poll Url */
            poll_url: string;
            /**
             * Retry After Ms
             * @default 500
             */
            retry_after_ms?: number;
            /** Session Id */
            session_id: string;
            /** @default pending */
            status?: components["schemas"]["AnswerTerminal"];
        };
        /**
         * AnswerTerminal
         * @enum {string}
         */
        AnswerTerminal: "pending" | "completed" | "refused" | "failed" | "cancelled";
        /** AskRequest */
        AskRequest: {
            inference?: components["schemas"]["InferenceSelection"] | null;
            /** Question */
            question: string;
            /** Selection */
            selection?: (components["schemas"]["ExplicitSelection"] | components["schemas"]["AutoSelection"]) | null;
            /** Session Id */
            session_id?: string | null;
            /**
             * Wait Seconds
             * @default 30
             */
            wait_seconds?: number;
        };
        /**
         * AskResponse
         * @description Either a finished answer or a handle with polling instructions.
         */
        AskResponse: {
            answer?: components["schemas"]["Answer"] | null;
            handle?: components["schemas"]["AnswerHandle"] | null;
        };
        /** AutoSelection */
        AutoSelection: {
            /** Candidate Kb Ids */
            candidate_kb_ids?: string[] | null;
            /** Max Kbs */
            max_kbs?: number | null;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            mode: "auto";
        };
        /** BlobRef */
        BlobRef: {
            /** Digest */
            digest: string;
            /**
             * Media Type
             * @default application/octet-stream
             */
            media_type?: string;
            /** Size */
            size: number;
        };
        /**
         * CandidateEmbedder
         * @description One candidate snapshot is pinned to its exact embedding role and profile.
         */
        CandidateEmbedder: {
            binding: components["schemas"]["RoleBinding"];
            /** Fingerprint */
            fingerprint: string;
            /** Kb Id */
            kb_id: string;
            /** Version Id */
            version_id: string;
        };
        /** CapabilitiesBody */
        CapabilitiesBody: {
            /** Implemented */
            implemented: string[];
            /** Mode */
            mode: string;
            /**
             * Schema Version
             * @default 2
             */
            schema_version?: number;
            /** Selection Limits */
            selection_limits: {
                [key: string]: number;
            };
            /** Unimplemented */
            unimplemented: string[];
        };
        /** ChangeReceipt */
        ChangeReceipt: {
            /** Document Id */
            document_id?: string | null;
            /** Job Id */
            job_id?: string | null;
            /** Kb Id */
            kb_id: string;
            /**
             * Requires Publish
             * @default true
             */
            requires_publish?: boolean;
            /** Version Id */
            version_id?: string | null;
        };
        /** Citation */
        Citation: {
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
            locator?: components["schemas"]["Locator"] | null;
            /** Quote */
            quote: string;
            /** Revision Id */
            revision_id: string;
            /** Version Id */
            version_id: string;
        };
        /** CitationDetail */
        CitationDetail: {
            citation: components["schemas"]["Citation"];
            /** Document Title */
            document_title: string;
            /** Kb Name */
            kb_name: string;
        };
        /**
         * ContentKind
         * @enum {string}
         */
        ContentKind: "document" | "qa_pair";
        /** CreateKB */
        CreateKB: {
            /**
             * Description
             * @default
             */
            description?: string;
            /** Domain Tags */
            domain_tags?: string[];
            /** Name */
            name: string;
            /** Routing Examples */
            routing_examples?: string[];
        };
        /** CreateSession */
        CreateSession: {
            inference?: components["schemas"]["InferenceSelection"] | null;
            /** Selection */
            selection?: (components["schemas"]["ExplicitSelection"] | components["schemas"]["AutoSelection"]) | null;
        };
        /** DiscoveryReport */
        DiscoveryReport: {
            /** Host Id */
            host_id: string;
            /**
             * Observed At
             * Format: date-time
             */
            observed_at?: string;
            /** Report Id */
            report_id: string;
            /** Runtimes */
            runtimes?: components["schemas"]["RuntimeStatus"][];
        };
        /**
         * DiscoveryRequest
         * @description Only allow-listed runtime IDs; no URL, path, credential or proxy fields.
         */
        DiscoveryRequest: {
            /** Target Ids */
            target_ids?: string[];
        };
        /** Document */
        Document: {
            /** @default document */
            content_kind?: components["schemas"]["ContentKind"];
            /**
             * Deleted
             * @default false
             */
            deleted?: boolean;
            /** Document Id */
            document_id: string;
            /** Kb Id */
            kb_id: string;
            /** Latest Revision Id */
            latest_revision_id: string;
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at?: string;
        };
        /** DocumentDetail */
        DocumentDetail: {
            document: components["schemas"]["Document"];
            revision: components["schemas"]["Revision"];
        };
        /** EffectiveInference */
        EffectiveInference: {
            /** Profile Revision */
            profile_revision?: string | null;
            selection: components["schemas"]["InferenceSelection"];
            /**
             * Source
             * @default default
             * @enum {string}
             */
            source?: "request" | "session" | "default";
        };
        /** EffectiveSelection */
        EffectiveSelection: {
            /** Selection */
            selection: components["schemas"]["ExplicitSelection"] | components["schemas"]["AutoSelection"];
            /**
             * Source
             * @default default
             * @enum {string}
             */
            source?: "request" | "session" | "default";
        };
        /**
         * EmbeddingProfile
         * @description Full snapshot fingerprint; only a resolved identity is usable for vectors.
         */
        EmbeddingProfile: {
            /** Digest */
            digest?: string | null;
            /** Dimension */
            dimension: number;
            identity?: components["schemas"]["ModelIdentity"] | null;
            /** Model Id */
            model_id: string;
            /**
             * Normalized
             * @default true
             */
            normalized?: boolean;
            /**
             * Preprocessing
             * @default none
             */
            preprocessing?: string;
            /** Profile Key */
            profile_key: string;
            /**
             * Truncation Policy
             * @default reject
             * @enum {string}
             */
            truncation_policy?: "reject" | "truncate";
            /** Truncation Tokens */
            truncation_tokens?: number | null;
        };
        /** ErrorBody */
        ErrorBody: {
            code: components["schemas"]["ErrorCode"];
            /** Details */
            details?: components["schemas"]["ErrorDetail"][];
            /** Message */
            message: string;
        };
        /**
         * ErrorCode
         * @enum {string}
         */
        ErrorCode: "VALIDATION_FAILED" | "UNAUTHENTICATED" | "PERMISSION_DENIED" | "NOT_FOUND" | "CONFLICT" | "GONE" | "RATE_LIMITED" | "FEATURE_NOT_IMPLEMENTED" | "PROVIDER_UNAVAILABLE" | "EVIDENCE_INSUFFICIENT" | "MODEL_UNAVAILABLE" | "MODEL_CHANGED" | "MODEL_CAPABILITY_MISSING" | "INFERENCE_POLICY_VIOLATION" | "INTERNAL_ERROR";
        /** ErrorDetail */
        ErrorDetail: {
            /**
             * Field
             * @default null
             */
            field?: string | null;
            /** Reason */
            reason: string;
        };
        /**
         * ExecutionLocation
         * @enum {string}
         */
        ExecutionLocation: "local" | "configured_remote";
        /** ExplicitSelection */
        ExplicitSelection: {
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            mode: "explicit";
            /** Targets */
            targets: components["schemas"]["KBTarget"][];
        };
        /** Feedback */
        Feedback: {
            /** Answer Id */
            answer_id: string;
            /**
             * Comment
             * @default
             */
            comment?: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            /** Feedback Id */
            feedback_id: string;
            /** Principal Id */
            principal_id: string;
            /**
             * Rating
             * @enum {string}
             */
            rating: "like" | "dislike";
        };
        /** FeedbackInput */
        FeedbackInput: {
            /**
             * Comment
             * @default
             */
            comment?: string;
            /**
             * Rating
             * @enum {string}
             */
            rating: "like" | "dislike";
        };
        /**
         * ForkDocument
         * @description Fork the manual copy; server allocates the new document ID.
         */
        ForkDocument: {
            /** Document Id */
            document_id: string;
            /** Incoming Source Digest */
            incoming_source_digest?: string | null;
            /** Manual Revision Id */
            manual_revision_id: string;
            /** Relative Path */
            relative_path: string;
            /** Source Baseline Digest */
            source_baseline_digest: string;
            /** Source Baseline Revision Id */
            source_baseline_revision_id: string;
            /** Source Id */
            source_id: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            strategy: "fork_document";
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** Health */
        Health: {
            /** Mode */
            mode: string;
            /**
             * Schema Version
             * @default 2
             */
            schema_version?: number;
            /** Status */
            status: string;
        };
        /**
         * HistoryPolicy
         * @enum {string}
         */
        HistoryPolicy: "reset_on_scope_change" | "carry_user_questions";
        /**
         * Hit
         * @description One retrieved chunk; provenance is always per-knowledge-base.
         */
        Hit: {
            /** Chunk Id */
            chunk_id: string;
            /** Kb Id */
            kb_id: string;
            locator?: components["schemas"]["Locator"] | null;
            /** Score */
            score: number;
            /** Text */
            text: string;
            /** Version Id */
            version_id: string;
        };
        /**
         * ImportConflict
         * @description Server-observed identity of one source/manual revision conflict.
         */
        ImportConflict: {
            /** Document Id */
            document_id: string;
            /** Incoming Source Digest */
            incoming_source_digest?: string | null;
            /** Manual Revision Id */
            manual_revision_id: string;
            /** Relative Path */
            relative_path: string;
            /** Source Baseline Digest */
            source_baseline_digest: string;
            /** Source Baseline Revision Id */
            source_baseline_revision_id: string;
            /** Source Id */
            source_id: string;
        };
        /** ImportPreview */
        ImportPreview: {
            /** Added */
            added?: string[];
            /** Conflict Details */
            conflict_details?: components["schemas"]["ImportConflict"][];
            /** Conflicts */
            conflicts?: string[];
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            /** Kb Id */
            kb_id: string;
            /** Modified */
            modified?: string[];
            /** Preview Hash */
            preview_hash: string;
            /** Preview Id */
            preview_id: string;
            /** Removed */
            removed?: string[];
        };
        /** ImportPreviewRequest */
        ImportPreviewRequest: {
            /** Kb Id */
            kb_id: string;
            /**
             * Mode
             * @default merge
             * @enum {string}
             */
            mode?: "merge" | "mirror";
            selection?: components["schemas"]["Selection"];
            /** Source Id */
            source_id: string;
        };
        /** ImportRequest */
        ImportRequest: {
            /** Expected Preview Hash */
            expected_preview_hash: string;
            /** Kb Id */
            kb_id: string;
            /**
             * Mode
             * @default merge
             * @enum {string}
             */
            mode?: "merge" | "mirror";
            /** Resolution Id */
            resolution_id?: string | null;
            selection?: components["schemas"]["Selection"];
            /** Source Id */
            source_id: string;
        };
        /**
         * ImportResolution
         * @description An immutable decision reference, not proof that apply already ran.
         */
        ImportResolution: {
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            /** Decisions */
            decisions: (components["schemas"]["KeepManual"] | components["schemas"]["UseSource"] | components["schemas"]["ForkDocument"])[];
            /** Expected Active Version Id */
            expected_active_version_id?: string | null;
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Kb Id */
            kb_id: string;
            /** Preview Hash */
            preview_hash: string;
            /** Preview Id */
            preview_id: string;
            /** Principal Id */
            principal_id: string;
            /** Request Hash */
            request_hash: string;
            /** Resolution Id */
            resolution_id: string;
            /** Source Id */
            source_id: string;
        };
        /** InferenceBinding */
        InferenceBinding: {
            /** Binding Id */
            binding_id: string;
            /** Candidate Embedders */
            candidate_embedders?: components["schemas"]["CandidateEmbedder"][];
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            policy: components["schemas"]["InferencePolicy"];
            /** Profile Revision */
            profile_revision?: string | null;
            /** Roles */
            roles?: components["schemas"]["RoleBinding"][];
        };
        /**
         * InferencePolicy
         * @enum {string}
         */
        InferencePolicy: "local_only" | "configured";
        /**
         * InferenceProfile
         * @description Immutable profile revision; editing appends a new revision.
         */
        InferenceProfile: {
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            /** @default local_only */
            policy_default?: components["schemas"]["InferencePolicy"];
            /** Profile Id */
            profile_id: string;
            /** Revision */
            revision: string;
            /**
             * Rewriter Enabled
             * @default false
             */
            rewriter_enabled?: boolean;
            /** Roles */
            roles?: {
                [key: string]: components["schemas"]["ModelIdentity"];
            };
        };
        /** InferenceSelection */
        InferenceSelection: {
            /** @default local_only */
            policy?: components["schemas"]["InferencePolicy"];
            /** Profile Id */
            profile_id?: string | null;
        };
        /** InstallConfirmation */
        InstallConfirmation: {
            /**
             * Confirmed
             * @constant
             */
            confirmed: true;
            /** Preview Hash */
            preview_hash: string;
            /** Preview Id */
            preview_id: string;
        };
        /** InstallPreview */
        InstallPreview: {
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            expected_identity?: components["schemas"]["ModelIdentity"] | null;
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /**
             * Identity Status
             * @default unresolved
             * @enum {string}
             */
            identity_status?: "resolved" | "unresolved";
            /** License Url */
            license_url?: string | null;
            /** Missing Layers */
            missing_layers?: number | null;
            /** Model Ref */
            model_ref: string;
            /** Preview Hash */
            preview_hash: string;
            /** Preview Id */
            preview_id: string;
            /** Principal Id */
            principal_id: string;
            /** Size Bytes */
            size_bytes?: number | null;
            /** Target Cache */
            target_cache?: string | null;
            /** Target Id */
            target_id: string;
            target_location: components["schemas"]["ExecutionLocation"];
            /** Unknown Fields */
            unknown_fields?: string[];
        };
        /** InstallRequest */
        InstallRequest: {
            /** Model Ref */
            model_ref: string;
            /** Target Id */
            target_id: string;
        };
        /** Issue */
        Issue: {
            /** Answer Id */
            answer_id: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            /** Issue Id */
            issue_id: string;
            /** Linked Revision Id */
            linked_revision_id?: string | null;
            /** Linked Version Id */
            linked_version_id?: string | null;
            /** Question */
            question: string;
            /** Revision */
            revision: number;
            /** @default open */
            status?: components["schemas"]["IssueStatus"];
        };
        /** IssueResolution */
        IssueResolution: {
            /**
             * Note
             * @default
             */
            note?: string;
            /**
             * Status
             * @default resolved
             * @constant
             */
            status?: "resolved";
        };
        /**
         * IssueStatus
         * @enum {string}
         */
        IssueStatus: "open" | "linked" | "resolved";
        /** Job */
        Job: {
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            /** Diagnostics */
            diagnostics?: components["schemas"]["JobFileDiagnostic"][];
            /** Error Code */
            error_code?: string | null;
            /** Idempotency Key */
            idempotency_key?: string | null;
            /** Job Id */
            job_id: string;
            kind: components["schemas"]["JobKind"];
            /** Lease Until */
            lease_until?: string | null;
            /**
             * Progress
             * @default 0
             */
            progress?: number;
            /** Result Version Id */
            result_version_id?: string | null;
            /** Revision */
            revision: number;
            /** @default queued */
            state?: components["schemas"]["JobState"];
            /** Worker Id */
            worker_id?: string | null;
        };
        /** JobEvent */
        JobEvent: {
            /** Bytes Downloaded */
            bytes_downloaded?: number | null;
            /** Diagnostic */
            diagnostic?: string | null;
            event: components["schemas"]["JobEventType"];
            /** Job Id */
            job_id: string;
            /** Phase */
            phase?: string | null;
            /** Progress */
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
            /** Total Bytes */
            total_bytes?: number | null;
        };
        /**
         * JobEventEnvelope
         * @description P2 JSON replay; distinct from the future SSE representation.
         */
        JobEventEnvelope: {
            data: components["schemas"]["JobEvent"];
            /** Event */
            event: string;
            /** Id */
            id: number;
        };
        /**
         * JobEventType
         * @enum {string}
         */
        JobEventType: "job.accepted" | "job.progress" | "job.completed" | "job.failed" | "job.cancelled";
        /** JobFileDiagnostic */
        JobFileDiagnostic: {
            /**
             * Message
             * @default
             */
            message?: string;
            /** Relative Path */
            relative_path: string;
            /**
             * Status
             * @enum {string}
             */
            status: "ok" | "skipped" | "failed";
        };
        /**
         * JobKind
         * @enum {string}
         */
        JobKind: "import" | "model_install" | "model_verify";
        /**
         * JobState
         * @enum {string}
         */
        JobState: "queued" | "running" | "cancel_requested" | "succeeded" | "failed" | "cancelled" | "outcome_unknown";
        /**
         * KBDescriptor
         * @description Routing metadata an authorized caller may see (no counts, no paths).
         */
        KBDescriptor: {
            /**
             * Description
             * @default
             */
            description?: string;
            /** Domain Tags */
            domain_tags?: string[];
            /** Kb Id */
            kb_id: string;
            /** Name */
            name: string;
            /** Routing Examples */
            routing_examples?: string[];
            /** Version Id */
            version_id?: string | null;
        };
        /**
         * KBTarget
         * @description One knowledge base pinned to an optional immutable version.
         */
        KBTarget: {
            /** Kb Id */
            kb_id: string;
            /** Version Id */
            version_id?: string | null;
        };
        /**
         * KeepManual
         * @description Retain the manual revision and record the source divergence.
         */
        KeepManual: {
            /** Document Id */
            document_id: string;
            /** Incoming Source Digest */
            incoming_source_digest?: string | null;
            /** Manual Revision Id */
            manual_revision_id: string;
            /** Relative Path */
            relative_path: string;
            /** Source Baseline Digest */
            source_baseline_digest: string;
            /** Source Baseline Revision Id */
            source_baseline_revision_id: string;
            /** Source Id */
            source_id: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            strategy: "keep_manual";
        };
        /** KnowledgeBase */
        KnowledgeBase: {
            /** Active Version Id */
            active_version_id?: string | null;
            /**
             * Description
             * @default
             */
            description?: string;
            /** Domain Tags */
            domain_tags?: string[];
            /** Etag */
            etag: string;
            /** Kb Id */
            kb_id: string;
            /** Name */
            name: string;
            /** Routing Examples */
            routing_examples?: string[];
            /**
             * Updated At
             * Format: date-time
             */
            updated_at?: string;
        };
        /**
         * Locator
         * @description Traceable original position. Never invent a page number a format lacks.
         */
        Locator: {
            /** Cell Range */
            cell_range?: string | null;
            /** End Line */
            end_line?: number | null;
            /** Heading */
            heading?: string | null;
            kind: components["schemas"]["LocatorKind"];
            /** Page */
            page?: number | null;
            /** Paragraph */
            paragraph?: number | null;
            /** Sheet */
            sheet?: string | null;
            /** Start Line */
            start_line?: number | null;
        };
        /**
         * LocatorKind
         * @enum {string}
         */
        LocatorKind: "markdown_lines" | "text_lines" | "word_paragraph" | "word_table" | "excel_range" | "pdf_page" | "qa_fields";
        /** ManifestFile */
        ManifestFile: {
            /** Digest */
            digest: string;
            /** Relative Path */
            relative_path: string;
            /** Size */
            size: number;
        };
        /** ModelCapabilities */
        ModelCapabilities: {
            /**
             * Install Requires Confirmation
             * @default true
             */
            install_requires_confirmation?: boolean;
            /**
             * Mode
             * @default scaffold
             * @enum {string}
             */
            mode?: "scaffold" | "operational";
            /** Runtimes */
            runtimes?: components["schemas"]["RuntimeCapability"][];
        };
        /**
         * ModelIdentity
         * @description An exact tag is an alias; only a resolved digest pins model bytes.
         *
         *     An adapter must compare this identity with a fresh runtime observation before
         *     every call. A mutable tag alone cannot promise reproducible results.
         */
        ModelIdentity: {
            /** Digest */
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
            /** Runtime Target Id */
            runtime_target_id?: string | null;
        };
        /** ModelRef */
        ModelRef: {
            /** Digest */
            digest?: string | null;
            /** @default unknown */
            downloaded?: components["schemas"]["Presence"];
            /** Exact Tag */
            exact_tag: string;
            /** Family */
            family?: string | null;
            /**
             * Identity Status
             * @default unresolved
             * @enum {string}
             */
            identity_status?: "resolved" | "unresolved";
            /** @default unknown */
            installed?: components["schemas"]["Presence"];
            /** @default unknown */
            loaded?: components["schemas"]["Presence"];
            /** Model Id */
            model_id: string;
            /** Parameters */
            parameters?: string | null;
            /** Quantization */
            quantization?: string | null;
            /** Runtime Target Id */
            runtime_target_id: string;
            /** Size Bytes */
            size_bytes?: number | null;
            /** Verified Roles */
            verified_roles?: components["schemas"]["ModelRole"][];
        };
        /**
         * ModelRole
         * @enum {string}
         */
        ModelRole: "generator" | "rewriter" | "support_checker" | "reranker" | "embedder" | "token_counter";
        /** Page[Document] */
        Page_Document_: {
            /** Items */
            items?: components["schemas"]["Document"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** Page[KBDescriptor] */
        Page_KBDescriptor_: {
            /** Items */
            items?: components["schemas"]["KBDescriptor"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** Page[KnowledgeBase] */
        Page_KnowledgeBase_: {
            /** Items */
            items?: components["schemas"]["KnowledgeBase"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** Page[ModelRef] */
        Page_ModelRef_: {
            /** Items */
            items?: components["schemas"]["ModelRef"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** Page[ProfileSummary] */
        Page_ProfileSummary_: {
            /** Items */
            items?: components["schemas"]["ProfileSummary"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** Page[QAPair] */
        Page_QAPair_: {
            /** Items */
            items?: components["schemas"]["QAPair"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /**
         * PinnedKBTarget
         * @description An authorized KB resolved to its immutable version before retrieval.
         */
        PinnedKBTarget: {
            /** Kb Id */
            kb_id: string;
            /** Version Id */
            version_id: string;
        };
        /**
         * Presence
         * @description Four independent facts; ``unknown`` is a first-class answer.
         * @enum {string}
         */
        Presence: "present" | "absent" | "unknown";
        /** ProfileSummary */
        ProfileSummary: {
            policy_default: components["schemas"]["InferencePolicy"];
            /** Profile Id */
            profile_id: string;
            /** Revision */
            revision: string;
            /** Role Names */
            role_names?: components["schemas"]["ModelRole"][];
        };
        /** PublishRequest */
        PublishRequest: {
            /** Expected Active Version Id */
            expected_active_version_id?: string | null;
        };
        /** PutDocument */
        PutDocument: {
            /** Expected Revision Id */
            expected_revision_id?: string | null;
            /** Kb Id */
            kb_id: string;
            /** Relative Path */
            relative_path?: string | null;
            /**
             * Text
             * @default
             */
            text?: string;
            /** Title */
            title: string;
        };
        /** PutInferenceProfile */
        PutInferenceProfile: {
            /** Expected Revision */
            expected_revision?: string | null;
            /** @default local_only */
            policy_default?: components["schemas"]["InferencePolicy"];
            /** Profile Id */
            profile_id?: string | null;
            /**
             * Rewriter Enabled
             * @default false
             */
            rewriter_enabled?: boolean;
            /** Roles */
            roles?: {
                [key: string]: components["schemas"]["ModelIdentity"];
            };
        };
        /** PutQA */
        PutQA: {
            /** Answer */
            answer: string;
            /** Expected Revision Id */
            expected_revision_id?: string | null;
            /** Kb Id */
            kb_id: string;
            /** Question */
            question: string;
        };
        /** QAPair */
        QAPair: {
            /** Answer */
            answer: string;
            /**
             * Deleted
             * @default false
             */
            deleted?: boolean;
            /** Kb Id */
            kb_id: string;
            /** Qa Id */
            qa_id: string;
            /** Question */
            question: string;
            /** Revision Id */
            revision_id: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at?: string;
        };
        /** Readiness */
        Readiness: {
            /** Answer Roles Ready */
            answer_roles_ready?: boolean | null;
            /** Management Api Ready */
            management_api_ready?: boolean | null;
            /** Mode */
            mode: string;
            /** Ready */
            ready: boolean;
            /** Reason */
            reason: string;
            /** Retrieval Roles Ready */
            retrieval_roles_ready?: boolean | null;
        };
        /** ResolveImportConflicts */
        ResolveImportConflicts: {
            /** Decisions */
            decisions: (components["schemas"]["KeepManual"] | components["schemas"]["UseSource"] | components["schemas"]["ForkDocument"])[];
            /** Expected Active Version Id */
            expected_active_version_id: string | null;
            /** Expected Preview Hash */
            expected_preview_hash: string;
            /** Kb Id */
            kb_id: string;
            /** Preview Id */
            preview_id: string;
            /** Source Id */
            source_id: string;
        };
        /** ResolvedScope */
        ResolvedScope: {
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
            targets: components["schemas"]["PinnedKBTarget"][];
        };
        /** RetestRequest */
        RetestRequest: {
            inference?: components["schemas"]["InferenceSelection"] | null;
            /** Selection */
            selection?: (components["schemas"]["ExplicitSelection"] | components["schemas"]["AutoSelection"]) | null;
        };
        /** Revision */
        Revision: {
            blob?: components["schemas"]["BlobRef"] | null;
            /** @default document */
            content_kind?: components["schemas"]["ContentKind"];
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            /** Diagnostics */
            diagnostics?: string[];
            /** Document Id */
            document_id: string;
            /**
             * Normalized Text
             * @default
             */
            normalized_text?: string;
            /** Parent Revision Id */
            parent_revision_id?: string | null;
            /** Relative Path */
            relative_path?: string | null;
            /** Revision Id */
            revision_id: string;
            /** Source Id */
            source_id?: string | null;
        };
        /** RoleBinding */
        RoleBinding: {
            /** Budget Tokens */
            budget_tokens?: number | null;
            identity: components["schemas"]["ModelIdentity"];
            /** @default local */
            location?: components["schemas"]["ExecutionLocation"];
            policy: components["schemas"]["InferencePolicy"];
            role: components["schemas"]["ModelRole"];
            /** Runtime Target Id */
            runtime_target_id?: string | null;
            /** Timeout Ms */
            timeout_ms?: number | null;
        };
        /** RollbackRequest */
        RollbackRequest: {
            /** Expected Active Version Id */
            expected_active_version_id?: string | null;
            /** Target Version Id */
            target_version_id: string;
        };
        /** RuntimeCapability */
        RuntimeCapability: {
            kind: components["schemas"]["RuntimeKind"];
            /** @default unknown */
            supports_cancel?: components["schemas"]["Presence"];
            /** @default unknown */
            supports_embed?: components["schemas"]["Presence"];
            /** @default unknown */
            supports_install?: components["schemas"]["Presence"];
            /** @default unknown */
            supports_list?: components["schemas"]["Presence"];
            /** @default unknown */
            supports_resume?: components["schemas"]["Presence"];
            /** @default unknown */
            supports_stream?: components["schemas"]["Presence"];
            /** Verified Versions */
            verified_versions?: string[];
        };
        /** RuntimeEvidence */
        RuntimeEvidence: {
            /** Detail */
            detail: string;
            /** Kind */
            kind: string;
        };
        /**
         * RuntimeKind
         * @enum {string}
         */
        RuntimeKind: "ollama" | "lm_studio" | "llama_cpp";
        /** RuntimeStatus */
        RuntimeStatus: {
            /** Diagnostic */
            diagnostic?: string | null;
            /** Evidence */
            evidence?: components["schemas"]["RuntimeEvidence"][];
            /** @default unknown */
            installed?: components["schemas"]["Presence"];
            kind: components["schemas"]["RuntimeKind"];
            /**
             * Observed At
             * Format: date-time
             */
            observed_at?: string;
            /** @default unknown */
            running?: components["schemas"]["Presence"];
            /** Target Id */
            target_id: string;
            /** Version */
            version?: string | null;
        };
        /** SearchRequest */
        SearchRequest: {
            inference?: components["schemas"]["InferenceSelection"] | null;
            /** Question */
            question: string;
            /** Selection */
            selection?: (components["schemas"]["ExplicitSelection"] | components["schemas"]["AutoSelection"]) | null;
            /**
             * Top K
             * @default 10
             */
            top_k?: number;
        };
        /** SearchResult */
        SearchResult: {
            /** Binding Id */
            binding_id?: string | null;
            /** Hits */
            hits?: components["schemas"]["Hit"][];
            resolved_scope?: components["schemas"]["ResolvedScope"] | null;
            selection_result: components["schemas"]["SelectionResult"];
        };
        /**
         * Selection
         * @description File selection for an import or source scan (not knowledge selection).
         */
        Selection: {
            /** Exclude Globs */
            exclude_globs?: string[];
            /** Include Globs */
            include_globs?: string[];
            /** Relative Paths */
            relative_paths?: string[];
        };
        /** SelectionPreviewRequest */
        SelectionPreviewRequest: {
            inference?: components["schemas"]["InferenceSelection"] | null;
            /** Question */
            question: string;
            /** Selection */
            selection: components["schemas"]["ExplicitSelection"] | components["schemas"]["AutoSelection"];
        };
        /** SelectionResult */
        SelectionResult: {
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
            status: components["schemas"]["SelectionStatus"];
            /** Targets */
            targets?: components["schemas"]["PinnedKBTarget"][];
        };
        /**
         * SelectionStatus
         * @enum {string}
         */
        SelectionStatus: "resolved" | "no_match" | "needs_clarification";
        /** Session */
        Session: {
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            /** @default reset_on_scope_change */
            history_policy?: components["schemas"]["HistoryPolicy"];
            inference: components["schemas"]["InferenceSelection"];
            /** Inference Revision */
            inference_revision: number;
            /** Principal Id */
            principal_id: string;
            /** Scope Revision */
            scope_revision: number;
            /** Selection */
            selection: components["schemas"]["ExplicitSelection"] | components["schemas"]["AutoSelection"];
            /** Session Id */
            session_id: string;
        };
        /** SessionInference */
        SessionInference: {
            inference: components["schemas"]["InferenceSelection"];
            /** Inference Revision */
            inference_revision: number;
            /** Session Id */
            session_id: string;
        };
        /** SessionSelection */
        SessionSelection: {
            /** @default reset_on_scope_change */
            history_policy?: components["schemas"]["HistoryPolicy"];
            /** Scope Revision */
            scope_revision: number;
            /** Selection */
            selection: components["schemas"]["ExplicitSelection"] | components["schemas"]["AutoSelection"];
            /** Session Id */
            session_id: string;
        };
        /** Snapshot */
        Snapshot: {
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            /** Document Revisions */
            document_revisions?: {
                [key: string]: string;
            };
            embedding_fingerprint?: components["schemas"]["EmbeddingProfile"] | null;
            /** Embedding Profile */
            embedding_profile?: string | null;
            /** Indexed File Ids */
            indexed_file_ids?: string[];
            /** Kb Id */
            kb_id: string;
            /** Keyword Index Ref */
            keyword_index_ref?: string | null;
            /** Keyword Profile */
            keyword_profile?: string | null;
            /** Parent Version Id */
            parent_version_id?: string | null;
            /** @default draft */
            state?: components["schemas"]["SnapshotState"];
            /**
             * Vector Index
             * @default absent
             * @enum {string}
             */
            vector_index?: "present" | "absent";
            /** Vector Index Ref */
            vector_index_ref?: string | null;
            /** Version Id */
            version_id: string;
        };
        /**
         * SnapshotState
         * @enum {string}
         */
        SnapshotState: "draft" | "staging" | "ready" | "published" | "failed";
        /** Source */
        Source: {
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            /** Display Name */
            display_name: string;
            /** Kb Id */
            kb_id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "local_root" | "upload";
            /** Revision */
            revision: string;
            /** Root Id */
            root_id?: string | null;
            /** Source Id */
            source_id: string;
        };
        /**
         * SourceManifest
         * @description Server-verified scan result; only a successful full scan can be complete.
         */
        SourceManifest: {
            /** Complete */
            complete: boolean;
            /** Files */
            files?: components["schemas"]["ManifestFile"][];
            /**
             * Scan Scope
             * @enum {string}
             */
            scan_scope: "full" | "partial";
            /**
             * Scan Status
             * @enum {string}
             */
            scan_status: "succeeded" | "failed";
            /**
             * Scanned At
             * Format: date-time
             */
            scanned_at?: string;
            selection?: components["schemas"]["Selection"];
            /** Source Id */
            source_id: string;
        };
        /** SubmitAnswer */
        SubmitAnswer: {
            inference?: components["schemas"]["InferenceSelection"] | null;
            /** Question */
            question: string;
            /** Selection */
            selection?: (components["schemas"]["ExplicitSelection"] | components["schemas"]["AutoSelection"]) | null;
        };
        /** Turn */
        Turn: {
            /** Answer Id */
            answer_id: string;
            /**
             * Answer Text
             * @default
             */
            answer_text?: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at?: string;
            /** Question */
            question: string;
            /** @default completed */
            terminal?: components["schemas"]["AnswerTerminal"];
            /** Turn Id */
            turn_id: string;
        };
        /** UpdateKB */
        UpdateKB: {
            /** Description */
            description?: string | null;
            /** Domain Tags */
            domain_tags?: string[] | null;
            /** Name */
            name?: string | null;
            /** Routing Examples */
            routing_examples?: string[] | null;
        };
        /** UpdateSessionInference */
        UpdateSessionInference: {
            /** Expected Inference Revision */
            expected_inference_revision: number;
            inference: components["schemas"]["InferenceSelection"];
        };
        /** UpdateSessionSelection */
        UpdateSessionSelection: {
            /** Expected Scope Revision */
            expected_scope_revision: number;
            /** @default reset_on_scope_change */
            history_policy?: components["schemas"]["HistoryPolicy"];
            /** Selection */
            selection: components["schemas"]["ExplicitSelection"] | components["schemas"]["AutoSelection"];
        };
        /** UploadBatch */
        UploadBatch: {
            /** Batch Id */
            batch_id: string;
            /** Source Id */
            source_id: string;
        };
        /**
         * UploadManifest
         * @description Untrusted client file claims; these never authorize mirror deletions.
         */
        UploadManifest: {
            /** Files */
            files?: components["schemas"]["ManifestFile"][];
            selection?: components["schemas"]["Selection"];
            /** Source Id */
            source_id: string;
        };
        /**
         * UseSource
         * @description Restore source ownership; keep the previous revision for old citations.
         */
        UseSource: {
            /** Document Id */
            document_id: string;
            /** Incoming Source Digest */
            incoming_source_digest?: string | null;
            /** Manual Revision Id */
            manual_revision_id: string;
            /** Relative Path */
            relative_path: string;
            /** Source Baseline Digest */
            source_baseline_digest: string;
            /** Source Baseline Revision Id */
            source_baseline_revision_id: string;
            /** Source Id */
            source_id: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            strategy: "use_source";
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
        /** VerifyModelRequest */
        VerifyModelRequest: {
            /** Roles */
            roles: components["schemas"]["ModelRole"][];
        };
        /** VersionDiff */
        VersionDiff: {
            /** Added */
            added?: string[];
            /** Left */
            left: string;
            /** Modified */
            modified?: string[];
            /** Removed */
            removed?: string[];
            /** Right */
            right: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type APIErrorResponse = components['schemas']['APIErrorResponse'];
export type Answer = components['schemas']['Answer'];
export type AnswerHandle = components['schemas']['AnswerHandle'];
export type AnswerTerminal = components['schemas']['AnswerTerminal'];
export type AskRequest = components['schemas']['AskRequest'];
export type AskResponse = components['schemas']['AskResponse'];
export type AutoSelection = components['schemas']['AutoSelection'];
export type BlobRef = components['schemas']['BlobRef'];
export type CandidateEmbedder = components['schemas']['CandidateEmbedder'];
export type CapabilitiesBody = components['schemas']['CapabilitiesBody'];
export type ChangeReceipt = components['schemas']['ChangeReceipt'];
export type Citation = components['schemas']['Citation'];
export type CitationDetail = components['schemas']['CitationDetail'];
export type ContentKind = components['schemas']['ContentKind'];
export type CreateKB = components['schemas']['CreateKB'];
export type CreateSession = components['schemas']['CreateSession'];
export type DiscoveryReport = components['schemas']['DiscoveryReport'];
export type DiscoveryRequest = components['schemas']['DiscoveryRequest'];
export type Document = components['schemas']['Document'];
export type DocumentDetail = components['schemas']['DocumentDetail'];
export type EffectiveInference = components['schemas']['EffectiveInference'];
export type EffectiveSelection = components['schemas']['EffectiveSelection'];
export type EmbeddingProfile = components['schemas']['EmbeddingProfile'];
export type ErrorBody = components['schemas']['ErrorBody'];
export type ErrorCode = components['schemas']['ErrorCode'];
export type ErrorDetail = components['schemas']['ErrorDetail'];
export type ExecutionLocation = components['schemas']['ExecutionLocation'];
export type ExplicitSelection = components['schemas']['ExplicitSelection'];
export type Feedback = components['schemas']['Feedback'];
export type FeedbackInput = components['schemas']['FeedbackInput'];
export type ForkDocument = components['schemas']['ForkDocument'];
export type HTTPValidationError = components['schemas']['HTTPValidationError'];
export type Health = components['schemas']['Health'];
export type HistoryPolicy = components['schemas']['HistoryPolicy'];
export type Hit = components['schemas']['Hit'];
export type ImportConflict = components['schemas']['ImportConflict'];
export type ImportPreview = components['schemas']['ImportPreview'];
export type ImportPreviewRequest = components['schemas']['ImportPreviewRequest'];
export type ImportRequest = components['schemas']['ImportRequest'];
export type ImportResolution = components['schemas']['ImportResolution'];
export type InferenceBinding = components['schemas']['InferenceBinding'];
export type InferencePolicy = components['schemas']['InferencePolicy'];
export type InferenceProfile = components['schemas']['InferenceProfile'];
export type InferenceSelection = components['schemas']['InferenceSelection'];
export type InstallConfirmation = components['schemas']['InstallConfirmation'];
export type InstallPreview = components['schemas']['InstallPreview'];
export type InstallRequest = components['schemas']['InstallRequest'];
export type Issue = components['schemas']['Issue'];
export type IssueResolution = components['schemas']['IssueResolution'];
export type IssueStatus = components['schemas']['IssueStatus'];
export type Job = components['schemas']['Job'];
export type JobEvent = components['schemas']['JobEvent'];
export type JobEventEnvelope = components['schemas']['JobEventEnvelope'];
export type JobEventType = components['schemas']['JobEventType'];
export type JobFileDiagnostic = components['schemas']['JobFileDiagnostic'];
export type JobKind = components['schemas']['JobKind'];
export type JobState = components['schemas']['JobState'];
export type KBDescriptor = components['schemas']['KBDescriptor'];
export type KBTarget = components['schemas']['KBTarget'];
export type KeepManual = components['schemas']['KeepManual'];
export type KnowledgeBase = components['schemas']['KnowledgeBase'];
export type Locator = components['schemas']['Locator'];
export type LocatorKind = components['schemas']['LocatorKind'];
export type ManifestFile = components['schemas']['ManifestFile'];
export type ModelCapabilities = components['schemas']['ModelCapabilities'];
export type ModelIdentity = components['schemas']['ModelIdentity'];
export type ModelRef = components['schemas']['ModelRef'];
export type ModelRole = components['schemas']['ModelRole'];
export type Page_Document_ = components['schemas']['Page_Document_'];
export type Page_KBDescriptor_ = components['schemas']['Page_KBDescriptor_'];
export type Page_KnowledgeBase_ = components['schemas']['Page_KnowledgeBase_'];
export type Page_ModelRef_ = components['schemas']['Page_ModelRef_'];
export type Page_ProfileSummary_ = components['schemas']['Page_ProfileSummary_'];
export type Page_QAPair_ = components['schemas']['Page_QAPair_'];
export type PinnedKBTarget = components['schemas']['PinnedKBTarget'];
export type Presence = components['schemas']['Presence'];
export type ProfileSummary = components['schemas']['ProfileSummary'];
export type PublishRequest = components['schemas']['PublishRequest'];
export type PutDocument = components['schemas']['PutDocument'];
export type PutInferenceProfile = components['schemas']['PutInferenceProfile'];
export type PutQA = components['schemas']['PutQA'];
export type QAPair = components['schemas']['QAPair'];
export type Readiness = components['schemas']['Readiness'];
export type ResolveImportConflicts = components['schemas']['ResolveImportConflicts'];
export type ResolvedScope = components['schemas']['ResolvedScope'];
export type RetestRequest = components['schemas']['RetestRequest'];
export type Revision = components['schemas']['Revision'];
export type RoleBinding = components['schemas']['RoleBinding'];
export type RollbackRequest = components['schemas']['RollbackRequest'];
export type RuntimeCapability = components['schemas']['RuntimeCapability'];
export type RuntimeEvidence = components['schemas']['RuntimeEvidence'];
export type RuntimeKind = components['schemas']['RuntimeKind'];
export type RuntimeStatus = components['schemas']['RuntimeStatus'];
export type SearchRequest = components['schemas']['SearchRequest'];
export type SearchResult = components['schemas']['SearchResult'];
export type Selection = components['schemas']['Selection'];
export type SelectionPreviewRequest = components['schemas']['SelectionPreviewRequest'];
export type SelectionResult = components['schemas']['SelectionResult'];
export type SelectionStatus = components['schemas']['SelectionStatus'];
export type Session = components['schemas']['Session'];
export type SessionInference = components['schemas']['SessionInference'];
export type SessionSelection = components['schemas']['SessionSelection'];
export type Snapshot = components['schemas']['Snapshot'];
export type SnapshotState = components['schemas']['SnapshotState'];
export type Source = components['schemas']['Source'];
export type SourceManifest = components['schemas']['SourceManifest'];
export type SubmitAnswer = components['schemas']['SubmitAnswer'];
export type Turn = components['schemas']['Turn'];
export type UpdateKB = components['schemas']['UpdateKB'];
export type UpdateSessionInference = components['schemas']['UpdateSessionInference'];
export type UpdateSessionSelection = components['schemas']['UpdateSessionSelection'];
export type UploadBatch = components['schemas']['UploadBatch'];
export type UploadManifest = components['schemas']['UploadManifest'];
export type UseSource = components['schemas']['UseSource'];
export type ValidationError = components['schemas']['ValidationError'];
export type VerifyModelRequest = components['schemas']['VerifyModelRequest'];
export type VersionDiff = components['schemas']['VersionDiff'];
export type $defs = Record<string, never>;
export interface operations {
    health_healthz_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Health"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    readiness_readyz_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Successful Response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Readiness"];
                };
            };
        };
    };
    get_answer_v1_answers__answer_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                answer_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Answer"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    cancel_answer_v1_answers__answer_id__cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                answer_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Answer"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    get_citation_v1_answers__answer_id__citations__citation_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                answer_id: string;
                citation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CitationDetail"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    answer_events_v1_answers__answer_id__events_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                answer_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Reserved P3 answer SSE; this build returns 501 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                    "text/event-stream": string;
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    submit_feedback_v1_answers__answer_id__feedback_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                answer_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FeedbackInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Feedback"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    ask_v1_ask_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AskRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AskResponse"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    capabilities_v1_capabilities_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CapabilitiesBody"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    get_document_v1_documents__document_id__get: {
        parameters: {
            query?: {
                revision_id?: string | null;
            };
            header?: never;
            path: {
                document_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DocumentDetail"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    delete_document_v1_documents__document_id__delete: {
        parameters: {
            query?: {
                expected_revision_id?: string | null;
            };
            header?: never;
            path: {
                document_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeReceipt"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    update_document_v1_documents__document_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PutDocument"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeReceipt"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    list_profiles_v1_inference_profiles_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_ProfileSummary_"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    create_profile_v1_inference_profiles_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PutInferenceProfile"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InferenceProfile"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    get_profile_v1_inference_profiles__profile_id__get: {
        parameters: {
            query?: {
                revision?: string | null;
            };
            header?: never;
            path: {
                profile_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InferenceProfile"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    update_profile_v1_inference_profiles__profile_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                profile_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PutInferenceProfile"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InferenceProfile"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    disable_profile_v1_inference_profiles__profile_id__disable_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                profile_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PutInferenceProfile"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InferenceProfile"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    list_issues_v1_issues_get: {
        parameters: {
            query?: {
                status?: components["schemas"]["IssueStatus"] | null;
                limit?: number;
                cursor?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Issue"][];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    get_issue_v1_issues__issue_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                issue_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Issue"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    resolve_issue_v1_issues__issue_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                issue_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["IssueResolution"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Issue"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    retest_issue_v1_issues__issue_id__retest_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                issue_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RetestRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AskResponse"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    get_job_v1_jobs__job_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Job"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    cancel_job_v1_jobs__job_id__cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Job"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    job_events_v1_jobs__job_id__events_get: {
        parameters: {
            query?: never;
            header?: {
                "Last-Event-ID"?: string | null;
                Accept?: string | null;
            };
            path: {
                job_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Persisted JSON replay; SSE is not yet implemented */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobEventEnvelope"][];
                    /** @description Reserved for negotiated P3 SSE; currently returns 501 */
                    "text/event-stream": string;
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    list_kbs_v1_kbs_get: {
        parameters: {
            query?: {
                limit?: number;
                cursor?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_KnowledgeBase_"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    create_kb_v1_kbs_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateKB"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["KnowledgeBase"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    get_kb_v1_kbs__kb_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["KnowledgeBase"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    delete_kb_v1_kbs__kb_id__delete: {
        parameters: {
            query?: {
                expected_etag?: string | null;
            };
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    update_kb_v1_kbs__kb_id__patch: {
        parameters: {
            query?: {
                expected_etag?: string | null;
            };
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateKB"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["KnowledgeBase"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    list_documents_v1_kbs__kb_id__documents_get: {
        parameters: {
            query?: {
                limit?: number;
                cursor?: string | null;
            };
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_Document_"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    create_document_v1_kbs__kb_id__documents_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PutDocument"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeReceipt"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    import_documents_v1_kbs__kb_id__imports_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ImportRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeReceipt"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    preview_import_v1_kbs__kb_id__imports_preview_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ImportPreviewRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportPreview"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    resolve_import_conflicts_v1_kbs__kb_id__imports__preview_id__resolve_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path: {
                kb_id: string;
                preview_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ResolveImportConflicts"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportResolution"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    publish_kb_v1_kbs__kb_id__publish_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PublishRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["KnowledgeBase"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    list_qa_v1_kbs__kb_id__qa_pairs_get: {
        parameters: {
            query?: {
                limit?: number;
                cursor?: string | null;
            };
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_QAPair_"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    create_qa_v1_kbs__kb_id__qa_pairs_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PutQA"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeReceipt"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    rollback_version_v1_kbs__kb_id__rollback_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RollbackRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Snapshot"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    list_sources_v1_kbs__kb_id__sources_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Source"][];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    create_source_v1_kbs__kb_id__sources_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Source"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Source"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    diff_versions_v1_kbs__kb_id__version_diff_get: {
        parameters: {
            query: {
                left: string;
                right: string;
            };
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VersionDiff"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    list_versions_v1_kbs__kb_id__versions_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                kb_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Snapshot"][];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    list_retrievable_kbs_v1_knowledge_catalog_get: {
        parameters: {
            query?: {
                search?: string | null;
                limit?: number;
                cursor?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_KBDescriptor_"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    preview_selection_v1_knowledge_selection_preview_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SelectionPreviewRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SelectionResult"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    confirm_install_v1_model_installs_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InstallConfirmation"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Job"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    preview_install_v1_model_installs_preview_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InstallRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InstallPreview"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    list_models_v1_models_get: {
        parameters: {
            query?: {
                runtime_target_id?: string | null;
                role?: components["schemas"]["ModelRole"] | null;
                limit?: number;
                cursor?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_ModelRef_"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    model_capabilities_v1_models_capabilities_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ModelCapabilities"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    discover_runtimes_v1_models_discovery_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DiscoveryRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DiscoveryReport"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    list_runtimes_v1_models_runtimes_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RuntimeStatus"][];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    get_model_v1_models__model_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                model_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ModelRef"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    verify_model_v1_models__model_id__verifications_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path: {
                model_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VerifyModelRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Job"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    get_qa_v1_qa_pairs__qa_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                qa_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["QAPair"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    delete_qa_v1_qa_pairs__qa_id__delete: {
        parameters: {
            query?: {
                expected_revision_id?: string | null;
            };
            header?: never;
            path: {
                qa_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeReceipt"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    update_qa_v1_qa_pairs__qa_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                qa_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PutQA"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeReceipt"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    search_v1_search_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SearchRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SearchResult"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    create_session_v1_sessions_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateSession"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Session"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    submit_answer_v1_sessions__session_id__answers_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SubmitAnswer"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AskResponse"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    history_v1_sessions__session_id__history_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Turn"][];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    get_session_inference_v1_sessions__session_id__inference_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionInference"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    update_session_inference_v1_sessions__session_id__inference_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateSessionInference"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionInference"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    get_session_selection_v1_sessions__session_id__selection_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionSelection"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    update_session_selection_v1_sessions__session_id__selection_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateSessionSelection"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionSelection"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    list_roots_v1_source_roots_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": string[];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    scan_source_v1_source_roots__root_id__scan_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                root_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SourceManifest"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    get_source_v1_sources__source_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                source_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Source"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    delete_source_v1_sources__source_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                source_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    update_source_v1_sources__source_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                source_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Source"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Source"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    sync_source_v1_sources__source_id__sync_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                source_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Selection"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeReceipt"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    begin_upload_v1_uploads_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UploadManifest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UploadBatch"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    complete_upload_v1_uploads__batch_id__complete_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SourceManifest"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    upload_file_v1_uploads__batch_id__files_put: {
        parameters: {
            query: {
                relative_path: string;
            };
            header?: never;
            path: {
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/octet-stream": string;
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    get_version_v1_versions__version_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Snapshot"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    publish_version_v1_versions__version_id__publish_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PublishRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Snapshot"];
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
    issue_ticket_v1_widget_tickets_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Error response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            410: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            501: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
            /** @description Error response */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["APIErrorResponse"];
                };
            };
        };
    };
}
