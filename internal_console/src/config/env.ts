export type AppEnvConfig = {
  apiBaseUrl: string;
};

const normalizeBaseUrl = (value: string): string => {
  const trimmed = value.trim();
  if (!trimmed) {
    return "http://localhost:8000";
  }
  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
};

export const appEnvConfig: AppEnvConfig = {
  apiBaseUrl: normalizeBaseUrl(
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  ),
};
