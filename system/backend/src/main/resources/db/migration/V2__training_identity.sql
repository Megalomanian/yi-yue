CREATE TABLE training_enrollment (id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id BIGINT NOT NULL, instrument_id BIGINT NOT NULL, approved BOOLEAN NOT NULL DEFAULT FALSE, UNIQUE(user_id,instrument_id));
CREATE TABLE identity_review (id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id BIGINT NOT NULL UNIQUE, identity_info VARCHAR(2000) NOT NULL, contact VARCHAR(1000) NOT NULL);
ALTER TABLE qualification ADD COLUMN reminder_sent BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX idx_notification_user ON notification(user_id,id);
CREATE INDEX idx_audit_time ON audit_log(created_at);
CREATE INDEX idx_qualification_expiry ON qualification(expires_at);
