import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { ApiClientError } from "@/api/errors";
import { knowledgeApi } from "@/api/knowledgeApi";

const getErrorMessage = (error: unknown): string => {
  if (error instanceof ApiClientError) {
    const prefix = error.status ? `HTTP ${error.status}: ` : "";
    return `${prefix}${error.message}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unknown request error.";
};

const parseFilterInput = (rawValue: string): Record<string, unknown> => {
  const trimmed = rawValue.trim();
  if (!trimmed) {
    return {};
  }
  try {
    const parsed = JSON.parse(trimmed) as Record<string, unknown>;
    if (parsed && typeof parsed === "object") {
      return parsed;
    }
    return {};
  } catch {
    return {};
  }
};

export function useChunkInspector() {
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [selectedChunkId, setSelectedChunkId] = useState<string | null>(null);
  const [debugQueryText, setDebugQueryText] = useState("");
  const [debugTopK, setDebugTopK] = useState("4");
  const [debugFilterJson, setDebugFilterJson] = useState("");
  const [message, setMessage] = useState("Ready.");

  const documentsQuery = useQuery({
    queryKey: ["knowledge-documents"],
    queryFn: () => knowledgeApi.listDocuments(),
  });

  const documentDetailQuery = useQuery({
    queryKey: ["knowledge-document-detail", selectedDocumentId],
    queryFn: () => knowledgeApi.getDocument(selectedDocumentId as string),
    enabled: Boolean(selectedDocumentId),
  });

  const chunksQuery = useQuery({
    queryKey: ["knowledge-document-chunks", selectedDocumentId],
    queryFn: () => knowledgeApi.listDocumentChunks(selectedDocumentId as string),
    enabled: Boolean(selectedDocumentId),
  });

  const chunkDetailQuery = useQuery({
    queryKey: ["knowledge-chunk-detail", selectedChunkId],
    queryFn: () => knowledgeApi.getChunk(selectedChunkId as string),
    enabled: Boolean(selectedChunkId),
  });

  const retrievalDebugMutation = useMutation({
    mutationFn: () =>
      knowledgeApi.retrievalDebug({
        query_text: debugQueryText.trim(),
        top_k: Number.isFinite(Number(debugTopK)) ? Number(debugTopK) : undefined,
        metadata_filter: parseFilterInput(debugFilterJson),
      }),
    onSuccess: (response) => {
      setMessage(`检索调试完成，status=${response.status}，hits=${response.hits.length}`);
    },
    onError: (error) => setMessage(getErrorMessage(error)),
  });

  return {
    selectedDocumentId,
    setSelectedDocumentId,
    selectedChunkId,
    setSelectedChunkId,
    debugQueryText,
    setDebugQueryText,
    debugTopK,
    setDebugTopK,
    debugFilterJson,
    setDebugFilterJson,
    message,
    documents: documentsQuery.data ?? [],
    documentsLoading: documentsQuery.isLoading,
    documentsError: documentsQuery.error ? getErrorMessage(documentsQuery.error) : null,
    documentDetail: documentDetailQuery.data ?? null,
    documentDetailLoading: documentDetailQuery.isFetching,
    chunks: chunksQuery.data ?? [],
    chunksLoading: chunksQuery.isLoading || chunksQuery.isFetching,
    chunkDetail: chunkDetailQuery.data ?? null,
    chunkDetailLoading: chunkDetailQuery.isFetching,
    retrievalDebugResult: retrievalDebugMutation.data ?? null,
    retrievalDebugPending: retrievalDebugMutation.isPending,
    retrievalDebugError: retrievalDebugMutation.error
      ? getErrorMessage(retrievalDebugMutation.error)
      : null,
    runRetrievalDebug: () => retrievalDebugMutation.mutate(),
  };
}
