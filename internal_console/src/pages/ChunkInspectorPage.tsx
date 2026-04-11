import { KeyValueTable } from "@/components/KeyValueTable";
import { useChunkInspector } from "@/features/chunk-inspector/useChunkInspector";

export function ChunkInspectorPage(): JSX.Element {
  const {
    selectedDocumentId,
    setSelectedDocumentId,
    selectedChunkId,
    setSelectedChunkId,
    debugQueryText,
    setDebugQueryText,
    debugTopK,
    setDebugTopK,
    debugFilterJson,
    setDebugFilterJson,
    message,
    documents,
    documentsLoading,
    documentsError,
    documentDetail,
    chunks,
    chunksLoading,
    chunkDetail,
    retrievalDebugResult,
    retrievalDebugPending,
    retrievalDebugError,
    runRetrievalDebug,
  } = useChunkInspector();

  return (
    <section className="chat-grid">
      <article className="panel">
        <h2>Chunk Inspector</h2>
        <p className="muted">Browse documents/chunks and debug retrieval hits.</p>
        <p className="message">{message}</p>
        {documentsError ? <p className="error-text">{documentsError}</p> : null}
      </article>

      <article className="panel">
        <h3>Documents</h3>
        {documentsLoading ? <p className="muted">Loading documents...</p> : null}
        {!documentsLoading && documents.length === 0 ? (
          <p className="muted">No documents.</p>
        ) : null}
        {documents.length > 0 ? (
          <ul className="simple-list">
            {documents.map((document) => (
              <li key={document.document_id}>
                <button
                  type="button"
                  className={
                    selectedDocumentId === document.document_id ? "list-button active" : "list-button"
                  }
                  onClick={() => {
                    setSelectedDocumentId(document.document_id);
                    setSelectedChunkId(null);
                  }}
                >
                  <strong>{document.title}</strong>
                  <small>
                    doc={document.document_id} chunks={document.chunk_count}
                  </small>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </article>

      <article className="panel">
        <h3>Chunks</h3>
        {!selectedDocumentId ? <p className="muted">Select a document first.</p> : null}
        {selectedDocumentId && chunksLoading ? <p className="muted">Loading chunks...</p> : null}
        {selectedDocumentId && !chunksLoading && chunks.length === 0 ? (
          <p className="muted">No chunks for selected document.</p>
        ) : null}
        {chunks.length > 0 ? (
          <ul className="simple-list">
            {chunks.map((chunk) => (
              <li key={chunk.chunk_id}>
                <button
                  type="button"
                  className={selectedChunkId === chunk.chunk_id ? "list-button active" : "list-button"}
                  onClick={() => setSelectedChunkId(chunk.chunk_id)}
                >
                  <strong>chunk #{chunk.chunk_index}</strong>
                  <small>
                    id={chunk.chunk_id} token={chunk.token_count}
                  </small>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </article>

      <article className="panel">
        <h3>Retrieval Debug</h3>
        <div className="form-grid">
          <label>
            Query Text
            <input
              value={debugQueryText}
              onChange={(event) => setDebugQueryText(event.target.value)}
              placeholder="ask a retrieval query..."
            />
          </label>
          <div className="inline-grid">
            <label>
              Top K
              <input value={debugTopK} onChange={(event) => setDebugTopK(event.target.value)} />
            </label>
            <label>
              Metadata Filter JSON
              <input
                value={debugFilterJson}
                onChange={(event) => setDebugFilterJson(event.target.value)}
                placeholder='{"domain":"law"}'
              />
            </label>
          </div>
        </div>
        <div className="button-row">
          <button
            type="button"
            className="accent"
            disabled={retrievalDebugPending || !debugQueryText.trim()}
            onClick={runRetrievalDebug}
          >
            {retrievalDebugPending ? "Debugging..." : "Run Retrieval Debug"}
          </button>
        </div>
        {retrievalDebugError ? <p className="error-text">{retrievalDebugError}</p> : null}
        {retrievalDebugResult?.hits?.length ? (
          <ul className="citation-list">
            {retrievalDebugResult.hits.map((hit) => (
              <li key={hit.chunk_id}>
                <div className="citation-head">
                  <strong>{hit.title ?? hit.document_id}</strong>
                  <code>{hit.chunk_id}</code>
                </div>
                <p>{hit.snippet}</p>
                <small>score={hit.score.toFixed(4)}</small>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No retrieval hits yet.</p>
        )}
      </article>

      <KeyValueTable title="Document Detail" value={documentDetail} />
      <KeyValueTable title="Chunk Detail" value={chunkDetail} />
      <KeyValueTable title="Retrieval Trace" value={retrievalDebugResult?.trace ?? null} />
    </section>
  );
}
