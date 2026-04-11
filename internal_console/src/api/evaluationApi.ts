import { httpRequest } from "@/api/httpClient";
import type {
  EvaluationRunCase,
  EvaluationRunCreatePayload,
  EvaluationRunSummary,
} from "@/types/console";

export const evaluationApi = {
  createRun(payload: EvaluationRunCreatePayload): Promise<EvaluationRunSummary> {
    return httpRequest<EvaluationRunSummary>("/evaluation/rag/runs", {
      method: "POST",
      body: payload,
    });
  },

  listRuns(): Promise<EvaluationRunSummary[]> {
    return httpRequest<EvaluationRunSummary[]>("/evaluation/rag/runs");
  },

  getRun(runId: string): Promise<EvaluationRunSummary> {
    return httpRequest<EvaluationRunSummary>(`/evaluation/rag/runs/${runId}`);
  },

  listRunCases(runId: string): Promise<EvaluationRunCase[]> {
    return httpRequest<EvaluationRunCase[]>(`/evaluation/rag/runs/${runId}/cases`);
  },
};
