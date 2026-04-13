import { httpRequest } from "@/api/httpClient";
import type {
  BuildCreatePayload,
  BuildDetail,
  BuildSummary,
  KnowledgeChunkDetail,
  KnowledgeChunkVectorDetail,
  KnowledgeChunkSummary,
  KnowledgeDocumentDetail,
  KnowledgeDocumentUploadPayload,
  KnowledgeDocumentSummary,
  KnowledgeDocumentUploadResponse,
  RetrievalDebugPayload,
  RetrievalDebugResponse,
} from "@/types/console";

const toFormData = (
  file: File,
  extra: KnowledgeDocumentUploadPayload,
): FormData => {
  const formData = new FormData();
  formData.append("file", file);
  if (extra.title?.trim()) {
    formData.append("title", extra.title.trim());
  }
  if (extra.document_id?.trim()) {
    formData.append("document_id", extra.document_id.trim());
  }
  if (extra.origin_uri?.trim()) {
    formData.append("origin_uri", extra.origin_uri.trim());
  }
  if (extra.source_type?.trim()) {
    formData.append("source_type", extra.source_type.trim());
  }
  if (extra.jurisdiction?.trim()) {
    formData.append("jurisdiction", extra.jurisdiction.trim());
  }
  if (extra.domain?.trim()) {
    formData.append("domain", extra.domain.trim());
  }
  if (extra.tags?.trim()) {
    formData.append("tags", extra.tags.trim());
  }
  return formData;
};

export const knowledgeApi = {
  uploadDocument(
    file: File,
    extra: KnowledgeDocumentUploadPayload = {},
  ): Promise<KnowledgeDocumentUploadResponse> {
    const formData = toFormData(file, extra);
    return httpRequest<KnowledgeDocumentUploadResponse>("/knowledge/documents/upload", {
      method: "POST",
      body: formData,
      isFormData: true,
    });
  },

  createBuild(payload: BuildCreatePayload): Promise<BuildDetail> {
    return httpRequest<BuildDetail>("/knowledge/builds", {
      method: "POST",
      body: payload,
    });
  },

  listBuilds(): Promise<BuildSummary[]> {
    return httpRequest<BuildSummary[]>("/knowledge/builds");
  },

  getBuild(buildId: string): Promise<BuildDetail> {
    return httpRequest<BuildDetail>(`/knowledge/builds/${buildId}`);
  },

  listDocuments(): Promise<KnowledgeDocumentSummary[]> {
    return httpRequest<KnowledgeDocumentSummary[]>("/knowledge/documents");
  },

  getDocument(documentId: string): Promise<KnowledgeDocumentDetail> {
    return httpRequest<KnowledgeDocumentDetail>(`/knowledge/documents/${documentId}`);
  },

  listDocumentChunks(documentId: string): Promise<KnowledgeChunkSummary[]> {
    return httpRequest<KnowledgeChunkSummary[]>(
      `/knowledge/documents/${documentId}/chunks`,
    );
  },

  getChunk(chunkId: string): Promise<KnowledgeChunkDetail> {
    return httpRequest<KnowledgeChunkDetail>(`/knowledge/chunks/${chunkId}`);
  },

  getChunkVectorDetail(chunkId: string): Promise<KnowledgeChunkVectorDetail> {
    return httpRequest<KnowledgeChunkVectorDetail>(`/knowledge/chunks/${chunkId}/vector`);
  },

  retrievalDebug(payload: RetrievalDebugPayload): Promise<RetrievalDebugResponse> {
    return httpRequest<RetrievalDebugResponse>("/knowledge/retrieval/debug", {
      method: "POST",
      body: payload,
    });
  },
};
