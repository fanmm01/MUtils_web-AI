-- Track worker lease ownership so expired recovery and heartbeats are fenced.
ALTER TABLE jobs ADD COLUMN worker_id TEXT;
