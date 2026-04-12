import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiClientError } from "@/api/errors";
import { evaluationApi } from "@/api/evaluationApi";
import type { EvaluationRunCreatePayload } from "@/types/console";

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

const parseCsv = (raw: string): string[] =>
  raw
    .split(",")
    .map((segment) => segment.trim())
    .filter(Boolean);

export function useEvaluationDashboard() {
  const queryClient = useQueryClient();
  const [datasetId, setDatasetId] = useState("");
  const [versionId, setVersionId] = useState("");
  const [queryText, setQueryText] = useState("");
  const [expectedDocumentIds, setExpectedDocumentIds] = useState("");
  const [expectedChunkIds, setExpectedChunkIds] = useState("");
  const [requiredTerms, setRequiredTerms] = useState("");
  const [forbiddenTerms, setForbiddenTerms] = useState("");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [message, setMessage] = useState("Ready.");

  const runsQuery = useQuery({
    queryKey: ["evaluation-runs"],
    queryFn: () => evaluationApi.listRuns(),
  });

  const runDetailQuery = useQuery({
    queryKey: ["evaluation-run-detail", selectedRunId],
    queryFn: () => evaluationApi.getRun(selectedRunId as string),
    enabled: Boolean(selectedRunId),
  });

  const runCasesQuery = useQuery({
    queryKey: ["evaluation-run-cases", selectedRunId],
    queryFn: () => evaluationApi.listRunCases(selectedRunId as string),
    enabled: Boolean(selectedRunId),
  });

  const createRunMutation = useMutation({
    mutationFn: () => {
      const payload: EvaluationRunCreatePayload = {
        dataset_id: datasetId.trim() || undefined,
        version_id: versionId.trim() || undefined,
      };
      if (queryText.trim()) {
        payload.samples = [
          {
            sample_id: "manual-1",
            query_text: queryText.trim(),
            retrieval_label: {
              expected_document_ids: parseCsv(expectedDocumentIds),
              expected_chunk_ids: parseCsv(expectedChunkIds),
              min_recall: 1.0,
            },
            answer_label: {
              required_terms: parseCsv(requiredTerms),
              forbidden_terms: parseCsv(forbiddenTerms),
              min_required_term_hit_ratio: 1.0,
              max_forbidden_term_hit_count: 0,
            },
          },
        ];
      } else {
        payload.samples = [];
      }
      return evaluationApi.createRun(payload);
    },
    onSuccess: (response) => {
      setSelectedRunId(response.run_id);
      setMessage(`评估完成：${response.run_id}`);
      queryClient.invalidateQueries({ queryKey: ["evaluation-runs"] }).catch(() => undefined);
    },
    onError: (error) => setMessage(getErrorMessage(error)),
  });

  return {
    datasetId,
    setDatasetId,
    versionId,
    setVersionId,
    queryText,
    setQueryText,
    expectedDocumentIds,
    setExpectedDocumentIds,
    expectedChunkIds,
    setExpectedChunkIds,
    requiredTerms,
    setRequiredTerms,
    forbiddenTerms,
    setForbiddenTerms,
    selectedRunId,
    setSelectedRunId,
    message,
    runs: runsQuery.data ?? [],
    runsLoading: runsQuery.isLoading,
    runsError: runsQuery.error ? getErrorMessage(runsQuery.error) : null,
    runDetail: runDetailQuery.data ?? null,
    runDetailLoading: runDetailQuery.isFetching,
    runCases: runCasesQuery.data ?? [],
    runCasesLoading: runCasesQuery.isFetching,
    createRun: () => createRunMutation.mutate(),
    createRunPending: createRunMutation.isPending,
  };
}
