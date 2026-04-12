-- RAG 控制面持久化升级：基础表结构迁移（MySQL 基线）。

CREATE TABLE IF NOT EXISTS documents (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    source_type VARCHAR(64) NOT NULL,
    origin_uri TEXT NULL,
    file_name VARCHAR(255) NULL,
    jurisdiction VARCHAR(128) NULL,
    domain VARCHAR(128) NULL,
    visibility VARCHAR(64) NOT NULL DEFAULT 'internal',
    tags_details JSON NOT NULL,
    status VARCHAR(64) NOT NULL DEFAULT 'active',
    latest_version_id VARCHAR(64) NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS document_versions (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    version_id VARCHAR(64) NOT NULL UNIQUE,
    document_id VARCHAR(64) NOT NULL,
    version_no INT NOT NULL,
    content_hash VARCHAR(128) NOT NULL,
    normalized_text_hash VARCHAR(128) NOT NULL,
    hash_algorithm VARCHAR(32) NOT NULL,
    raw_storage_path TEXT NOT NULL,
    normalized_storage_path TEXT NOT NULL,
    raw_file_size BIGINT NOT NULL,
    normalized_char_count INT NOT NULL,
    parser_name VARCHAR(128) NOT NULL,
    cleaner_name VARCHAR(128) NOT NULL,
    metadata_details JSON NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_document_versions_document_id (document_id)
);

CREATE TABLE IF NOT EXISTS build_tasks (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    build_id VARCHAR(64) NOT NULL UNIQUE,
    build_version_id VARCHAR(128) NOT NULL,
    status VARCHAR(64) NOT NULL,
    chunk_strategy_name VARCHAR(128) NOT NULL,
    chunk_strategy_details JSON NOT NULL,
    embedding_model_name VARCHAR(128) NOT NULL,
    manifest_details JSON NOT NULL,
    statistics_details JSON NOT NULL,
    quality_gate_details JSON NOT NULL,
    error_message TEXT NULL,
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS build_documents (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    build_id VARCHAR(64) NOT NULL,
    document_id VARCHAR(64) NOT NULL,
    document_version_id VARCHAR(64) NOT NULL,
    content_hash VARCHAR(128) NOT NULL,
    action VARCHAR(64) NOT NULL,
    chunk_count INT NOT NULL DEFAULT 0,
    vector_count INT NOT NULL DEFAULT 0,
    error_message TEXT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_build_documents_build_id (build_id),
    INDEX idx_build_documents_document_id (document_id)
);

CREATE TABLE IF NOT EXISTS chunks (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    chunk_id VARCHAR(64) NOT NULL UNIQUE,
    build_id VARCHAR(64) NOT NULL,
    document_id VARCHAR(64) NOT NULL,
    document_version_id VARCHAR(64) NOT NULL,
    chunk_index INT NOT NULL,
    token_count INT NOT NULL,
    start_offset INT NULL,
    end_offset INT NULL,
    chunk_text_hash VARCHAR(128) NOT NULL,
    chunk_preview TEXT NOT NULL,
    embedding_model_name VARCHAR(128) NOT NULL,
    vector_dimension INT NOT NULL,
    vector_collection VARCHAR(128) NOT NULL,
    vector_point_id VARCHAR(128) NOT NULL,
    metadata_details JSON NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_chunks_document_id (document_id),
    INDEX idx_chunks_build_id (build_id),
    INDEX idx_chunks_vector_point_id (vector_point_id)
);

CREATE TABLE IF NOT EXISTS evaluation_runs (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL UNIQUE,
    build_id VARCHAR(64) NULL,
    dataset_id VARCHAR(128) NOT NULL,
    dataset_version_id VARCHAR(128) NOT NULL,
    status VARCHAR(64) NOT NULL,
    trigger_type VARCHAR(64) NOT NULL,
    triggered_by VARCHAR(128) NOT NULL,
    summary_details JSON NOT NULL,
    metadata_details JSON NOT NULL,
    error_message TEXT NULL,
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluation_cases (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    case_id VARCHAR(64) NOT NULL UNIQUE,
    run_id VARCHAR(64) NOT NULL,
    sample_id VARCHAR(128) NOT NULL,
    query_text TEXT NOT NULL,
    metadata_filter_details JSON NOT NULL,
    top_k INT NULL,
    retrieval_label_details JSON NOT NULL,
    citation_label_details JSON NOT NULL,
    answer_label_details JSON NOT NULL,
    retrieved_chunk_ids JSON NOT NULL,
    retrieved_document_ids JSON NOT NULL,
    generated_citation_ids JSON NOT NULL,
    generated_citation_document_ids JSON NOT NULL,
    answer_text TEXT NOT NULL,
    case_result_details JSON NOT NULL,
    passed BOOLEAN NOT NULL,
    error_message TEXT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_evaluation_cases_run_id (run_id)
);

