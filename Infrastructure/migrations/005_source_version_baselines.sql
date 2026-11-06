-- Preserve the exact source baseline associated with each immutable snapshot.
-- A rollback must compare against that version, not a newer READY build.
CREATE TABLE source_version_baselines (
    source_id TEXT NOT NULL,
    version_id TEXT NOT NULL,
    manifest TEXT,
    revision_ids TEXT NOT NULL,
    PRIMARY KEY (source_id, version_id)
);
