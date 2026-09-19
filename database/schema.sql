CREATE DATABASE IF NOT EXISTS eva_ai
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE eva_ai;

CREATE TABLE IF NOT EXISTS conversations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_conversations_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS memories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    memory_type VARCHAR(50) NOT NULL DEFAULT 'episodic',
    content TEXT NOT NULL,
    importance DECIMAL(4,3) NOT NULL DEFAULT 0.500,
    emotional_value DECIMAL(4,3) NOT NULL DEFAULT 0.000,
    source_message_id BIGINT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed DATETIME NULL,
    access_count INT NOT NULL DEFAULT 0,
    INDEX idx_memories_type (memory_type),
    INDEX idx_memories_importance (importance)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS emotional_state (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    emotion VARCHAR(50) NOT NULL,
    intensity DECIMAL(4,3) NOT NULL DEFAULT 0.500,
    trust DECIMAL(4,3) NOT NULL DEFAULT 0.400,
    energy DECIMAL(4,3) NOT NULL DEFAULT 0.750,
    curiosity DECIMAL(4,3) NOT NULL DEFAULT 0.600,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS identity_profile (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(20) NOT NULL,
    identity_key VARCHAR(80) NOT NULL,
    identity_value TEXT NOT NULL,
    confidence DECIMAL(4,3) NOT NULL DEFAULT 0.800,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL,
    UNIQUE KEY uq_identity_subject_key (subject, identity_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS relationships (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    entity_name VARCHAR(120) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL DEFAULT 'persona',
    affinity DECIMAL(5,3) NOT NULL DEFAULT 0.000,
    trust DECIMAL(5,3) NOT NULL DEFAULT 0.400,
    familiarity DECIMAL(5,3) NOT NULL DEFAULT 0.000,
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL,
    UNIQUE KEY uq_relationship_entity (entity_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS goals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(180) NOT NULL,
    description TEXT NULL,
    priority DECIMAL(4,3) NOT NULL DEFAULT 0.500,
    progress DECIMAL(4,3) NOT NULL DEFAULT 0.000,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    INDEX idx_goals_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS internal_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    summary TEXT NOT NULL,
    importance DECIMAL(4,3) NOT NULL DEFAULT 0.500,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_internal_events_type (event_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS decisions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    reason_summary TEXT NULL,
    confidence DECIMAL(4,3) NOT NULL DEFAULT 0.500,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_decisions_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
