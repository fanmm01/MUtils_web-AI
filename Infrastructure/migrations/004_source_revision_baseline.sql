-- The source file hash alone cannot distinguish a manual document edit from a
-- source import. Keep the revision actually imported for each source path so
-- a later scan cannot silently overwrite a newer manual revision.
ALTER TABLE source_baselines ADD COLUMN revision_ids TEXT NOT NULL DEFAULT '{}';
