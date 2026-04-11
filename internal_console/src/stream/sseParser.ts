import type { SSEMessage } from "@/stream/sseTypes";

const parseRetry = (value: string): number | undefined => {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed) || parsed < 0) {
    return undefined;
  }
  return parsed;
};

const parseSSEBlock = (rawBlock: string): SSEMessage | null => {
  const lines = rawBlock.split(/\r?\n/);
  let event = "message";
  let dataParts: string[] = [];
  let id: string | undefined;
  let retry: number | undefined;

  for (const line of lines) {
    if (!line || line.startsWith(":")) {
      continue;
    }
    const separatorIndex = line.indexOf(":");
    const field = separatorIndex >= 0 ? line.slice(0, separatorIndex) : line;
    let value = separatorIndex >= 0 ? line.slice(separatorIndex + 1) : "";
    if (value.startsWith(" ")) {
      value = value.slice(1);
    }

    if (field === "event") {
      event = value || "message";
    } else if (field === "data") {
      dataParts.push(value);
    } else if (field === "id") {
      id = value;
    } else if (field === "retry") {
      retry = parseRetry(value);
    }
  }

  if (dataParts.length === 0) {
    return null;
  }
  return {
    event,
    data: dataParts.join("\n"),
    id,
    retry,
  };
};

export const extractSSEMessages = (buffer: string): {
  messages: SSEMessage[];
  remainingBuffer: string;
} => {
  const messages: SSEMessage[] = [];
  let workingBuffer = buffer;

  while (true) {
    const delimiterIndex = workingBuffer.search(/\r?\n\r?\n/);
    if (delimiterIndex < 0) {
      break;
    }
    const block = workingBuffer.slice(0, delimiterIndex);
    const consumedLength = block.length + (workingBuffer[delimiterIndex] === "\r" ? 4 : 2);
    workingBuffer = workingBuffer.slice(consumedLength);
    const parsed = parseSSEBlock(block);
    if (parsed) {
      messages.push(parsed);
    }
  }

  return {
    messages,
    remainingBuffer: workingBuffer,
  };
};
