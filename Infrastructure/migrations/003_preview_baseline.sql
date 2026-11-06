-- A preview is only valid against the baseline it was computed from; applying a
-- stale preview after another import moved the baseline must conflict instead
-- of silently reusing an old job or skipping a real change.
ALTER TABLE import_previews ADD COLUMN baseline_hash TEXT;

-- Upload batches must not share a destination: each batch writes under its own
-- key so two clients uploading the same relative path cannot overwrite one
-- another mid-flight. Only a completed batch is promoted to the source store.
