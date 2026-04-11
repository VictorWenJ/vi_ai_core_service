export type SSEMessage = {
  event: string;
  data: string;
  id?: string;
  retry?: number;
};

export type SSEClientConnectOptions = {
  path: string;
  method?: "GET" | "POST";
  body?: unknown;
  signal?: AbortSignal;
  headers?: Record<string, string>;
  onOpen?: (response: Response) => void;
  onMessage: (message: SSEMessage) => void;
  onError?: (error: unknown) => void;
  onClose?: () => void;
};
