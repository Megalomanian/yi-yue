ALTER TABLE audit_log ADD COLUMN source_ip VARCHAR(60) DEFAULT 'system';
ALTER TABLE audit_log ADD COLUMN result VARCHAR(20) DEFAULT 'SUCCESS';
CREATE TABLE bill_adjustment (id BIGINT AUTO_INCREMENT PRIMARY KEY,bill_id BIGINT NOT NULL,actor_id BIGINT NOT NULL,previous_adjustment DECIMAL(12,2) NOT NULL,new_adjustment DECIMAL(12,2) NOT NULL,reason VARCHAR(500) NOT NULL,created_at VARCHAR(30) NOT NULL);
CREATE TABLE integration_event (id BIGINT AUTO_INCREMENT PRIMARY KEY,channel VARCHAR(30) NOT NULL,object_id BIGINT NOT NULL,payload VARCHAR(4000) NOT NULL,status VARCHAR(20) NOT NULL,attempts INT NOT NULL DEFAULT 0,next_at VARCHAR(30) NOT NULL,last_error VARCHAR(200));
CREATE INDEX idx_event_pending ON integration_event(status,next_at);
