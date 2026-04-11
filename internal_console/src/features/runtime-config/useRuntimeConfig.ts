import { useQuery } from "@tanstack/react-query";

import { ApiClientError } from "@/api/errors";
import { runtimeApi } from "@/api/runtimeApi";

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

export function useRuntimeConfig() {
  const summaryQuery = useQuery({
    queryKey: ["runtime-summary"],
    queryFn: () => runtimeApi.getSummary(),
  });

  const configQuery = useQuery({
    queryKey: ["runtime-config-summary"],
    queryFn: () => runtimeApi.getConfigSummary(),
  });

  const healthQuery = useQuery({
    queryKey: ["runtime-health"],
    queryFn: () => runtimeApi.getHealth(),
  });

  return {
    summary: summaryQuery.data ?? null,
    configSummary: configQuery.data ?? null,
    health: healthQuery.data ?? null,
    loading: summaryQuery.isLoading || configQuery.isLoading || healthQuery.isLoading,
    error: summaryQuery.error
      ? getErrorMessage(summaryQuery.error)
      : configQuery.error
        ? getErrorMessage(configQuery.error)
        : healthQuery.error
          ? getErrorMessage(healthQuery.error)
          : null,
  };
}
