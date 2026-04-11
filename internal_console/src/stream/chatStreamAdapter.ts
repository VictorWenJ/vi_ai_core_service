import type { SSEMessage } from "@/stream/sseTypes";
import type {
  ChatStreamEvent,
  ChatStreamCancelledEventData,
  ChatStreamCompletedEventData,
  ChatStreamDeltaEventData,
  ChatStreamErrorEventData,
  ChatStreamHeartbeatEventData,
  ChatStreamStartedEventData,
} from "@/types/chat";

const parseEventData = <T>(raw: string): T | null => {
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
};

export const adaptSSEToChatStreamEvent = (
  message: SSEMessage,
): ChatStreamEvent | null => {
  if (message.event === "response.started") {
    const data = parseEventData<ChatStreamStartedEventData>(message.data);
    if (!data) {
      return null;
    }
    return { event: "response.started", data };
  }

  if (message.event === "response.delta") {
    const data = parseEventData<ChatStreamDeltaEventData>(message.data);
    if (!data) {
      return null;
    }
    return { event: "response.delta", data };
  }

  if (message.event === "response.heartbeat") {
    const data = parseEventData<ChatStreamHeartbeatEventData>(message.data);
    if (!data) {
      return null;
    }
    return { event: "response.heartbeat", data };
  }

  if (message.event === "response.completed") {
    const data = parseEventData<ChatStreamCompletedEventData>(message.data);
    if (!data) {
      return null;
    }
    return { event: "response.completed", data };
  }

  if (message.event === "response.cancelled") {
    const data = parseEventData<ChatStreamCancelledEventData>(message.data);
    if (!data) {
      return null;
    }
    return { event: "response.cancelled", data };
  }

  if (message.event === "response.error") {
    const data = parseEventData<ChatStreamErrorEventData>(message.data);
    if (!data) {
      return null;
    }
    return { event: "response.error", data };
  }

  return null;
};
