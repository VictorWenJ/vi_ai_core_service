import type { ChatCitation } from "@/types/chat";

export type KnowledgeDocumentUploadResponse = {
  document_id: string;
  title: string;
  source_type: string;
  file_name?: string | null;
  updated_at?: string | null;
  metadata: Record<string, unknown>;
};

export type BuildCreatePayload = {
  version_id?: string;
  force_rebuild_document_ids?: string[];
  max_failure_ratio?: number;
  max_empty_chunk_ratio?: number;
};

export type BuildMetadata = {
  build_id: string;
  version_id: string;
  chunk_strategy_version: string;
  embedding_model_version: string;
  build_mode: string;
  started_at: string;
  completed_at: string;
};

export type BuildStatistics = {
  requested_document_count: number;
  processed_document_count: number;
  skipped_document_count: number;
  failed_document_count: number;
  chunk_count: number;
  upserted_count: number;
  embedding_batch_count: number;
  latency_ms: number;
};

export type BuildQualityGate = {
  passed: boolean;
  failed_rules: string[];
  failure_ratio: number;
  empty_chunk_ratio: number;
  max_failure_ratio: number;
  max_empty_chunk_ratio: number;
};

export type BuildSummary = {
  metadata: BuildMetadata;
  statistics: BuildStatistics;
  quality_gate: BuildQualityGate;
};

export type BuildDetail = BuildSummary & {
  manifest: Record<string, unknown>;
  ingestion_results: Array<Record<string, unknown>>;
};

export type KnowledgeDocumentSummary = {
  document_id: string;
  title: string;
  source_type: string;
  origin_uri?: string | null;
  file_name?: string | null;
  jurisdiction?: string | null;
  domain?: string | null;
  tags: string[];
  effective_at?: string | null;
  updated_at?: string | null;
  visibility: string;
  metadata: Record<string, unknown>;
  chunk_count: number;
};

export type KnowledgeDocumentDetail = KnowledgeDocumentSummary & {
  content: string;
};

export type KnowledgeChunkSummary = {
  chunk_id: string;
  document_id: string;
  chunk_index: number;
  token_count: number;
  embedding_model: string;
  chunk_text_preview: string;
  metadata: Record<string, unknown>;
};

export type KnowledgeChunkDetail = {
  chunk_id: string;
  document_id: string;
  chunk_index: number;
  token_count: number;
  embedding_model: string;
  chunk_text: string;
  metadata: Record<string, unknown>;
};

export type RetrievalDebugPayload = {
  query_text: string;
  metadata_filter?: Record<string, unknown>;
  top_k?: number;
};

export type RetrievalDebugHit = {
  chunk_id: string;
  document_id: string;
  score: number;
  title?: string | null;
  source_type?: string | null;
  origin_uri?: string | null;
  snippet: string;
  metadata: Record<string, unknown>;
};

export type RetrievalDebugResponse = {
  query_text: string;
  top_k: number;
  status: string;
  hits: RetrievalDebugHit[];
  citations: ChatCitation[];
  trace: Record<string, unknown>;
};

export type EvaluationRetrievalLabelPayload = {
  expected_document_ids?: string[];
  expected_chunk_ids?: string[];
  min_recall?: number;
};

export type EvaluationCitationLabelPayload = {
  expected_citation_ids?: string[];
  expected_document_ids?: string[];
  min_recall?: number;
  min_precision?: number;
};

export type EvaluationAnswerLabelPayload = {
  required_terms?: string[];
  forbidden_terms?: string[];
  min_required_term_hit_ratio?: number;
  max_forbidden_term_hit_count?: number;
};

export type EvaluationSamplePayload = {
  sample_id?: string;
  query_text: string;
  metadata_filter?: Record<string, unknown>;
  top_k?: number;
  retrieval_label?: EvaluationRetrievalLabelPayload;
  citation_label?: EvaluationCitationLabelPayload;
  answer_label?: EvaluationAnswerLabelPayload;
  metadata?: Record<string, unknown>;
};

export type EvaluationRunCreatePayload = {
  dataset_id?: string;
  version_id?: string;
  samples?: EvaluationSamplePayload[];
  metadata?: Record<string, unknown>;
};

export type EvaluationRunSummary = {
  run_id: string;
  dataset_id: string;
  dataset_version_id: string;
  started_at: string;
  completed_at: string;
  summary: Record<string, unknown>;
  metadata: Record<string, unknown>;
  case_count: number;
};

export type EvaluationRunCase = {
  sample_id: string;
  retrieval: Record<string, unknown>;
  citation: Record<string, unknown>;
  answer: Record<string, unknown>;
  retrieval_status: string;
  passed: boolean;
  resolved_top_k: number;
};

export type RuntimeSummary = {
  service: string;
  default_provider: string;
  rag_enabled: boolean;
  embedding_provider: string;
  embedding_model: string;
  retrieval_top_k: number;
  score_threshold?: number | null;
  chunk_token_size: number;
  chunk_overlap_token_size: number;
  document_count: number;
  chunk_count: number;
  build_count: number;
  evaluation_run_count: number;
};

export type RuntimeConfigSummary = {
  default_provider: string;
  providers: Record<string, unknown>;
  streaming: Record<string, unknown>;
  rag: Record<string, unknown>;
};

export type RuntimeHealth = {
  status: string;
  service: string;
  checked_at: string;
  summary: RuntimeSummary;
};
