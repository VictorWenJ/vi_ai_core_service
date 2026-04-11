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
          Use `/chat`, `/chat_stream`, and `/chat_stream_cancel` against current
          backend contract.
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
            disabled={!streamRequestId || cancelPending}
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
