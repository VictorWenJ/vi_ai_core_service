import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiClientError } from "@/api/errors";
import { knowledgeApi } from "@/api/knowledgeApi";
import { runtimeApi } from "@/api/runtimeApi";
import type { BuildCreatePayload } from "@/types/console";

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

const parseOptionalNumber = (value: string): number | undefined => {
  const trimmed = value.trim();
  if (!trimmed) {
    return undefined;
  }
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const parseCsvIds = (rawValue: string): string[] =>
  rawValue
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

export function useKnowledgeIngest() {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [originUri, setOriginUri] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [jurisdiction, setJurisdiction] = useState("");
  const [domain, setDomain] = useState("");
  const [tags, setTags] = useState("");
  const [versionId, setVersionId] = useState("");
  const [forceRebuildDocumentIds, setForceRebuildDocumentIds] = useState("");
  const [maxFailureRatio, setMaxFailureRatio] = useState("");
  const [maxEmptyChunkRatio, setMaxEmptyChunkRatio] = useState("");
  const [selectedBuildId, setSelectedBuildId] = useState<string | null>(null);
  const [message, setMessage] = useState("Ready.");

  const buildsQuery = useQuery({
    queryKey: ["knowledge-builds"],
    queryFn: () => knowledgeApi.listBuilds(),
  });

  const buildDetailQuery = useQuery({
    queryKey: ["knowledge-build-detail", selectedBuildId],
    queryFn: () => knowledgeApi.getBuild(selectedBuildId as string),
    enabled: Boolean(selectedBuildId),
  });

  const runtimeSummaryQuery = useQuery({
    queryKey: ["runtime-summary"],
    queryFn: () => runtimeApi.getSummary(),
  });

  const runtimeConfigQuery = useQuery({
    queryKey: ["runtime-config-summary"],
    queryFn: () => runtimeApi.getConfigSummary(),
  });

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!selectedFile) {
        throw new Error("Please select a file to upload.");
      }
      return knowledgeApi.uploadDocument(selectedFile, {
        title,
        document_id: documentId,
        origin_uri: originUri,
        source_type: sourceType,
        jurisdiction,
        domain,
        tags,
      });
    },
    onSuccess: (response) => {
      setMessage(`Upload succeeded: ${response.document_id}`);
      queryClient.invalidateQueries({ queryKey: ["knowledge-documents"] }).catch(() => undefined);
    },
    onError: (error) => setMessage(getErrorMessage(error)),
  });

  const buildMutation = useMutation({
    mutationFn: () => {
      const rebuiltIds = parseCsvIds(forceRebuildDocumentIds);
      const payload: BuildCreatePayload = {
        version_id: versionId.trim() || undefined,
        force_rebuild_document_ids: rebuiltIds.length > 0 ? rebuiltIds : undefined,
        max_failure_ratio: parseOptionalNumber(maxFailureRatio),
        max_empty_chunk_ratio: parseOptionalNumber(maxEmptyChunkRatio),
      };
      return knowledgeApi.createBuild(payload);
    },
    onSuccess: (result) => {
      setMessage(`Build completed: ${result.metadata.build_id}`);
      setSelectedBuildId(result.metadata.build_id);
      queryClient.invalidateQueries({ queryKey: ["knowledge-builds"] }).catch(() => undefined);
      queryClient.invalidateQueries({ queryKey: ["knowledge-documents"] }).catch(() => undefined);
      queryClient.invalidateQueries({ queryKey: ["runtime-summary"] }).catch(() => undefined);
    },
    onError: (error) => setMessage(getErrorMessage(error)),
  });

  const latestBuild = useMemo(() => buildsQuery.data?.[0] ?? null, [buildsQuery.data]);
  const runtimeError = runtimeSummaryQuery.error
    ? getErrorMessage(runtimeSummaryQuery.error)
    : runtimeConfigQuery.error
      ? getErrorMessage(runtimeConfigQuery.error)
      : null;

  return {
    selectedFile,
    setSelectedFile,
    title,
    setTitle,
    documentId,
    setDocumentId,
    originUri,
    setOriginUri,
    sourceType,
    setSourceType,
    jurisdiction,
    setJurisdiction,
    domain,
    setDomain,
    tags,
    setTags,
    versionId,
    setVersionId,
    forceRebuildDocumentIds,
    setForceRebuildDocumentIds,
    maxFailureRatio,
    setMaxFailureRatio,
    maxEmptyChunkRatio,
    setMaxEmptyChunkRatio,
    selectedBuildId,
    setSelectedBuildId,
    message,
    setMessage,
    builds: buildsQuery.data ?? [],
    buildsLoading: buildsQuery.isLoading,
    buildsError: buildsQuery.error ? getErrorMessage(buildsQuery.error) : null,
    buildDetail: buildDetailQuery.data ?? null,
    buildDetailLoading: buildDetailQuery.isFetching,
    latestBuild,
    runtimeSummary: runtimeSummaryQuery.data ?? null,
    runtimeConfig: runtimeConfigQuery.data ?? null,
    runtimeLoading: runtimeSummaryQuery.isFetching || runtimeConfigQuery.isFetching,
    runtimeError,
    uploadDocument: () => uploadMutation.mutate(),
    uploadPending: uploadMutation.isPending,
    triggerBuild: () => buildMutation.mutate(),
    buildPending: buildMutation.isPending,
  };
}
