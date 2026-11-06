-- P2-A1 initial schema.
--
-- Executed only by the explicit migration action (``qa-migrate`` or
-- ``SQLiteStore.migrate``), never on import or API startup. JSON columns hold
-- canonical, versioned contract payloads instead of decompressed ad-hoc text.

CREATE TABLE IF NOT EXISTS schema_meta (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kbs (
    kb_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    domain_tags TEXT NOT NULL DEFAULT '[]',
    routing_examples TEXT NOT NULL DEFAULT '[]',
    active_version_id TEXT,
    etag TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    kb_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    root_id TEXT,
    display_name TEXT NOT NULL DEFAULT '',
    revision TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sources_kb ON sources (kb_id);

-- Baseline manifest used to compute incremental differences. It is written
-- only after a successful import, so a failed scan never becomes the baseline.
CREATE TABLE IF NOT EXISTS source_baselines (
    source_id TEXT PRIMARY KEY,
    manifest TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    kb_id TEXT NOT NULL,
    title TEXT NOT NULL,
    latest_revision_id TEXT NOT NULL,
    content_kind TEXT NOT NULL DEFAULT 'document',
    deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_kb ON documents (kb_id);

CREATE TABLE IF NOT EXISTS revisions (
    revision_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    parent_revision_id TEXT,
    content_kind TEXT NOT NULL DEFAULT 'document',
    source_id TEXT,
    relative_path TEXT,
    blob_digest TEXT,
    blob_size INTEGER,
    blob_media_type TEXT,
    normalized_text TEXT NOT NULL DEFAULT '',
    diagnostics TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_revisions_document ON revisions (document_id);

CREATE TABLE IF NOT EXISTS qa_pairs (
    qa_id TEXT PRIMARY KEY,
    kb_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    revision_id TEXT NOT NULL,
    deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_qa_pairs_kb ON qa_pairs (kb_id);

CREATE TABLE IF NOT EXISTS snapshots (
    version_id TEXT PRIMARY KEY,
    kb_id TEXT NOT NULL,
    parent_version_id TEXT,
    state TEXT NOT NULL,
    indexed_file_ids TEXT NOT NULL DEFAULT '[]',
    document_revisions TEXT NOT NULL DEFAULT '{}',
    keyword_profile TEXT,
    keyword_index_ref TEXT,
    embedding_profile TEXT,
    vector_index TEXT NOT NULL DEFAULT 'absent',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_kb ON snapshots (kb_id);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    state TEXT NOT NULL,
    progress REAL NOT NULL DEFAULT 0,
    revision INTEGER NOT NULL DEFAULT 0,
    idempotency_key TEXT,
    lease_until TEXT,
    result_version_id TEXT,
    diagnostics TEXT NOT NULL DEFAULT '[]',
    error_code TEXT,
    payload TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jobs_kind_state ON jobs (kind, state);
CREATE UNIQUE INDEX IF NOT EXISTS uq_jobs_idempotency
    ON jobs (kind, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS job_events (
    job_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    event TEXT NOT NULL,
    PRIMARY KEY (job_id, seq)
);

CREATE TABLE IF NOT EXISTS import_previews (
    preview_id TEXT PRIMARY KEY,
    kb_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    preview_hash TEXT NOT NULL,
    added TEXT NOT NULL DEFAULT '[]',
    modified TEXT NOT NULL DEFAULT '[]',
    removed TEXT NOT NULL DEFAULT '[]',
    conflicts TEXT NOT NULL DEFAULT '[]',
    manifest TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_import_previews_kb ON import_previews (kb_id);

CREATE TABLE IF NOT EXISTS idempotency (
    principal_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    job_id TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (principal_id, operation, key)
);

CREATE TABLE IF NOT EXISTS upload_batches (
    batch_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    selection TEXT NOT NULL DEFAULT '{}',
    files TEXT NOT NULL DEFAULT '[]',
    manifest TEXT,
    created_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS upload_parts (
    batch_id TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    digest TEXT NOT NULL,
    size INTEGER NOT NULL,
    PRIMARY KEY (batch_id, relative_path)
);
