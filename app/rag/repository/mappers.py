"""Repository 层 ORM 实体到读模型的映射器。"""

from __future__ import annotations

from app.rag.repository._utils import copy_json_dict, copy_json_list, datetime_to_iso
from app.rag.repository.models import (
    BuildDocumentEntity,
    BuildTaskEntity,
    ChunkEntity,
    DocumentEntity,
    DocumentVersionEntity,
    EvaluationCaseEntity,
    EvaluationRunEntity,
)
from app.rag.repository.read_models import (
    BuildDocumentRecord,
    BuildTaskRecord,
    BuildTaskStatusSummary,
    ChunkRecord,
    DocumentRecord,
    DocumentVersionRecord,
    EvaluationCaseRecord,
    EvaluationRunRecord,
    EvaluationRunStatusSummary,
    LatestDocumentVersionRecord,
)


def map_document_entity_to_record(entity: DocumentEntity) -> DocumentRecord:
    """将文档 ORM 实体映射为文档读模型。"""
    return DocumentRecord(
        # 文档业务 ID。
        document_id=entity.document_id,
        # 文档标题。
        title=entity.title,
        # 文档来源类型。
        source_type=entity.source_type,
        # 文档来源 URI。
        origin_uri=entity.origin_uri,
        # 原始文件名。
        file_name=entity.file_name,
        # 法域标签。
        jurisdiction=entity.jurisdiction,
        # 业务域标签。
        domain=entity.domain,
        # 可见性范围。
        visibility=entity.visibility,
        # 文档标签详情列表。
        tags_details=copy_json_list(entity.tags_details),
        # 文档状态。
        status=entity.status,
        # 最新版本业务 ID。
        latest_version_id=entity.latest_version_id,
        # 创建时间（UTC ISO）。
        created_at=datetime_to_iso(entity.created_at),
        # 更新时间（UTC ISO）。
        updated_at=datetime_to_iso(entity.updated_at),
    )


def map_document_version_entity_to_record(entity: DocumentVersionEntity) -> DocumentVersionRecord:
    """将文档版本 ORM 实体映射为文档版本读模型。"""
    return DocumentVersionRecord(
        # 版本业务 ID。
        version_id=entity.version_id,
        # 所属文档业务 ID。
        document_id=entity.document_id,
        # 版本号。
        version_no=entity.version_no,
        # 原始内容哈希。
        content_hash=entity.content_hash,
        # 规范化文本哈希。
        normalized_text_hash=entity.normalized_text_hash,
        # 哈希算法名称。
        hash_algorithm=entity.hash_algorithm,
        # 原始文件存储路径。
        raw_storage_path=entity.raw_storage_path,
        # 规范化文本存储路径。
        normalized_storage_path=entity.normalized_storage_path,
        # 原始文件大小（字节）。
        raw_file_size=entity.raw_file_size,
        # 规范化文本字符数。
        normalized_char_count=entity.normalized_char_count,
        # 解析器名称。
        parser_name=entity.parser_name,
        # 清洗器名称。
        cleaner_name=entity.cleaner_name,
        # 版本元数据详情。
        metadata_details=copy_json_dict(entity.metadata_details),
        # 创建时间（UTC ISO）。
        created_at=datetime_to_iso(entity.created_at),
    )


def map_latest_document_version_record(
    document_entity: DocumentEntity,
    version_entity: DocumentVersionEntity,
) -> LatestDocumentVersionRecord:
    """将文档与其最新版本实体组合映射为构建用读模型。"""
    return LatestDocumentVersionRecord(
        # 文档主记录。
        document=map_document_entity_to_record(document_entity),
        # 最新版本记录。
        version=map_document_version_entity_to_record(version_entity),
    )


def map_build_task_entity_to_record(entity: BuildTaskEntity) -> BuildTaskRecord:
    """将构建任务 ORM 实体映射为构建任务读模型。"""
    return BuildTaskRecord(
        # 构建任务业务 ID。
        build_id=entity.build_id,
        # 构建版本标识。
        build_version_id=entity.build_version_id,
        # 构建状态。
        status=entity.status,
        # 分块策略名称。
        chunk_strategy_name=entity.chunk_strategy_name,
        # 分块策略详情。
        chunk_strategy_details=copy_json_dict(entity.chunk_strategy_details),
        # embedding 模型名称。
        embedding_model_name=entity.embedding_model_name,
        # 构建输入快照详情。
        manifest_details=copy_json_dict(entity.manifest_details),
        # 构建统计详情。
        statistics_details=copy_json_dict(entity.statistics_details),
        # 质量门禁详情。
        quality_gate_details=copy_json_dict(entity.quality_gate_details),
        # 错误信息。
        error_message=entity.error_message,
        # 开始时间（UTC ISO）。
        started_at=datetime_to_iso(entity.started_at),
        # 完成时间（UTC ISO）。
        completed_at=datetime_to_iso(entity.completed_at),
        # 创建时间（UTC ISO）。
        created_at=datetime_to_iso(entity.created_at),
    )


def map_build_task_entity_to_status_summary(entity: BuildTaskEntity) -> BuildTaskStatusSummary:
    """将构建任务 ORM 实体映射为轻量状态摘要读模型。"""
    return BuildTaskStatusSummary(
        # 构建任务业务 ID。
        build_id=entity.build_id,
        # 构建任务状态。
        status=entity.status,
        # 创建时间（UTC ISO）。
        created_at=datetime_to_iso(entity.created_at),
        # 完成时间（UTC ISO）。
        completed_at=datetime_to_iso(entity.completed_at),
    )


def map_build_document_entity_to_record(entity: BuildDocumentEntity) -> BuildDocumentRecord:
    """将构建文档关系 ORM 实体映射为构建文档读模型。"""
    return BuildDocumentRecord(
        # 所属构建任务业务 ID。
        build_id=entity.build_id,
        # 文档业务 ID。
        document_id=entity.document_id,
        # 文档版本业务 ID。
        document_version_id=entity.document_version_id,
        # 文档内容哈希。
        content_hash=entity.content_hash,
        # 本次动作类型。
        action=entity.action,
        # chunk 数量。
        chunk_count=entity.chunk_count,
        # 向量数量。
        vector_count=entity.vector_count,
        # 错误信息。
        error_message=entity.error_message,
        # 创建时间（UTC ISO）。
        created_at=datetime_to_iso(entity.created_at),
    )


def map_chunk_entity_to_record(entity: ChunkEntity) -> ChunkRecord:
    """将 chunk ORM 实体映射为 chunk 读模型。"""
    return ChunkRecord(
        # chunk 业务 ID。
        chunk_id=entity.chunk_id,
        # 所属构建任务业务 ID。
        build_id=entity.build_id,
        # 所属文档业务 ID。
        document_id=entity.document_id,
        # 所属文档版本业务 ID。
        document_version_id=entity.document_version_id,
        # chunk 序号。
        chunk_index=entity.chunk_index,
        # token 数量。
        token_count=entity.token_count,
        # 起始偏移量。
        start_offset=entity.start_offset,
        # 结束偏移量。
        end_offset=entity.end_offset,
        # chunk 文本哈希。
        chunk_text_hash=entity.chunk_text_hash,
        # chunk 预览文本。
        chunk_preview=entity.chunk_preview,
        # embedding 模型名称。
        embedding_model_name=entity.embedding_model_name,
        # 向量维度。
        vector_dimension=entity.vector_dimension,
        # 向量集合名称。
        vector_collection=entity.vector_collection,
        # 向量点 ID。
        vector_point_id=entity.vector_point_id,
        # chunk 元数据详情。
        metadata_details=copy_json_dict(entity.metadata_details),
        # 创建时间（UTC ISO）。
        created_at=datetime_to_iso(entity.created_at),
    )


def map_evaluation_run_entity_to_record(entity: EvaluationRunEntity) -> EvaluationRunRecord:
    """将评测运行 ORM 实体映射为评测运行读模型。"""
    return EvaluationRunRecord(
        # 运行业务 ID。
        run_id=entity.run_id,
        # 关联构建任务业务 ID。
        build_id=entity.build_id,
        # 数据集业务 ID，可为空。
        dataset_id=entity.dataset_id,
        # 数据集版本业务 ID，可为空。
        dataset_version_id=entity.dataset_version_id,
        # 运行状态。
        status=entity.status,
        # 触发类型。
        trigger_type=entity.trigger_type,
        # 触发来源。
        triggered_by=entity.triggered_by,
        # 汇总详情。
        summary_details=copy_json_dict(entity.summary_details),
        # 元数据详情。
        metadata_details=copy_json_dict(entity.metadata_details),
        # 错误信息。
        error_message=entity.error_message,
        # 开始时间（UTC ISO）。
        started_at=datetime_to_iso(entity.started_at),
        # 完成时间（UTC ISO）。
        completed_at=datetime_to_iso(entity.completed_at),
        # 创建时间（UTC ISO）。
        created_at=datetime_to_iso(entity.created_at),
    )


def map_evaluation_run_entity_to_status_summary(
    entity: EvaluationRunEntity,
) -> EvaluationRunStatusSummary:
    """将评测运行 ORM 实体映射为轻量状态摘要读模型。"""
    return EvaluationRunStatusSummary(
        # 运行业务 ID。
        run_id=entity.run_id,
        # 运行状态。
        status=entity.status,
        # 创建时间（UTC ISO）。
        created_at=datetime_to_iso(entity.created_at),
        # 完成时间（UTC ISO）。
        completed_at=datetime_to_iso(entity.completed_at),
    )


def map_evaluation_case_entity_to_record(entity: EvaluationCaseEntity) -> EvaluationCaseRecord:
    """将评测样本 ORM 实体映射为评测样本读模型。"""
    return EvaluationCaseRecord(
        # case 业务 ID。
        case_id=entity.case_id,
        # 所属运行业务 ID。
        run_id=entity.run_id,
        # 样本业务 ID。
        sample_id=entity.sample_id,
        # 查询文本。
        query_text=entity.query_text,
        # 元数据过滤详情。
        metadata_filter_details=copy_json_dict(entity.metadata_filter_details),
        # 检索 top-k。
        top_k=entity.top_k,
        # 检索标签详情。
        retrieval_label_details=copy_json_dict(entity.retrieval_label_details),
        # 引用标签详情。
        citation_label_details=copy_json_dict(entity.citation_label_details),
        # 回答标签详情。
        answer_label_details=copy_json_dict(entity.answer_label_details),
        # 检索命中 chunk ID 列表。
        retrieved_chunk_ids=copy_json_list(entity.retrieved_chunk_ids),
        # 检索命中文档 ID 列表。
        retrieved_document_ids=copy_json_list(entity.retrieved_document_ids),
        # 生成引用 ID 列表。
        generated_citation_ids=copy_json_list(entity.generated_citation_ids),
        # 生成引用文档 ID 列表。
        generated_citation_document_ids=copy_json_list(entity.generated_citation_document_ids),
        # 回答文本。
        answer_text=entity.answer_text,
        # case 结果详情。
        case_result_details=copy_json_dict(entity.case_result_details),
        # 是否通过。
        passed=entity.passed,
        # 错误信息。
        error_message=entity.error_message,
        # 创建时间（UTC ISO）。
        created_at=datetime_to_iso(entity.created_at),
    )
