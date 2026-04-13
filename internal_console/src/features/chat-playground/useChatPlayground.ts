import { useMutation } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";

import { chatApi } from "@/api/chatApi";
import { ApiClientError } from "@/api/errors";
import type {
  ChatCitation,
  ChatRequestPayload,
  ChatResponse,
  ChatStreamEvent,
  ChatStreamRequestPayload,
  StreamStatus,
} from "@/types/chat";

type FormState = {
  userPrompt: string;
  provider: string;
  model: string;
  temperature: string;
  maxTokens: string;
  systemPrompt: string;
  sessionId: string;
  conversationId: string;
  requestId: string;
  metadataJson: string;
  streamHeartbeatIntervalSeconds: string;
  streamRequestTimeoutSeconds: string;
  streamEmitUsage: "" | "true" | "false";
  streamEmitTrace: "" | "true" | "false";
  cancelRequestId: string;
  cancelAssistantMessageId: string;
};

const initialFormState: FormState = {
  userPrompt: "",
  provider: "",
  model: "",
  temperature: "",
  maxTokens: "",
  systemPrompt: "",
  sessionId: "",
  conversationId: "",
  requestId: "",
  metadataJson: "",
  streamHeartbeatIntervalSeconds: "",
  streamRequestTimeoutSeconds: "",
  streamEmitUsage: "",
  streamEmitTrace: "",
  cancelRequestId: "",
  cancelAssistantMessageId: "",
};

const trimOrUndefined = (value: string): string | undefined => {
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
};

const parseOptionalNumber = (
  value: string,
  fieldName: string,
): number | undefined => {
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

const parseOptionalInt = (value: string, fieldName: string): number | undefined => {
  const parsed = parseOptionalNumber(value, fieldName);
  if (parsed === undefined) {
    return undefined;
  }
  if (!Number.isInteger(parsed)) {
    throw new Error(`${fieldName} must be an integer.`);
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
      throw new Error(`${fieldName} must be a JSON object.`);
    }
    return parsed as Record<string, unknown>;
  } catch {
    throw new Error(`${fieldName} must be valid JSON object.`);
  }
};

const parseTriStateBoolean = (value: "" | "true" | "false"): boolean | undefined => {
  if (value === "") {
    return undefined;
  }
  return value === "true";
};

const buildPayloadFromForm = (form: FormState): ChatRequestPayload => ({
  user_prompt: form.userPrompt.trim(),
  provider: trimOrUndefined(form.provider),
  model: trimOrUndefined(form.model),
  temperature: parseOptionalNumber(form.temperature, "temperature"),
  max_tokens: parseOptionalInt(form.maxTokens, "max_tokens"),
  system_prompt: trimOrUndefined(form.systemPrompt),
  session_id: trimOrUndefined(form.sessionId),
  conversation_id: trimOrUndefined(form.conversationId),
  request_id: trimOrUndefined(form.requestId),
  metadata: parseOptionalJsonObject(form.metadataJson, "metadata"),
});

const buildStreamPayloadFromForm = (form: FormState): ChatStreamRequestPayload => {
  const basePayload = buildPayloadFromForm(form);
  const streamHeartbeat = parseOptionalNumber(
    form.streamHeartbeatIntervalSeconds,
    "stream_heartbeat_interval_seconds",
  );
  const streamTimeout = parseOptionalNumber(
    form.streamRequestTimeoutSeconds,
    "stream_request_timeout_seconds",
  );
  const streamEmitUsage = parseTriStateBoolean(form.streamEmitUsage);
  const streamEmitTrace = parseTriStateBoolean(form.streamEmitTrace);

  const streamOptions =
    streamHeartbeat !== undefined ||
    streamTimeout !== undefined ||
    streamEmitUsage !== undefined ||
    streamEmitTrace !== undefined
      ? {
          stream_heartbeat_interval_seconds: streamHeartbeat,
          stream_request_timeout_seconds: streamTimeout,
          stream_emit_usage: streamEmitUsage,
          stream_emit_trace: streamEmitTrace,
        }
      : undefined;

  return {
    ...basePayload,
    stream: true,
    stream_options: streamOptions,
  };
};

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

export function useChatPlayground() {
  const [form, setForm] = useState<FormState>(initialFormState);
  const [syncResponse, setSyncResponse] = useState<ChatResponse | null>(null);
  const [streamStatus, setStreamStatus] = useState<StreamStatus>("idle");
  const [streamText, setStreamText] = useState("");
  const [streamCitations, setStreamCitations] = useState<ChatCitation[]>([]);
  const [streamTrace, setStreamTrace] = useState<Record<string, unknown> | null>(
    null,
  );
  const [streamMessage, setStreamMessage] = useState<string>("");
  const [streamRequestId, setStreamRequestId] = useState<string | undefined>(undefined);
  const [assistantMessageId, setAssistantMessageId] = useState<string | undefined>(undefined);
  const [streamEventCount, setStreamEventCount] = useState(0);

  const activeConnectionRef = useRef<{ close: () => void } | null>(null);
  const streamStatusRef = useRef<StreamStatus>("idle");

  const updateStreamStatus = (nextStatus: StreamStatus) => {
    streamStatusRef.current = nextStatus;
    setStreamStatus(nextStatus);
  };

  const chatMutation = useMutation({
    mutationFn: (payload: ChatRequestPayload) => chatApi.sendChat(payload),
    onSuccess: (response) => {
      setSyncResponse(response);
      setStreamMessage("/chat request succeeded.");
    },
    onError: (error) => {
      setStreamMessage(getErrorMessage(error));
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () => {
      const requestId = trimOrUndefined(form.cancelRequestId) ?? streamRequestId;
      const resolvedAssistantMessageId =
        trimOrUndefined(form.cancelAssistantMessageId) ?? assistantMessageId;
      return chatApi.cancelStream({
        request_id: requestId,
        assistant_message_id: resolvedAssistantMessageId,
        session_id: trimOrUndefined(form.sessionId),
        conversation_id: trimOrUndefined(form.conversationId),
      });
    },
    onSuccess: (response) => {
      setStreamMessage(
        response.cancelled
          ? "Cancel request submitted."
          : response.already_cancelled
            ? "Stream is already cancelled."
            : "No active stream matched cancellation conditions.",
      );
    },
    onError: (error) => {
      setStreamMessage(getErrorMessage(error));
    },
  });

  const stopStream = () => {
    activeConnectionRef.current?.close();
    activeConnectionRef.current = null;
  };

  useEffect(() => () => stopStream(), []);

  const handleStreamEvent = (event: ChatStreamEvent) => {
    setStreamEventCount((count) => count + 1);
    if (event.event === "response.started") {
      updateStreamStatus("started");
      setStreamRequestId(event.data.request_id);
      setAssistantMessageId(event.data.assistant_message_id);
      setStreamMessage("Stream started.");
      return;
    }
    if (event.event === "response.delta") {
      updateStreamStatus("delta");
      setStreamText((current) => `${current}${event.data.delta}`);
      return;
    }
    if (event.event === "response.heartbeat") {
      updateStreamStatus("heartbeat");
      setStreamMessage("Heartbeat received.");
      return;
    }
    if (event.event === "response.completed") {
      updateStreamStatus("completed");
      setStreamCitations(event.data.citations ?? []);
      setStreamTrace((event.data.trace ?? null) as Record<string, unknown> | null);
      setStreamMessage(
        `Stream completed: finish_reason=${event.data.finish_reason ?? "unknown"}`,
      );
      stopStream();
      return;
    }
    if (event.event === "response.cancelled") {
      updateStreamStatus("cancelled");
      setStreamTrace((event.data.trace ?? null) as Record<string, unknown> | null);
      setStreamMessage("Stream cancelled.");
      stopStream();
      return;
    }
    if (event.event === "response.error") {
      updateStreamStatus("error");
      setStreamTrace((event.data.trace ?? null) as Record<string, unknown> | null);
      setStreamMessage(`Stream error: ${event.data.error_code} - ${event.data.message}`);
      stopStream();
    }
  };

  const sendChat = async () => {
    if (!form.userPrompt.trim()) {
      setStreamMessage("Please input user prompt.");
      return;
    }
    try {
      await chatMutation.mutateAsync(buildPayloadFromForm(form));
    } catch {
      // onError handles user-facing message.
    }
  };

  const startStream = () => {
    if (!form.userPrompt.trim()) {
      setStreamMessage("Please input user prompt.");
      return;
    }
    let streamPayload: ChatStreamRequestPayload;
    try {
      streamPayload = buildStreamPayloadFromForm(form);
    } catch (error) {
      setStreamMessage(getErrorMessage(error));
      return;
    }

    stopStream();
    updateStreamStatus("idle");
    setStreamText("");
    setStreamCitations([]);
    setStreamTrace(null);
    setStreamRequestId(undefined);
    setAssistantMessageId(undefined);
    setStreamEventCount(0);
    setStreamMessage("Connecting /chat_stream ...");

    const connection = chatApi.streamChat(streamPayload, {
      onEvent: handleStreamEvent,
      onError: (error) => {
        updateStreamStatus("error");
        setStreamMessage(getErrorMessage(error));
        stopStream();
      },
      onClose: () => {
        const terminalStatus = streamStatusRef.current;
        if (terminalStatus !== "completed" && terminalStatus !== "cancelled") {
          setStreamMessage("Stream connection closed.");
        }
      },
    });
    activeConnectionRef.current = connection;
  };

  const canCancel = Boolean(
    streamRequestId ||
      assistantMessageId ||
      trimOrUndefined(form.cancelRequestId) ||
      trimOrUndefined(form.cancelAssistantMessageId),
  );

  const cancelStream = async () => {
    if (!canCancel) {
      setStreamMessage("request_id or assistant_message_id is required for cancellation.");
      return;
    }
    await cancelMutation.mutateAsync();
  };

  const clearOutput = () => {
    stopStream();
    setSyncResponse(null);
    updateStreamStatus("idle");
    setStreamText("");
    setStreamCitations([]);
    setStreamTrace(null);
    setStreamMessage("");
    setStreamRequestId(undefined);
    setAssistantMessageId(undefined);
    setStreamEventCount(0);
  };

  const metadataSummary = useMemo(() => syncResponse?.metadata ?? null, [syncResponse]);

  return {
    form,
    setForm,
    sendChat,
    startStream,
    cancelStream,
    clearOutput,
    syncResponse,
    chatPending: chatMutation.isPending,
    cancelPending: cancelMutation.isPending,
    canCancel,
    streamStatus,
    streamText,
    streamCitations,
    streamTrace,
    streamRequestId,
    assistantMessageId,
    streamMessage,
    streamEventCount,
    metadataSummary,
  };
}
