import { appEnvConfig } from "@/config/env";
import { normalizeApiError } from "@/api/errors";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

type HttpClientRequestOptions = {
  method?: HttpMethod;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
};

const buildUrl = (path: string): string => {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${appEnvConfig.apiBaseUrl}${normalizedPath}`;
};

const maybeParseJson = async (response: Response): Promise<unknown> => {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    const plainText = await response.text();
    if (!plainText.trim()) {
      return null;
    }
    return plainText;
  }
  try {
    return await response.json();
  } catch {
    return null;
  }
};

export async function httpRequest<TResponse>(
  path: string,
  options: HttpClientRequestOptions = {},
): Promise<TResponse> {
  const { method = "GET", body, headers = {}, signal } = options;
  const response = await fetch(buildUrl(path), {
    method,
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  });

  const payload = await maybeParseJson(response);
  if (!response.ok) {
    throw normalizeApiError(
      response.status,
      payload,
      `HTTP ${response.status} request failed.`,
    );
  }
  return payload as TResponse;
}
