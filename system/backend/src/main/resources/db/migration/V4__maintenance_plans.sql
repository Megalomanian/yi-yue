ALTER TABLE maintenance ADD COLUMN applied BOOLEAN NOT NULL DEFAULT TRUE;
CREATE INDEX idx_maintenance_window ON maintenance(instrument_id,start_at,end_at);
