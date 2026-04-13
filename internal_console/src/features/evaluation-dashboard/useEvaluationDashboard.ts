import { useMemo, useState } from "react";
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

const parseOptionalNumber = (value: string, fieldName: string): number | undefined => {
  const trimmed = value.trim();
  if (!trimmed) {
    return undefined;
  }
  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed)) {
    throw new Error(`${fieldName} must be numeric.`);
  }
  return parsed;
};

const parseOptionalInteger = (value: string, fieldName: string): number | undefined => {
  const parsed = parseOptionalNumber(value, fieldName);
  if (parsed === undefined) {
    return undefined;
  }
  if (!Number.isInteger(parsed)) {
    throw new Error(`${fieldName} must be integer.`);
  }
  return parsed;
};

const parseOptionalJsonObject = (
  value: string,
  fieldName: string,
): Record<string, unknown> | undefined => {
  const trimmed = value.trim();
  if (!trimmed) {
    return undefined;
  }
  try {
    const parsed = JSON.parse(trimmed) as unknown;
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error(`${fieldName} must be JSON object.`);
    }
    return parsed as Record<string, unknown>;
  } catch {
    throw new Error(`${fieldName} must be valid JSON object.`);
  }
};

export function useEvaluationDashboard() {
  const queryClient = useQueryClient();
  const [buildId, setBuildId] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [versionId, setVersionId] = useState("");
  const [runMetadataJson, setRunMetadataJson] = useState("");

  const [sampleId, setSampleId] = useState("");
  const [queryText, setQueryText] = useState("");
  const [sampleTopK, setSampleTopK] = useState("");
  const [sampleMetadataFilterJson, setSampleMetadataFilterJson] = useState("");
  const [sampleMetadataJson, setSampleMetadataJson] = useState("");

  const [expectedDocumentIds, setExpectedDocumentIds] = useState("");
  const [expectedChunkIds, setExpectedChunkIds] = useState("");
  const [retrievalMinRecall, setRetrievalMinRecall] = useState("");

  const [expectedCitationIds, setExpectedCitationIds] = useState("");
  const [expectedCitationDocumentIds, setExpectedCitationDocumentIds] = useState("");
  const [citationMinRecall, setCitationMinRecall] = useState("");
  const [citationMinPrecision, setCitationMinPrecision] = useState("");

  const [requiredTerms, setRequiredTerms] = useState("");
  const [forbiddenTerms, setForbiddenTerms] = useState("");
  const [minRequiredTermHitRatio, setMinRequiredTermHitRatio] = useState("");
  const [maxForbiddenTermHitCount, setMaxForbiddenTermHitCount] = useState("");

  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
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
        build_id: buildId.trim() || undefined,
        dataset_id: datasetId.trim() || undefined,
        version_id: versionId.trim() || undefined,
        metadata: parseOptionalJsonObject(runMetadataJson, "run metadata") ?? undefined,
      };
      if (queryText.trim()) {
        payload.samples = [
          {
            sample_id: sampleId.trim() || undefined,
            query_text: queryText.trim(),
            metadata_filter:
              parseOptionalJsonObject(sampleMetadataFilterJson, "sample metadata_filter") ??
              undefined,
            top_k: parseOptionalInteger(sampleTopK, "sample top_k"),
            retrieval_label: {
              expected_document_ids: parseCsv(expectedDocumentIds),
              expected_chunk_ids: parseCsv(expectedChunkIds),
              min_recall: parseOptionalNumber(retrievalMinRecall, "retrieval min_recall"),
            },
            citation_label: {
              expected_citation_ids: parseCsv(expectedCitationIds),
              expected_document_ids: parseCsv(expectedCitationDocumentIds),
              min_recall: parseOptionalNumber(citationMinRecall, "citation min_recall"),
              min_precision: parseOptionalNumber(citationMinPrecision, "citation min_precision"),
            },
            answer_label: {
              required_terms: parseCsv(requiredTerms),
              forbidden_terms: parseCsv(forbiddenTerms),
              min_required_term_hit_ratio: parseOptionalNumber(
                minRequiredTermHitRatio,
                "answer min_required_term_hit_ratio",
              ),
              max_forbidden_term_hit_count: parseOptionalInteger(
                maxForbiddenTermHitCount,
                "answer max_forbidden_term_hit_count",
              ),
            },
            metadata:
              parseOptionalJsonObject(sampleMetadataJson, "sample metadata") ?? undefined,
          },
        ];
      } else {
        payload.samples = [];
      }
      return evaluationApi.createRun(payload);
    },
    onSuccess: (response) => {
      setSelectedRunId(response.run_id);
      setSelectedCaseId(null);
      setMessage(`Evaluation completed: ${response.run_id}`);
      queryClient.invalidateQueries({ queryKey: ["evaluation-runs"] }).catch(() => undefined);
    },
    onError: (error) => setMessage(getErrorMessage(error)),
  });

  const runCases = runCasesQuery.data ?? [];
  const selectedCase = useMemo(() => {
    if (!selectedCaseId) {
      return null;
    }
    return runCases.find((item) => item.sample_id === selectedCaseId) ?? null;
  }, [runCases, selectedCaseId]);

  return {
    buildId,
    setBuildId,
    datasetId,
    setDatasetId,
    versionId,
    setVersionId,
    runMetadataJson,
    setRunMetadataJson,
    sampleId,
    setSampleId,
    queryText,
    setQueryText,
    sampleTopK,
    setSampleTopK,
    sampleMetadataFilterJson,
    setSampleMetadataFilterJson,
    sampleMetadataJson,
    setSampleMetadataJson,
    expectedDocumentIds,
    setExpectedDocumentIds,
    expectedChunkIds,
    setExpectedChunkIds,
    retrievalMinRecall,
    setRetrievalMinRecall,
    expectedCitationIds,
    setExpectedCitationIds,
    expectedCitationDocumentIds,
    setExpectedCitationDocumentIds,
    citationMinRecall,
    setCitationMinRecall,
    citationMinPrecision,
    setCitationMinPrecision,
    requiredTerms,
    setRequiredTerms,
    forbiddenTerms,
    setForbiddenTerms,
    minRequiredTermHitRatio,
    setMinRequiredTermHitRatio,
    maxForbiddenTermHitCount,
    setMaxForbiddenTermHitCount,
    selectedRunId,
    setSelectedRunId,
    selectedCaseId,
    setSelectedCaseId,
    selectedCase,
    message,
    runs: runsQuery.data ?? [],
    runsLoading: runsQuery.isLoading,
    runsError: runsQuery.error ? getErrorMessage(runsQuery.error) : null,
    runDetail: runDetailQuery.data ?? null,
    runDetailLoading: runDetailQuery.isFetching,
    runCases,
    runCasesLoading: runCasesQuery.isFetching,
    createRun: () => createRunMutation.mutate(),
    createRunPending: createRunMutation.isPending,
  };
}
