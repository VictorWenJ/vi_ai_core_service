import { useRuntimeConfig } from "@/features/runtime-config/useRuntimeConfig";

const formatTime = (value?: string): string => {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

export function RuntimeConfigPage(): JSX.Element {
  const { summary, configSummary, health, loading, error } = useRuntimeConfig();

  const ragConfig = configSummary?.rag ?? {};

  return (
    <section className="chat-grid">
      <article className="panel">
        <h2>Runtime / Config View</h2>
        <p className="muted">Read-only runtime summary and current system configuration baseline.</p>
        {loading ? <p className="muted">Loading runtime data...</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </article>

      <article className="panel">
        <h3>RAG Runtime Baseline</h3>
        <div className="info-grid">
          <div className="info-item">
            <span className="muted">embedding provider</span>
            <strong>{summary?.embedding_provider ?? "-"}</strong>
          </div>
          <div className="info-item">
            <span className="muted">embedding model</span>
            <strong>{summary?.embedding_model ?? "-"}</strong>
          </div>
          <div className="info-item">
            <span className="muted">embedding dimension</span>
            <strong>{String(ragConfig.embedding_dimension ?? "-")}</strong>
          </div>
          <div className="info-item">
            <span className="muted">vector collection</span>
            <strong>{String(ragConfig.qdrant_collection ?? "-")}</strong>
          </div>
          <div className="info-item">
            <span className="muted">storage root</span>
            <strong>{String(ragConfig.content_store_root ?? "-")}</strong>
          </div>
          <div className="info-item">
            <span className="muted">retrieval_top_k</span>
            <strong>{String(summary?.retrieval_top_k ?? "-")}</strong>
          </div>
        </div>
      </article>

      <article className="panel">
        <h3>Runtime Counters</h3>
        <div className="metric-grid">
          <div className="metric-card">
            <span className="muted">document_count</span>
            <strong>{summary?.document_count ?? 0}</strong>
          </div>
          <div className="metric-card">
            <span className="muted">chunk_count</span>
            <strong>{summary?.chunk_count ?? 0}</strong>
          </div>
          <div className="metric-card">
            <span className="muted">build_count</span>
            <strong>{summary?.build_count ?? 0}</strong>
          </div>
          <div className="metric-card">
            <span className="muted">evaluation_run_count</span>
            <strong>{summary?.evaluation_run_count ?? 0}</strong>
          </div>
          <div className="metric-card">
            <span className="muted">service</span>
            <strong>{summary?.service ?? "-"}</strong>
          </div>
          <div className="metric-card">
            <span className="muted">health</span>
            <strong>{health?.status ?? "-"}</strong>
          </div>
        </div>
      </article>

      <article className="panel">
        <h3>Recent Build Statuses</h3>
        {!summary?.recent_build_statuses?.length ? (
          <p className="muted">No recent build records.</p>
        ) : (
          <ul className="simple-list">
            {summary.recent_build_statuses.map((item, index) => (
              <li key={`${item.build_id ?? item.id ?? index}`} className="result-card">
                <div className="result-card-header">
                  <strong>{item.build_id ?? item.id ?? "-"}</strong>
                  <span
                    className={`badge ${
                      item.status === "succeeded"
                        ? "pass"
                        : item.status === "failed"
                          ? "fail"
                          : "neutral"
                    }`}
                  >
                    {item.status ?? "-"}
                  </span>
                </div>
                <small>started_at={formatTime(item.started_at)}</small>
                <small>completed_at={formatTime(item.completed_at)}</small>
              </li>
            ))}
          </ul>
        )}
      </article>

      <article className="panel">
        <h3>Recent Evaluation Statuses</h3>
        {!summary?.recent_evaluation_statuses?.length ? (
          <p className="muted">No recent evaluation records.</p>
        ) : (
          <ul className="simple-list">
            {summary.recent_evaluation_statuses.map((item, index) => (
              <li key={`${item.run_id ?? item.id ?? index}`} className="result-card">
                <div className="result-card-header">
                  <strong>{item.run_id ?? item.id ?? "-"}</strong>
                  <span
                    className={`badge ${
                      item.status === "succeeded"
                        ? "pass"
                        : item.status === "failed"
                          ? "fail"
                          : "neutral"
                    }`}
                  >
                    {item.status ?? "-"}
                  </span>
                </div>
                <small>started_at={formatTime(item.started_at)}</small>
                <small>completed_at={formatTime(item.completed_at)}</small>
              </li>
            ))}
          </ul>
        )}
      </article>

      <article className="panel">
        <h3>Config Snapshot</h3>
        <details open>
          <summary>RAG Config</summary>
          <pre>{JSON.stringify(configSummary?.rag ?? {}, null, 2)}</pre>
        </details>
        <details>
          <summary>Streaming Config</summary>
          <pre>{JSON.stringify(configSummary?.streaming ?? {}, null, 2)}</pre>
        </details>
        <details>
          <summary>Provider Config</summary>
          <pre>{JSON.stringify(configSummary?.providers ?? {}, null, 2)}</pre>
        </details>
        <details>
          <summary>Database Config</summary>
          <pre>{JSON.stringify(configSummary?.database ?? {}, null, 2)}</pre>
        </details>
      </article>
    </section>
  );
}
