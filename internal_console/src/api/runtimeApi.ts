import { httpRequest } from "@/api/httpClient";
import type {
  RuntimeConfigSummary,
  RuntimeHealth,
  RuntimeSummary,
} from "@/types/console";

export const runtimeApi = {
  getSummary(): Promise<RuntimeSummary> {
    return httpRequest<RuntimeSummary>("/runtime/summary");
  },

  getConfigSummary(): Promise<RuntimeConfigSummary> {
    return httpRequest<RuntimeConfigSummary>("/runtime/config-summary");
  },

  getHealth(): Promise<RuntimeHealth> {
    return httpRequest<RuntimeHealth>("/runtime/health");
  },
};
