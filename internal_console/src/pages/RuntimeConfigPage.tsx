import { KeyValueTable } from "@/components/KeyValueTable";
import { useRuntimeConfig } from "@/features/runtime-config/useRuntimeConfig";

export function RuntimeConfigPage(): JSX.Element {
  const { summary, configSummary, health, loading, error } = useRuntimeConfig();

  return (
    <section className="chat-grid">
      <article className="panel">
        <h2>Runtime / Config View</h2>
        <p className="muted">Read-only runtime summary and safe config snapshot.</p>
        {loading ? <p className="muted">Loading runtime data...</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </article>

      <KeyValueTable title="Runtime Summary" value={summary} />
      <KeyValueTable title="Config Summary" value={configSummary} />
      <KeyValueTable title="Health Summary" value={health} />
    </section>
  );
}
