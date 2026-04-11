import { normalizeApiError } from "@/api/errors";
import { httpRequest } from "@/api/httpClient";
import { adaptSSEToChatStreamEvent } from "@/stream/chatStreamAdapter";
import { SSEClient } from "@/stream/sseClient";
import type {
  ChatCancelRequestPayload,
  ChatCancelResponse,
  ChatRequestPayload,
  ChatResponse,
  ChatStreamEvent,
  ChatStreamRequestPayload,
} from "@/types/chat";

type StreamCallbacks = {
  onEvent: (event: ChatStreamEvent) => void;
  onError: (error: Error) => void;
  onClose?: () => void;
};

export const chatApi = {
  sendChat(payload: ChatRequestPayload): Promise<ChatResponse> {
    return httpRequest<ChatResponse>("/chat", {
      method: "POST",
      body: payload,
    });
  },

  cancelStream(payload: ChatCancelRequestPayload): Promise<ChatCancelResponse> {
    return httpRequest<ChatCancelResponse>("/chat_stream_cancel", {
      method: "POST",
      body: payload,
    });
  },

  streamChat(
    payload: ChatStreamRequestPayload,
    callbacks: StreamCallbacks,
  ): { close: () => void } {
    const client = new SSEClient();
    return client.connect({
      path: "/chat_stream",
      method: "POST",
      body: {
        ...payload,
        stream: true,
      },
      onMessage: (message) => {
        const event = adaptSSEToChatStreamEvent(message);
        if (event) {
          callbacks.onEvent(event);
        }
      },
      onError: (error) => {
        const normalized = normalizeApiError(
          undefined,
          error,
          "SSE stream failed.",
        );
        callbacks.onError(normalized);
      },
      onClose: callbacks.onClose,
    });
  },
};
