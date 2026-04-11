import { KeyValueTable } from "@/components/KeyValueTable";
import { useKnowledgeIngest } from "@/features/knowledge-ingest/useKnowledgeIngest";

export function KnowledgeIngestPage(): JSX.Element {
  const {
    selectedFile,
    setSelectedFile,
    title,
    setTitle,
    documentId,
    setDocumentId,
    sourceType,
    setSourceType,
    tags,
    setTags,
    versionId,
    setVersionId,
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
    uploadDocument,
    uploadPending,
    triggerBuild,
    buildPending,
  } = useKnowledgeIngest();

  return (
    <section className="chat-grid">
      <article className="panel">
        <h2>Knowledge Ingest</h2>
        <p className="muted">Upload document and trigger offline build.</p>

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
              Source Type (optional)
              <input
                value={sourceType}
                onChange={(event) => setSourceType(event.target.value)}
                placeholder="raw_text / markdown_file / text_file"
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
                placeholder="console-20260412"
              />
            </label>
            <label>
              Max Failure Ratio
              <input
                value={maxFailureRatio}
                onChange={(event) => setMaxFailureRatio(event.target.value)}
                placeholder="0.0"
              />
            </label>
          </div>
          <label>
            Max Empty Chunk Ratio
            <input
              value={maxEmptyChunkRatio}
              onChange={(event) => setMaxEmptyChunkRatio(event.target.value)}
              placeholder="0.0"
            />
          </label>
        </div>
        <div className="button-row">
          <button type="button" className="accent" disabled={buildPending} onClick={triggerBuild}>
            {buildPending ? "Building..." : "Trigger Build"}
          </button>
        </div>
        <p className="message">{message}</p>
        {buildsError ? <p className="error-text">{buildsError}</p> : null}
      </article>

      <article className="panel">
        <h3>Build List</h3>
        {buildsLoading ? <p className="muted">Loading builds...</p> : null}
        {!buildsLoading && builds.length === 0 ? <p className="muted">No builds.</p> : null}
        {builds.length > 0 ? (
          <ul className="simple-list">
            {builds.map((build) => (
              <li key={build.metadata.build_id}>
                <button
                  type="button"
                  className={
                    selectedBuildId === build.metadata.build_id ? "list-button active" : "list-button"
                  }
                  onClick={() => setSelectedBuildId(build.metadata.build_id)}
                >
                  <strong>{build.metadata.build_id}</strong>
                  <small>
                    version={build.metadata.version_id} mode={build.metadata.build_mode}
                  </small>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </article>

      <KeyValueTable title="Latest Build Summary" value={latestBuild} />
      <KeyValueTable
        title="Selected Build Detail"
        value={buildDetailLoading ? { loading: true } : buildDetail}
      />
    </section>
  );
}
