CREATE TABLE submission_sequence (id BIGINT AUTO_INCREMENT PRIMARY KEY,reservation_id BIGINT NOT NULL UNIQUE);
ALTER TABLE reservation ADD COLUMN submitted_order BIGINT NOT NULL DEFAULT 0;
CREATE INDEX idx_waitlist_order ON reservation(instrument_id,status,submitted_order,id);
