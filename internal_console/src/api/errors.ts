export type ApiErrorShape = {
  message: string;
  status?: number;
  error_code?: string;
  detail?: unknown;
};

export class ApiClientError extends Error {
  public readonly status?: number;

  public readonly errorCode?: string;

  public readonly detail?: unknown;

  constructor(shape: ApiErrorShape) {
    super(shape.message);
    this.name = "ApiClientError";
    this.status = shape.status;
    this.errorCode = shape.error_code;
    this.detail = shape.detail;
  }
}

const readDetailMessage = (detail: unknown): string | null => {
  if (!detail) {
    return null;
  }
  if (typeof detail === "string") {
    return detail;
  }
  if (typeof detail === "object" && detail !== null) {
    const obj = detail as Record<string, unknown>;
    if (typeof obj.message === "string" && obj.message.trim()) {
      return obj.message;
    }
    if (typeof obj.error === "string" && obj.error.trim()) {
      return obj.error;
    }
    if (typeof obj.detail === "string" && obj.detail.trim()) {
      return obj.detail;
    }
  }
  return null;
};

export const normalizeApiError = (
  status: number | undefined,
  payload: unknown,
  fallbackMessage = "Request failed.",
): ApiClientError => {
  if (payload instanceof ApiClientError) {
    return payload;
  }
  if (typeof payload === "object" && payload !== null) {
    const obj = payload as Record<string, unknown>;
    const detail = obj.detail;
    const message =
      readDetailMessage(payload) ??
      readDetailMessage(detail) ??
      fallbackMessage;
    const errorCode =
      (typeof obj.error_code === "string" && obj.error_code) ||
      (typeof obj.code === "string" && obj.code) ||
      undefined;
    return new ApiClientError({
      message,
      status,
      error_code: errorCode,
      detail: payload,
    });
  }

  if (typeof payload === "string" && payload.trim()) {
    return new ApiClientError({ message: payload, status });
  }

  return new ApiClientError({ message: fallbackMessage, status, detail: payload });
};
