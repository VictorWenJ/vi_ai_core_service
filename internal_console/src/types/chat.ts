export type ChatRequestPayload = {
  user_prompt: string;
  provider?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
  session_id?: string;
  conversation_id?: string;
  request_id?: string;
  metadata?: Record<string, unknown>;
};

export type ChatStreamRequestPayload = ChatRequestPayload & {
  stream?: true;
  stream_options?: {
    stream_heartbeat_interval_seconds?: number;
    stream_request_timeout_seconds?: number;
    stream_emit_usage?: boolean;
    stream_emit_trace?: boolean;
  };
};

export type ChatCancelRequestPayload = {
  request_id?: string;
  assistant_message_id?: string;
  session_id?: string;
  conversation_id?: string;
};

export type ChatCancelResponse = {
  found: boolean;
  cancelled: boolean;
  already_cancelled?: boolean;
  request_id?: string;
  assistant_message_id?: string;
  session_id?: string;
  conversation_id?: string;
};

export type ChatUsage = {
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  total_tokens?: number | null;
};

export type ChatCitation = {
  citation_id: string;
  document_id: string;
  chunk_id: string;
  title?: string | null;
  snippet: string;
  origin_uri?: string | null;
  source_type?: string | null;
  updated_at?: string | null;
  metadata?: Record<string, unknown>;
};

export type ChatResponse = {
  content: string;
  provider: string;
  model?: string | null;
  usage?: ChatUsage | null;
  finish_reason?: string | null;
  metadata: Record<string, unknown>;
  raw_response?: Record<string, unknown> | null;
  citations: ChatCitation[];
};

export type StreamStatus =
  | "idle"
  | "started"
  | "delta"
  | "heartbeat"
  | "completed"
  | "cancelled"
  | "error";

export type ChatStreamStartedEventData = {
  request_id: string;
  session_id?: string | null;
  conversation_id?: string | null;
  assistant_message_id: string;
  provider?: string | null;
  model?: string | null;
  created_at?: string;
};

export type ChatStreamDeltaEventData = {
  request_id: string;
  assistant_message_id: string;
  delta: string;
  sequence: number;
};

export type ChatStreamHeartbeatEventData = {
  request_id: string;
  assistant_message_id: string;
  ts?: string;
};

export type ChatStreamCompletedEventData = {
  request_id: string;
  assistant_message_id: string;
  status: "completed";
  finish_reason?: string;
  usage?: ChatUsage | null;
  latency_ms?: number;
  citations?: ChatCitation[];
  trace?: Record<string, unknown> | null;
};

export type ChatStreamCancelledEventData = {
  request_id: string;
  assistant_message_id: string;
  status: "cancelled";
  partial_output_chars?: number;
  trace?: Record<string, unknown> | null;
};

export type ChatStreamErrorEventData = {
  request_id?: string;
  assistant_message_id?: string;
  status: "failed";
  error_code: string;
  message: string;
  trace?: Record<string, unknown> | null;
};

export type ChatStreamEvent =
  | { event: "response.started"; data: ChatStreamStartedEventData }
  | { event: "response.delta"; data: ChatStreamDeltaEventData }
  | { event: "response.heartbeat"; data: ChatStreamHeartbeatEventData }
  | { event: "response.completed"; data: ChatStreamCompletedEventData }
  | { event: "response.cancelled"; data: ChatStreamCancelledEventData }
  | { event: "response.error"; data: ChatStreamErrorEventData };
