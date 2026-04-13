import { useMemo } from "react";

import { useKnowledgeIngest } from "@/features/knowledge-ingest/useKnowledgeIngest";

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

const formatPercent = (value: number): string => `${(value * 100).toFixed(2)}%`;

const readStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => String(item));
};

const readManifestDocumentCount = (manifest: Record<string, unknown>): number => {
  const documentIds = readStringArray(manifest.document_ids);
  if (documentIds.length > 0) {
    return documentIds.length;
  }
  const documents = Array.isArray(manifest.documents) ? manifest.documents : [];
  return documents.length;
};

export function KnowledgeIngestPage(): JSX.Element {
  const {
    selectedFile,
    setSelectedFile,
    title,
    setTitle,
    documentId,
    setDocumentId,
    originUri,
    setOriginUri,
    sourceType,
    setSourceType,
    jurisdiction,
    setJurisdiction,
    domain,
    setDomain,
    tags,
    setTags,
    versionId,
    setVersionId,
    forceRebuildDocumentIds,
    setForceRebuildDocumentIds,
    maxFailureRatio,
    setMaxFailureRatio,
    maxEmptyChunkRatio,
    setMaxEmptyChunkRatio,
    selectedBuildId,
    setSelectedBuildId,
    message,
    builds,
    buildsLoading,
    buildsError,
    buildDetail,
    buildDetailLoading,
    latestBuild,
    runtimeSummary,
    runtimeConfig,
    runtimeLoading,
    runtimeError,
    uploadDocument,
    uploadPending,
    triggerBuild,
    buildPending,
  } = useKnowledgeIngest();

  const embeddingDimension = runtimeConfig?.rag?.embedding_dimension;
  const vectorCollection = runtimeConfig?.rag?.qdrant_collection;
  const storageRoot = runtimeConfig?.rag?.content_store_root;

  const selectedManifest = useMemo(
    () => (buildDetail?.manifest ? buildDetail.manifest : {}),
    [buildDetail],
  );

  return (
    <section className="chat-grid">
      <article className="panel">
        <h2>Knowledge Build Console</h2>
        <p className="muted">Upload documents, trigger build tasks, and inspect quality gate outcomes.</p>
        <p className="message">{message}</p>
        {buildsError ? <p className="error-text">{buildsError}</p> : null}
      </article>

      <article className="panel">
        <h3>Embedding Baseline</h3>
        {runtimeLoading ? <p className="muted">Loading runtime baseline...</p> : null}
        {runtimeError ? <p className="error-text">{runtimeError}</p> : null}
        <div className="info-grid">
          <div className="info-item">
            <span className="muted">provider</span>
            <strong>{runtimeSummary?.embedding_provider ?? "-"}</strong>
          </div>
          <div className="info-item">
            <span className="muted">model</span>
            <strong>{runtimeSummary?.embedding_model ?? "-"}</strong>
          </div>
          <div className="info-item">
            <span className="muted">dimension</span>
            <strong>{embeddingDimension ?? "-"}</strong>
          </div>
          <div className="info-item">
            <span className="muted">vector collection</span>
            <strong>{vectorCollection ?? "-"}</strong>
          </div>
          <div className="info-item">
            <span className="muted">storage root</span>
            <strong>{storageRoot ?? "-"}</strong>
          </div>
        </div>
      </article>

      <article className="panel">
        <h3>Document Upload</h3>
        <div className="form-grid">
          <label>
            Document File
            <input
              type="file"
              accept=".txt,.md,text/plain,text/markdown"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <div className="inline-grid">
            <label>
              Title (optional)
              <input value={title} onChange={(event) => setTitle(event.target.value)} />
            </label>
            <label>
              Document ID (optional)
              <input
                value={documentId}
                onChange={(event) => setDocumentId(event.target.value)}
              />
            </label>
          </div>
          <div className="inline-grid">
            <label>
              Origin URI (optional)
              <input
                value={originUri}
                onChange={(event) => setOriginUri(event.target.value)}
                placeholder="https://example.com/source"
              />
            </label>
            <label>
              Source Type (optional)
              <input
                value={sourceType}
                onChange={(event) => setSourceType(event.target.value)}
                placeholder="raw_text / markdown_file / text_file"
              />
            </label>
            <label>
              Jurisdiction (optional)
              <input
                value={jurisdiction}
                onChange={(event) => setJurisdiction(event.target.value)}
                placeholder="cn / us / eu"
              />
            </label>
          </div>
          <div className="inline-grid">
            <label>
              Domain (optional)
              <input
                value={domain}
                onChange={(event) => setDomain(event.target.value)}
                placeholder="law / finance / policy"
              />
            </label>
            <label>
              Tags (comma separated)
              <input value={tags} onChange={(event) => setTags(event.target.value)} />
            </label>
          </div>
        </div>

        <div className="button-row">
          <button
            type="button"
            disabled={!selectedFile || uploadPending}
            onClick={uploadDocument}
          >
            {uploadPending ? "Uploading..." : "Upload Document"}
          </button>
        </div>
      </article>

      <article className="panel">
        <h3>Build Trigger</h3>
        <div className="form-grid">
          <div className="inline-grid">
            <label>
              Version ID (optional)
              <input
                value={versionId}
                onChange={(event) => setVersionId(event.target.value)}
                placeholder="knowledge-20260413T120000Z"
              />
            </label>
            <label>
              Max Failure Ratio
              <input
                value={maxFailureRatio}
                onChange={(event) => setMaxFailureRatio(event.target.value)}
                placeholder="0.05"
              />
            </label>
          </div>
          <label>
            Max Empty Chunk Ratio
            <input
              value={maxEmptyChunkRatio}
              onChange={(event) => setMaxEmptyChunkRatio(event.target.value)}
              placeholder="0.2"
            />
          </label>
          <label>
            Force Rebuild Document IDs (CSV)
            <input
              value={forceRebuildDocumentIds}
              onChange={(event) => setForceRebuildDocumentIds(event.target.value)}
              placeholder="doc-1,doc-2"
            />
          </label>
        </div>
        <div className="button-row">
          <button type="button" className="accent" disabled={buildPending} onClick={triggerBuild}>
            {buildPending ? "Building..." : "Trigger Build"}
          </button>
        </div>
      </article>

      <article className="panel">
        <h3>Build List</h3>
        {buildsLoading ? <p className="muted">Loading builds...</p> : null}
        {!buildsLoading && builds.length === 0 ? <p className="muted">No builds.</p> : null}
        {builds.length > 0 ? (
          <ul className="simple-list">
            {builds.map((build) => {
              const status = build.metadata.status ?? "unknown";
              const isSelected = selectedBuildId === build.metadata.build_id;
              return (
                <li key={build.metadata.build_id}>
                  <button
                    type="button"
                    className={isSelected ? "list-button active" : "list-button"}
                    onClick={() => setSelectedBuildId(build.metadata.build_id)}
                  >
                    <div className="result-card-header">
                      <strong>{build.metadata.build_id}</strong>
                      <span className={`badge ${status === "succeeded" ? "pass" : status === "failed" ? "fail" : "neutral"}`}>
                        {status}
                      </span>
                    </div>
                    <small>
                      version={build.metadata.build_version_id ?? build.metadata.version_id}
                    </small>
                    <small>
                      started={formatTime(build.metadata.started_at)}
                    </small>
                  </button>
                </li>
              );
            })}
          </ul>
        ) : null}
      </article>

      <article className="panel">
        <h3>Latest Build Snapshot</h3>
        {!latestBuild ? <p className="muted">No completed build yet.</p> : null}
        {latestBuild ? (
          <div className="metric-grid">
            <div className="metric-card">
              <span className="muted">status</span>
              <strong>{latestBuild.metadata.status ?? "-"}</strong>
            </div>
            <div className="metric-card">
              <span className="muted">requested docs</span>
              <strong>{latestBuild.statistics.requested_document_count}</strong>
            </div>
            <div className="metric-card">
              <span className="muted">chunk count</span>
              <strong>{latestBuild.statistics.chunk_count}</strong>
            </div>
            <div className="metric-card">
              <span className="muted">latency</span>
              <strong>{latestBuild.statistics.latency_ms} ms</strong>
            </div>
          </div>
        ) : null}
      </article>

      <article className="panel">
        <h3>Selected Build Detail</h3>
        {!selectedBuildId ? <p className="muted">Select a build first.</p> : null}
        {selectedBuildId && buildDetailLoading ? <p className="muted">Loading build detail...</p> : null}
        {buildDetail ? (
          <>
            <div className="info-grid">
              <div className="info-item">
                <span className="muted">build_id</span>
                <strong>{buildDetail.metadata.build_id}</strong>
              </div>
              <div className="info-item">
                <span className="muted">build_version_id</span>
                <strong>{buildDetail.metadata.build_version_id ?? buildDetail.metadata.version_id}</strong>
              </div>
              <div className="info-item">
                <span className="muted">status</span>
                <strong>{buildDetail.metadata.status ?? "-"}</strong>
              </div>
              <div className="info-item">
                <span className="muted">started_at</span>
                <strong>{formatTime(buildDetail.metadata.started_at)}</strong>
              </div>
              <div className="info-item">
                <span className="muted">completed_at</span>
                <strong>{formatTime(buildDetail.metadata.completed_at)}</strong>
              </div>
            </div>

            <h4>Statistics</h4>
            <div className="metric-grid">
              <div className="metric-card">
                <span className="muted">processed / requested</span>
                <strong>
                  {buildDetail.statistics.processed_document_count} / {buildDetail.statistics.requested_document_count}
                </strong>
              </div>
              <div className="metric-card">
                <span className="muted">failed docs</span>
                <strong>{buildDetail.statistics.failed_document_count}</strong>
              </div>
              <div className="metric-card">
                <span className="muted">chunk count</span>
                <strong>{buildDetail.statistics.chunk_count}</strong>
              </div>
              <div className="metric-card">
                <span className="muted">upserted vectors</span>
                <strong>{buildDetail.statistics.upserted_count}</strong>
              </div>
              <div className="metric-card">
                <span className="muted">embedding batches</span>
                <strong>{buildDetail.statistics.embedding_batch_count}</strong>
              </div>
              <div className="metric-card">
                <span className="muted">latency</span>
                <strong>{buildDetail.statistics.latency_ms} ms</strong>
              </div>
            </div>

            <h4>Quality Gate</h4>
            <div className="info-grid">
              <div className="info-item">
                <span className="muted">passed</span>
                <strong>{String(buildDetail.quality_gate.passed)}</strong>
              </div>
              <div className="info-item">
                <span className="muted">failure ratio</span>
                <strong>{formatPercent(buildDetail.quality_gate.failure_ratio)}</strong>
              </div>
              <div className="info-item">
                <span className="muted">empty chunk ratio</span>
                <strong>{formatPercent(buildDetail.quality_gate.empty_chunk_ratio)}</strong>
              </div>
              <div className="info-item">
                <span className="muted">failed rules</span>
                <strong>
                  {buildDetail.quality_gate.failed_rules.length > 0
                    ? buildDetail.quality_gate.failed_rules.join(", ")
                    : "none"}
                </strong>
              </div>
            </div>

            <h4>Manifest Summary</h4>
            <div className="info-grid">
              <div className="info-item">
                <span className="muted">document count</span>
                <strong>{readManifestDocumentCount(selectedManifest)}</strong>
              </div>
              <div className="info-item">
                <span className="muted">forced document ids</span>
                <strong>{readStringArray(selectedManifest.forced_document_ids).join(", ") || "-"}</strong>
              </div>
            </div>
            <details>
              <summary>Manifest Details</summary>
              <pre>{JSON.stringify(buildDetail.manifest, null, 2)}</pre>
            </details>

            <h4>Processed Documents</h4>
            {buildDetail.ingestion_results.length === 0 ? (
              <p className="muted">No ingestion records.</p>
            ) : (
              <table className="kv-table">
                <thead>
                  <tr>
                    <th>document_id</th>
                    <th>version</th>
                    <th>action</th>
                    <th>chunks</th>
                    <th>vectors</th>
                    <th>error</th>
                  </tr>
                </thead>
                <tbody>
                  {buildDetail.ingestion_results.map((item) => (
                    <tr key={`${item.document_id}:${item.document_version_id ?? "-"}`}>
                      <td>
                        <code>{item.document_id}</code>
                      </td>
                      <td>{item.document_version_id ?? "-"}</td>
                      <td>{item.action}</td>
                      <td>{item.chunk_count}</td>
                      <td>{item.vector_count}</td>
                      <td>{item.error_message ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        ) : null}
      </article>
    </section>
  );
}
