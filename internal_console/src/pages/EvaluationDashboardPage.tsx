import { KeyValueTable } from "@/components/KeyValueTable";
import { useEvaluationDashboard } from "@/features/evaluation-dashboard/useEvaluationDashboard";

export function EvaluationDashboardPage(): JSX.Element {
  const {
    datasetId,
    setDatasetId,
    versionId,
    setVersionId,
    queryText,
    setQueryText,
    expectedDocumentIds,
    setExpectedDocumentIds,
    expectedChunkIds,
    setExpectedChunkIds,
    requiredTerms,
    setRequiredTerms,
    forbiddenTerms,
    setForbiddenTerms,
    selectedRunId,
    setSelectedRunId,
    message,
    runs,
    runsLoading,
    runsError,
    runDetail,
    runDetailLoading,
    runCases,
    runCasesLoading,
    createRun,
    createRunPending,
  } = useEvaluationDashboard();

  return (
    <section className="chat-grid">
      <article className="panel">
        <h2>Evaluation Dashboard</h2>
        <p className="muted">Start RAG evaluation runs and inspect failed cases.</p>
        <div className="form-grid">
          <div className="inline-grid">
            <label>
              Dataset ID (optional)
              <input value={datasetId} onChange={(event) => setDatasetId(event.target.value)} />
            </label>
            <label>
              Version ID (optional)
              <input value={versionId} onChange={(event) => setVersionId(event.target.value)} />
            </label>
          </div>
          <label>
            Query Text (optional, leave empty to auto-generate samples from documents)
            <input value={queryText} onChange={(event) => setQueryText(event.target.value)} />
          </label>
          <div className="inline-grid">
            <label>
              Expected Document IDs (CSV)
              <input
                value={expectedDocumentIds}
                onChange={(event) => setExpectedDocumentIds(event.target.value)}
              />
            </label>
            <label>
              Expected Chunk IDs (CSV)
              <input
                value={expectedChunkIds}
                onChange={(event) => setExpectedChunkIds(event.target.value)}
              />
            </label>
          </div>
          <div className="inline-grid">
            <label>
              Required Terms (CSV)
              <input
                value={requiredTerms}
                onChange={(event) => setRequiredTerms(event.target.value)}
              />
            </label>
            <label>
              Forbidden Terms (CSV)
              <input
                value={forbiddenTerms}
                onChange={(event) => setForbiddenTerms(event.target.value)}
              />
            </label>
          </div>
        </div>
        <div className="button-row">
          <button type="button" className="accent" disabled={createRunPending} onClick={createRun}>
            {createRunPending ? "Running..." : "Start Evaluation Run"}
          </button>
        </div>
        <p className="message">{message}</p>
        {runsError ? <p className="error-text">{runsError}</p> : null}
      </article>

      <article className="panel">
        <h3>Run List</h3>
        {runsLoading ? <p className="muted">Loading runs...</p> : null}
        {!runsLoading && runs.length === 0 ? <p className="muted">No runs.</p> : null}
        {runs.length > 0 ? (
          <ul className="simple-list">
            {runs.map((run) => (
              <li key={run.run_id}>
                <button
                  type="button"
                  className={selectedRunId === run.run_id ? "list-button active" : "list-button"}
                  onClick={() => setSelectedRunId(run.run_id)}
                >
                  <strong>{run.run_id}</strong>
                  <small>
                    dataset={run.dataset_id ?? "-"} version={run.dataset_version_id ?? "-"}
                  </small>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </article>

      <article className="panel">
        <h3>Run Cases</h3>
        {runCasesLoading ? <p className="muted">Loading cases...</p> : null}
        {!runCasesLoading && runCases.length === 0 ? (
          <p className="muted">Select a run to inspect cases.</p>
        ) : null}
        {runCases.length > 0 ? (
          <ul className="simple-list">
            {runCases.map((caseItem) => (
              <li key={caseItem.sample_id}>
                <div className={caseItem.passed ? "case-item pass" : "case-item fail"}>
                  <strong>{caseItem.sample_id}</strong>
                  <small>
                    status={caseItem.retrieval_status} top_k={caseItem.resolved_top_k}
                  </small>
                  {!caseItem.passed ? <span className="badge fail">FAILED</span> : <span className="badge pass">PASSED</span>}
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </article>

      <KeyValueTable
        title="Run Summary"
        value={runDetailLoading ? { loading: true } : runDetail?.summary ?? null}
      />
      <KeyValueTable title="Run Metadata" value={runDetail?.metadata ?? null} />
    </section>
  );
}
