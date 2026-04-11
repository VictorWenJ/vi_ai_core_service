import { normalizeApiError } from "@/api/errors";
import { appEnvConfig } from "@/config/env";
import { extractSSEMessages } from "@/stream/sseParser";
import type { SSEClientConnectOptions } from "@/stream/sseTypes";

export type SSEConnection = {
  close: () => void;
};

const toAbsoluteUrl = (path: string): string => {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${appEnvConfig.apiBaseUrl}${normalizedPath}`;
};

export class SSEClient {
  connect(options: SSEClientConnectOptions): SSEConnection {
    const abortController = new AbortController();
    const externalSignal = options.signal;

    if (externalSignal) {
      externalSignal.addEventListener("abort", () => abortController.abort(), {
        once: true,
      });
    }

    void this.startStreaming(options, abortController);
    return {
      close: () => abortController.abort(),
    };
  }

  private async startStreaming(
    options: SSEClientConnectOptions,
    abortController: AbortController,
  ): Promise<void> {
    try {
      const response = await fetch(toAbsoluteUrl(options.path), {
        method: options.method ?? "GET",
        headers: {
          Accept: "text/event-stream",
          ...(options.body !== undefined ? { "Content-Type": "application/json" } : {}),
          ...(options.headers ?? {}),
        },
        body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
        signal: abortController.signal,
      });

      options.onOpen?.(response);
      if (!response.ok || !response.body) {
        const bodyText = await response.text();
        throw normalizeApiError(
          response.status,
          bodyText,
          `SSE HTTP ${response.status} failed.`,
        );
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        const { messages, remainingBuffer } = extractSSEMessages(buffer);
        buffer = remainingBuffer;
        for (const message of messages) {
          options.onMessage(message);
        }
      }
      options.onClose?.();
    } catch (error) {
      if (abortController.signal.aborted) {
        options.onClose?.();
        return;
      }
      options.onError?.(error);
    }
  }
}
