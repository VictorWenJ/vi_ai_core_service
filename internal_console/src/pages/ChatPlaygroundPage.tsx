import { KeyValueTable } from "@/components/KeyValueTable";
import { useChatPlayground } from "@/features/chat-playground/useChatPlayground";

export function ChatPlaygroundPage(): JSX.Element {
  const {
    form,
    setForm,
    sendChat,
    startStream,
    cancelStream,
    clearOutput,
    syncResponse,
    chatPending,
    cancelPending,
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
  } = useChatPlayground();

  return (
    <section className="chat-grid">
      <article className="panel">
        <h2>Chat Playground</h2>
        <p className="muted">
          Use `/chat`, `/chat_stream`, and `/chat_stream_cancel` against current backend contract.
        </p>

        <div className="form-grid">
          <label>
            User Prompt
            <textarea
              rows={6}
              value={form.userPrompt}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  userPrompt: event.target.value,
                }))
              }
              placeholder="Type your test prompt..."
            />
          </label>

          <div className="inline-grid">
            <label>
              Provider (optional)
              <input
                value={form.provider}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    provider: event.target.value,
                  }))
                }
                placeholder="openai"
              />
            </label>
            <label>
              Model (optional)
              <input
                value={form.model}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    model: event.target.value,
                  }))
                }
                placeholder="gpt-test"
              />
            </label>
          </div>

          <div className="inline-grid">
            <label>
              Temperature (optional)
              <input
                value={form.temperature}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    temperature: event.target.value,
                  }))
                }
                placeholder="0.7"
              />
            </label>
            <label>
              Max Tokens (optional)
              <input
                value={form.maxTokens}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    maxTokens: event.target.value,
                  }))
                }
                placeholder="1024"
              />
            </label>
          </div>

          <label>
            System Prompt (optional)
            <textarea
              rows={3}
              value={form.systemPrompt}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  systemPrompt: event.target.value,
                }))
              }
              placeholder="Override system prompt"
            />
          </label>

          <div className="inline-grid">
            <label>
              Session ID (optional)
              <input
                value={form.sessionId}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    sessionId: event.target.value,
                  }))
                }
                placeholder="session-1"
              />
            </label>
            <label>
              Conversation ID (optional)
              <input
                value={form.conversationId}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    conversationId: event.target.value,
                  }))
                }
                placeholder="conv-1"
              />
            </label>
          </div>

          <div className="inline-grid">
            <label>
              Request ID (optional)
              <input
                value={form.requestId}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    requestId: event.target.value,
                  }))
                }
                placeholder="req-xxx"
              />
            </label>
            <label>
              Metadata JSON (optional)
              <textarea
                rows={2}
                className="textarea-mono"
                value={form.metadataJson}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    metadataJson: event.target.value,
                  }))
                }
                placeholder='{"trace_tag":"manual-test"}'
              />
            </label>
          </div>

          <details>
            <summary>Stream Options (optional)</summary>
            <div className="form-grid">
              <div className="inline-grid">
                <label>
                  stream_heartbeat_interval_seconds
                  <input
                    value={form.streamHeartbeatIntervalSeconds}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        streamHeartbeatIntervalSeconds: event.target.value,
                      }))
                    }
                    placeholder="15"
                  />
                </label>
                <label>
                  stream_request_timeout_seconds
                  <input
                    value={form.streamRequestTimeoutSeconds}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        streamRequestTimeoutSeconds: event.target.value,
                      }))
                    }
                    placeholder="120"
                  />
                </label>
              </div>
              <div className="inline-grid">
                <label>
                  stream_emit_usage
                  <select
                    value={form.streamEmitUsage}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        streamEmitUsage: event.target.value as "" | "true" | "false",
                      }))
                    }
                  >
                    <option value="">default</option>
                    <option value="true">true</option>
                    <option value="false">false</option>
                  </select>
                </label>
                <label>
                  stream_emit_trace
                  <select
                    value={form.streamEmitTrace}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        streamEmitTrace: event.target.value as "" | "true" | "false",
                      }))
                    }
                  >
                    <option value="">default</option>
                    <option value="true">true</option>
                    <option value="false">false</option>
                  </select>
                </label>
              </div>
            </div>
          </details>

          <details>
            <summary>Cancel Override (optional)</summary>
            <div className="inline-grid">
              <label>
                request_id
                <input
                  value={form.cancelRequestId}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      cancelRequestId: event.target.value,
                    }))
                  }
                  placeholder="req-from-other-window"
                />
              </label>
              <label>
                assistant_message_id
                <input
                  value={form.cancelAssistantMessageId}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      cancelAssistantMessageId: event.target.value,
                    }))
                  }
                  placeholder="msg-assistant-xxx"
                />
              </label>
            </div>
          </details>
        </div>

        <div className="button-row">
          <button type="button" disabled={chatPending} onClick={() => void sendChat()}>
            {chatPending ? "Sending..." : "Send /chat"}
          </button>
          <button type="button" className="accent" onClick={startStream}>
            Start /chat_stream
          </button>
          <button
            type="button"
            className="danger"
            disabled={!canCancel || cancelPending}
            onClick={() => void cancelStream()}
          >
            {cancelPending ? "Cancelling..." : "Cancel Stream"}
          </button>
          <button type="button" className="ghost" onClick={clearOutput}>
            Clear
          </button>
        </div>

        <div className="status-row">
          <span>
            Stream Status: <strong>{streamStatus}</strong>
          </span>
          <span>Events: {streamEventCount}</span>
          <span>Request ID: {streamRequestId ?? "-"}</span>
          <span>Assistant Message ID: {assistantMessageId ?? "-"}</span>
        </div>
        <p className="message">{streamMessage || "Ready."}</p>
      </article>

      <article className="panel">
        <h3>/chat Content</h3>
        <pre>{syncResponse?.content || "No /chat response yet."}</pre>
      </article>

      <article className="panel">
        <h3>/chat_stream Content</h3>
        <pre>{streamText || "No stream delta yet."}</pre>
      </article>

      <article className="panel">
        <h3>Citations</h3>
        {syncResponse?.citations?.length || streamCitations.length ? (
          <ul className="citation-list">
            {[...(syncResponse?.citations ?? []), ...streamCitations].map((citation) => (
              <li key={citation.citation_id}>
                <div className="citation-head">
                  <strong>{citation.title ?? citation.document_id}</strong>
                  <code>{citation.citation_id}</code>
                </div>
                <p>{citation.snippet}</p>
                <small>
                  chunk={citation.chunk_id} origin={citation.origin_uri ?? "-"}
                </small>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No citations.</p>
        )}
      </article>

      <KeyValueTable title="Sync Metadata Summary" value={metadataSummary} />
      <KeyValueTable title="Stream Trace Summary" value={streamTrace} />
    </section>
  );
}
