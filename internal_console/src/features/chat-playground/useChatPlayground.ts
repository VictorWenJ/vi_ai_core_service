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
  sessionId: string;
  conversationId: string;
};

const initialFormState: FormState = {
  userPrompt: "",
  provider: "",
  model: "",
  sessionId: "",
  conversationId: "",
};

const trimOrUndefined = (value: string): string | undefined => {
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
};

const buildPayloadFromForm = (form: FormState): ChatRequestPayload => ({
  user_prompt: form.userPrompt.trim(),
  provider: trimOrUndefined(form.provider),
  model: trimOrUndefined(form.model),
  session_id: trimOrUndefined(form.sessionId),
  conversation_id: trimOrUndefined(form.conversationId),
});

const buildStreamPayloadFromForm = (form: FormState): ChatStreamRequestPayload => ({
  ...buildPayloadFromForm(form),
  stream: true,
});

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
  const [streamRequestId, setStreamRequestId] = useState<string | undefined>(
    undefined,
  );
  const [assistantMessageId, setAssistantMessageId] = useState<
    string | undefined
  >(undefined);
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
      setStreamMessage("`/chat` 请求成功。");
    },
    onError: (error) => {
      setStreamMessage(getErrorMessage(error));
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () =>
      chatApi.cancelStream({
        request_id: streamRequestId,
        assistant_message_id: assistantMessageId,
        session_id: trimOrUndefined(form.sessionId),
        conversation_id: trimOrUndefined(form.conversationId),
      }),
    onSuccess: (response) => {
      setStreamMessage(
        response.cancelled
          ? "取消请求已提交。"
          : response.already_cancelled
            ? "流已取消，无需重复取消。"
            : "未找到可取消的流。",
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
      setStreamMessage("流式会话已开始。");
      return;
    }
    if (event.event === "response.delta") {
      updateStreamStatus("delta");
      setStreamText((current) => `${current}${event.data.delta}`);
      return;
    }
    if (event.event === "response.heartbeat") {
      updateStreamStatus("heartbeat");
      setStreamMessage("收到 heartbeat。");
      return;
    }
    if (event.event === "response.completed") {
      updateStreamStatus("completed");
      setStreamCitations(event.data.citations ?? []);
      setStreamTrace((event.data.trace ?? null) as Record<string, unknown> | null);
      setStreamMessage(
        `流式完成，finish_reason=${event.data.finish_reason ?? "unknown"}`,
      );
      stopStream();
      return;
    }
    if (event.event === "response.cancelled") {
      updateStreamStatus("cancelled");
      setStreamTrace((event.data.trace ?? null) as Record<string, unknown> | null);
      setStreamMessage("流式会话已取消。");
      stopStream();
      return;
    }
    if (event.event === "response.error") {
      updateStreamStatus("error");
      setStreamTrace((event.data.trace ?? null) as Record<string, unknown> | null);
      setStreamMessage(
        `流式错误：${event.data.error_code} - ${event.data.message}`,
      );
      stopStream();
    }
  };

  const sendChat = async () => {
    if (!form.userPrompt.trim()) {
      setStreamMessage("请输入 user prompt。");
      return;
    }
    await chatMutation.mutateAsync(buildPayloadFromForm(form));
  };

  const startStream = () => {
    if (!form.userPrompt.trim()) {
      setStreamMessage("请输入 user prompt。");
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
    setStreamMessage("正在连接 `/chat_stream` ...");

    const connection = chatApi.streamChat(buildStreamPayloadFromForm(form), {
      onEvent: handleStreamEvent,
      onError: (error) => {
        updateStreamStatus("error");
        setStreamMessage(getErrorMessage(error));
        stopStream();
      },
      onClose: () => {
        const terminalStatus = streamStatusRef.current;
        if (terminalStatus !== "completed" && terminalStatus !== "cancelled") {
          setStreamMessage("流连接已关闭。");
        }
      },
    });
    activeConnectionRef.current = connection;
  };

  const cancelStream = async () => {
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

  const metadataSummary = useMemo(
    () => syncResponse?.metadata ?? null,
    [syncResponse],
  );

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
