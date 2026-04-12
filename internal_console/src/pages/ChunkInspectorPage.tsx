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
    chunkDetailLoading,
    chunkVectorDetail,
    chunkVectorDetailLoading,
    chunkVectorDetailError,
    retrievalDebugResult,
    retrievalDebugPending,
    retrievalDebugError,
    runRetrievalDebug,
  } = useChunkInspector();
  const vectorPreview = chunkVectorDetail?.vector.slice(0, 16) ?? [];
  const hasTruncatedVector =
    (chunkVectorDetail?.vector.length ?? 0) > vectorPreview.length;

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
      <KeyValueTable
        title="Chunk Detail"
        value={chunkDetailLoading ? { loading: true } : chunkDetail}
      />
      <article className="panel">
        <h3>Chunk Vector Detail</h3>
        {!selectedChunkId ? <p className="muted">Select a chunk to inspect vector detail.</p> : null}
        {selectedChunkId && chunkVectorDetailLoading ? (
          <p className="muted">Loading vector detail...</p>
        ) : null}
        {chunkVectorDetailError ? <p className="error-text">{chunkVectorDetailError}</p> : null}
        {chunkVectorDetail ? (
          <>
            <table className="kv-table">
              <tbody>
                <tr>
                  <th>vector_point_id</th>
                  <td>
                    <code>{chunkVectorDetail.vector_point_id}</code>
                  </td>
                </tr>
                <tr>
                  <th>vector_dimension</th>
                  <td>{chunkVectorDetail.vector_dimension}</td>
                </tr>
                <tr>
                  <th>embedding_model_name</th>
                  <td>{chunkDetail?.embedding_model ?? "-"}</td>
                </tr>
                <tr>
                  <th>vector_collection</th>
                  <td>{chunkVectorDetail.vector_collection}</td>
                </tr>
                <tr>
                  <th>found</th>
                  <td>{String(chunkVectorDetail.found)}</td>
                </tr>
              </tbody>
            </table>
            {chunkVectorDetail.found ? (
              <>
                <details open>
                  <summary>
                    Vector Preview (first {vectorPreview.length} / {chunkVectorDetail.vector.length})
                  </summary>
                  <pre>{JSON.stringify(vectorPreview, null, 2)}</pre>
                </details>
                {hasTruncatedVector ? (
                  <details>
                    <summary>Expand Full Vector</summary>
                    <pre>{JSON.stringify(chunkVectorDetail.vector, null, 2)}</pre>
                  </details>
                ) : null}
                <details>
                  <summary>Vector Payload</summary>
                  <pre>{JSON.stringify(chunkVectorDetail.payload, null, 2)}</pre>
                </details>
              </>
            ) : (
              <p className="muted">Vector point was not found in Qdrant.</p>
            )}
          </>
        ) : null}
      </article>
      <KeyValueTable title="Retrieval Trace" value={retrievalDebugResult?.trace ?? null} />
    </section>
  );
}
