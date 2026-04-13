import { useMemo } from "react";

import { useEvaluationDashboard } from "@/features/evaluation-dashboard/useEvaluationDashboard";

const formatPercent = (value: unknown): string => {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "-";
  }
  return `${(value * 100).toFixed(2)}%`;
};

const formatTime = (value?: string | null): string => {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

export function EvaluationDashboardPage(): JSX.Element {
  const {
    buildId,
    setBuildId,
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
    selectedCaseId,
    setSelectedCaseId,
    selectedCase,
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

  const failedCaseCount = useMemo(
    () => runCases.filter((caseItem) => !caseItem.passed).length,
    [runCases],
  );

  return (
    <section className="chat-grid">
      <article className="panel">
        <h2>Evaluation Dashboard</h2>
        <p className="muted">Run RAG evaluation tasks and inspect run/case quality results.</p>
        <div className="form-grid">
          <div className="inline-grid">
            <label>
              Build ID (optional)
              <input value={buildId} onChange={(event) => setBuildId(event.target.value)} />
            </label>
            <label>
              Dataset ID (optional)
              <input value={datasetId} onChange={(event) => setDatasetId(event.target.value)} />
            </label>
          </div>
          <div className="inline-grid">
            <label>
              Dataset Version ID (optional)
              <input value={versionId} onChange={(event) => setVersionId(event.target.value)} />
            </label>
            <label>
              Query Text (optional, empty = auto-generated from documents)
              <input value={queryText} onChange={(event) => setQueryText(event.target.value)} />
            </label>
          </div>
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
                  onClick={() => {
                    setSelectedRunId(run.run_id);
                    setSelectedCaseId(null);
                  }}
                >
                  <div className="result-card-header">
                    <strong>{run.run_id}</strong>
                    <span
                      className={`badge ${
                        run.status === "succeeded"
                          ? "pass"
                          : run.status === "failed"
                            ? "fail"
                            : "neutral"
                      }`}
                    >
                      {run.status ?? "-"}
                    </span>
                  </div>
                  <small>build_id={run.build_id ?? "-"}</small>
                  <small>
                    dataset={run.dataset_id ?? "-"} / version={run.dataset_version_id ?? "-"}
                  </small>
                  <small>cases={run.case_count}</small>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </article>

      <article className="panel">
        <h3>Run Summary</h3>
        {!selectedRunId ? <p className="muted">Select a run first.</p> : null}
        {selectedRunId && runDetailLoading ? <p className="muted">Loading run detail...</p> : null}
        {runDetail ? (
          <>
            <div className="info-grid">
              <div className="info-item">
                <span className="muted">run_id</span>
                <strong>{runDetail.run_id}</strong>
              </div>
              <div className="info-item">
                <span className="muted">build_id</span>
                <strong>{runDetail.build_id ?? "-"}</strong>
              </div>
              <div className="info-item">
                <span className="muted">status</span>
                <strong>{runDetail.status ?? "-"}</strong>
              </div>
              <div className="info-item">
                <span className="muted">started_at</span>
                <strong>{formatTime(runDetail.started_at)}</strong>
              </div>
              <div className="info-item">
                <span className="muted">completed_at</span>
                <strong>{formatTime(runDetail.completed_at)}</strong>
              </div>
            </div>

            <h4>Summary Metrics</h4>
            <div className="metric-grid">
              <div className="metric-card">
                <span className="muted">sample_count</span>
                <strong>{String(runDetail.summary.sample_count ?? "-")}</strong>
              </div>
              <div className="metric-card">
                <span className="muted">overall_pass_rate</span>
                <strong>{formatPercent(runDetail.summary.overall_pass_rate)}</strong>
              </div>
              <div className="metric-card">
                <span className="muted">retrieval_pass_rate</span>
                <strong>{formatPercent(runDetail.summary.retrieval_pass_rate)}</strong>
              </div>
              <div className="metric-card">
                <span className="muted">citation_pass_rate</span>
                <strong>{formatPercent(runDetail.summary.citation_pass_rate)}</strong>
              </div>
              <div className="metric-card">
                <span className="muted">answer_pass_rate</span>
                <strong>{formatPercent(runDetail.summary.answer_pass_rate)}</strong>
              </div>
              <div className="metric-card">
                <span className="muted">failed_cases</span>
                <strong>{failedCaseCount}</strong>
              </div>
            </div>

            <details>
              <summary>Summary Details</summary>
              <pre>{JSON.stringify(runDetail.summary, null, 2)}</pre>
            </details>
            <details>
              <summary>Run Metadata</summary>
              <pre>{JSON.stringify(runDetail.metadata, null, 2)}</pre>
            </details>
          </>
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
                <button
                  type="button"
                  className={selectedCaseId === caseItem.sample_id ? "list-button active" : "list-button"}
                  onClick={() => setSelectedCaseId(caseItem.sample_id)}
                >
                  <div className="result-card-header">
                    <strong>{caseItem.sample_id}</strong>
                    {!caseItem.passed ? (
                      <span className="badge fail">FAILED</span>
                    ) : (
                      <span className="badge pass">PASSED</span>
                    )}
                  </div>
                  <small>retrieval_status={caseItem.retrieval_status}</small>
                  <small>top_k={caseItem.resolved_top_k}</small>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </article>

      <article className="panel">
        <h3>Case Detail</h3>
        {!selectedCase ? <p className="muted">Select a case to inspect detail.</p> : null}
        {selectedCase ? (
          <>
            <div className="info-grid">
              <div className="info-item">
                <span className="muted">sample_id</span>
                <strong>{selectedCase.sample_id}</strong>
              </div>
              <div className="info-item">
                <span className="muted">retrieval_status</span>
                <strong>{selectedCase.retrieval_status}</strong>
              </div>
              <div className="info-item">
                <span className="muted">resolved_top_k</span>
                <strong>{selectedCase.resolved_top_k}</strong>
              </div>
              <div className="info-item">
                <span className="muted">passed</span>
                <strong>{String(selectedCase.passed)}</strong>
              </div>
            </div>
            <details open>
              <summary>Retrieval Result</summary>
              <pre>{JSON.stringify(selectedCase.retrieval, null, 2)}</pre>
            </details>
            <details>
              <summary>Citation Result</summary>
              <pre>{JSON.stringify(selectedCase.citation, null, 2)}</pre>
            </details>
            <details>
              <summary>Answer Result</summary>
              <pre>{JSON.stringify(selectedCase.answer, null, 2)}</pre>
            </details>
          </>
        ) : null}
      </article>
    </section>
  );
}
