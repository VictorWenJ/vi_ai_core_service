"""Create RAG control-plane persistence tables.

Revision ID: 20260413_0001
Revises: 
Create Date: 2026-04-13 00:01:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


_AUTO_ID_TYPE = sa.Integer().with_variant(sa.BigInteger(), "mysql")


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", _AUTO_ID_TYPE, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("origin_uri", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("jurisdiction", sa.String(length=128), nullable=True),
        sa.Column("domain", sa.String(length=128), nullable=True),
        sa.Column("visibility", sa.String(length=64), nullable=False),
        sa.Column("tags_details", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("latest_version_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("document_id"),
    )

    op.create_table(
        "document_versions",
        sa.Column("id", _AUTO_ID_TYPE, primary_key=True, autoincrement=True),
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("normalized_text_hash", sa.String(length=128), nullable=False),
        sa.Column("hash_algorithm", sa.String(length=32), nullable=False),
        sa.Column("raw_storage_path", sa.Text(), nullable=False),
        sa.Column("normalized_storage_path", sa.Text(), nullable=False),
        sa.Column("raw_file_size", sa.BigInteger(), nullable=False),
        sa.Column("normalized_char_count", sa.Integer(), nullable=False),
        sa.Column("parser_name", sa.String(length=128), nullable=False),
        sa.Column("cleaner_name", sa.String(length=128), nullable=False),
        sa.Column("metadata_details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("version_id"),
    )
    op.create_index(
        "idx_document_versions_document_id",
        "document_versions",
        ["document_id"],
        unique=False,
    )

    op.create_table(
        "build_tasks",
        sa.Column("id", _AUTO_ID_TYPE, primary_key=True, autoincrement=True),
        sa.Column("build_id", sa.String(length=64), nullable=False),
        sa.Column("build_version_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("chunk_strategy_name", sa.String(length=128), nullable=False),
        sa.Column("chunk_strategy_details", sa.JSON(), nullable=False),
        sa.Column("embedding_model_name", sa.String(length=128), nullable=False),
        sa.Column("manifest_details", sa.JSON(), nullable=False),
        sa.Column("statistics_details", sa.JSON(), nullable=False),
        sa.Column("quality_gate_details", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("build_id"),
    )

    op.create_table(
        "build_documents",
        sa.Column("id", _AUTO_ID_TYPE, primary_key=True, autoincrement=True),
        sa.Column("build_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("document_version_id", sa.String(length=64), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vector_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_build_documents_build_id",
        "build_documents",
        ["build_id"],
        unique=False,
    )
    op.create_index(
        "idx_build_documents_document_id",
        "build_documents",
        ["document_id"],
        unique=False,
    )

    op.create_table(
        "chunks",
        sa.Column("id", _AUTO_ID_TYPE, primary_key=True, autoincrement=True),
        sa.Column("chunk_id", sa.String(length=64), nullable=False),
        sa.Column("build_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("document_version_id", sa.String(length=64), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=True),
        sa.Column("end_offset", sa.Integer(), nullable=True),
        sa.Column("chunk_text_hash", sa.String(length=128), nullable=False),
        sa.Column("chunk_preview", sa.Text(), nullable=False),
        sa.Column("embedding_model_name", sa.String(length=128), nullable=False),
        sa.Column("vector_dimension", sa.Integer(), nullable=False),
        sa.Column("vector_collection", sa.String(length=128), nullable=False),
        sa.Column("vector_point_id", sa.String(length=128), nullable=False),
        sa.Column("metadata_details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("chunk_id"),
    )
    op.create_index("idx_chunks_document_id", "chunks", ["document_id"], unique=False)
    op.create_index("idx_chunks_build_id", "chunks", ["build_id"], unique=False)
    op.create_index(
        "idx_chunks_vector_point_id",
        "chunks",
        ["vector_point_id"],
        unique=False,
    )

    op.create_table(
        "evaluation_runs",
        sa.Column("id", _AUTO_ID_TYPE, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("build_id", sa.String(length=64), nullable=True),
        sa.Column("dataset_id", sa.String(length=128), nullable=True),
        sa.Column("dataset_version_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("trigger_type", sa.String(length=64), nullable=False),
        sa.Column("triggered_by", sa.String(length=128), nullable=False),
        sa.Column("summary_details", sa.JSON(), nullable=False),
        sa.Column("metadata_details", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_id"),
    )

    op.create_table(
        "evaluation_cases",
        sa.Column("id", _AUTO_ID_TYPE, primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("sample_id", sa.String(length=128), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("metadata_filter_details", sa.JSON(), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=True),
        sa.Column("retrieval_label_details", sa.JSON(), nullable=False),
        sa.Column("citation_label_details", sa.JSON(), nullable=False),
        sa.Column("answer_label_details", sa.JSON(), nullable=False),
        sa.Column("retrieved_chunk_ids", sa.JSON(), nullable=False),
        sa.Column("retrieved_document_ids", sa.JSON(), nullable=False),
        sa.Column("generated_citation_ids", sa.JSON(), nullable=False),
        sa.Column("generated_citation_document_ids", sa.JSON(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("case_result_details", sa.JSON(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id"),
    )
    op.create_index(
        "idx_evaluation_cases_run_id",
        "evaluation_cases",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_evaluation_cases_run_id", table_name="evaluation_cases")
    op.drop_table("evaluation_cases")

    op.drop_table("evaluation_runs")

    op.drop_index("idx_chunks_vector_point_id", table_name="chunks")
    op.drop_index("idx_chunks_build_id", table_name="chunks")
    op.drop_index("idx_chunks_document_id", table_name="chunks")
    op.drop_table("chunks")

    op.drop_index("idx_build_documents_document_id", table_name="build_documents")
    op.drop_index("idx_build_documents_build_id", table_name="build_documents")
    op.drop_table("build_documents")

    op.drop_table("build_tasks")

    op.drop_index("idx_document_versions_document_id", table_name="document_versions")
    op.drop_table("document_versions")

    op.drop_table("documents")
