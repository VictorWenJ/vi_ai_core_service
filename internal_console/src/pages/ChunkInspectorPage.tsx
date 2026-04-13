import { useMemo } from "react";

import { useChunkInspector } from "@/features/chunk-inspector/useChunkInspector";

const formatTimeValue = (value: unknown): string => {
  if (typeof value !== "string" || !value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

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
    resolvedDebugTopK,
    resolvedDebugFilter,
    runRetrievalDebug,
  } = useChunkInspector();

  const vectorPreview = chunkVectorDetail?.vector.slice(0, 24) ?? [];
  const hasTruncatedVector = (chunkVectorDetail?.vector.length ?? 0) > vectorPreview.length;

  const selectedChunkMetadata = useMemo(
    () => (chunkDetail?.metadata ? chunkDetail.metadata : {}),
    [chunkDetail],
  );

  return (
    <section className="chat-grid">
      <article className="panel">
        <h2>Chunk / Vector Inspector</h2>
        <p className="muted">Inspect chunk source, vector payload, and retrieval behavior for debugging.</p>
        <p className="message">{message}</p>
        {documentsError ? <p className="error-text">{documentsError}</p> : null}
      </article>

      <article className="panel">
        <h3>Documents</h3>
        {documentsLoading ? <p className="muted">Loading documents...</p> : null}
        {!documentsLoading && documents.length === 0 ? <p className="muted">No documents.</p> : null}
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
                  <div className="result-card-header">
                    <strong>{document.title}</strong>
                    <span className="badge neutral">{document.source_type}</span>
                  </div>
                  <small>document_id={document.document_id}</small>
                  <small>chunks={document.chunk_count}</small>
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
                  <div className="result-card-header">
                    <strong>chunk #{chunk.chunk_index}</strong>
                    <span className="badge neutral">token={chunk.token_count}</span>
                  </div>
                  <small>chunk_id={chunk.chunk_id}</small>
                  <small>vector_point_id={chunk.vector_point_id ?? "-"}</small>
                  <small>{chunk.chunk_text_preview}</small>
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
              placeholder="Ask a retrieval query..."
            />
          </label>
          <div className="inline-grid">
            <label>
              Top K
              <input value={debugTopK} onChange={(event) => setDebugTopK(event.target.value)} />
            </label>
            <label>
              Metadata Filter JSON
              <textarea
                rows={2}
                className="textarea-mono"
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

        <div className="info-grid">
          <div className="info-item">
            <span className="muted">query</span>
            <strong>{retrievalDebugResult?.query_text ?? (debugQueryText || "-")}</strong>
          </div>
          <div className="info-item">
            <span className="muted">top_k</span>
            <strong>{retrievalDebugResult?.top_k ?? resolvedDebugTopK ?? "-"}</strong>
          </div>
          <div className="info-item">
            <span className="muted">status</span>
            <strong>{retrievalDebugResult?.status ?? "-"}</strong>
          </div>
        </div>

        <details>
          <summary>Resolved Metadata Filter</summary>
          <pre>{JSON.stringify(resolvedDebugFilter, null, 2)}</pre>
        </details>

        {retrievalDebugResult?.hits?.length ? (
          <ul className="simple-list">
            {retrievalDebugResult.hits.map((hit, index) => (
              <li key={hit.chunk_id} className="result-card">
                <div className="result-card-header">
                  <strong>
                    #{index + 1} {hit.title ?? hit.document_id}
                  </strong>
                  <span className="badge neutral">score={hit.score.toFixed(4)}</span>
                </div>
                <p>{hit.snippet}</p>
                <small>document_id={hit.document_id}</small>
                <small>chunk_id={hit.chunk_id}</small>
                <small>source={hit.source_type ?? "-"}</small>
                <small>origin={hit.origin_uri ?? "-"}</small>
                <div className="button-row">
                  <button type="button" onClick={() => setSelectedChunkId(hit.chunk_id)}>
                    Inspect This Chunk
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No retrieval hits yet.</p>
        )}

        <h4>Debug Citations</h4>
        {retrievalDebugResult?.citations?.length ? (
          <ul className="citation-list">
            {retrievalDebugResult.citations.map((citation) => (
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
          <p className="muted">No citations from retrieval debug.</p>
        )}

        <details>
          <summary>Retrieval Trace</summary>
          <pre>{JSON.stringify(retrievalDebugResult?.trace ?? {}, null, 2)}</pre>
        </details>
      </article>

      <article className="panel">
        <h3>Document Detail</h3>
        {!documentDetail ? <p className="muted">Select a document to inspect detail.</p> : null}
        {documentDetail ? (
          <div className="info-grid">
            <div className="info-item">
              <span className="muted">document_id</span>
              <strong>{documentDetail.document_id}</strong>
            </div>
            <div className="info-item">
              <span className="muted">title</span>
              <strong>{documentDetail.title}</strong>
            </div>
            <div className="info-item">
              <span className="muted">source_type</span>
              <strong>{documentDetail.source_type}</strong>
            </div>
            <div className="info-item">
              <span className="muted">latest_version_id</span>
              <strong>{documentDetail.latest_version_id ?? "-"}</strong>
            </div>
            <div className="info-item">
              <span className="muted">updated_at</span>
              <strong>{formatTimeValue(documentDetail.updated_at)}</strong>
            </div>
          </div>
        ) : null}
      </article>

      <article className="panel">
        <h3>Chunk Detail</h3>
        {!selectedChunkId ? <p className="muted">Select a chunk first.</p> : null}
        {selectedChunkId && chunkDetailLoading ? <p className="muted">Loading chunk detail...</p> : null}
        {chunkDetail ? (
          <>
            <h4>Base Info</h4>
            <div className="info-grid">
              <div className="info-item">
                <span className="muted">chunk_id</span>
                <strong>{chunkDetail.chunk_id}</strong>
              </div>
              <div className="info-item">
                <span className="muted">document_id</span>
                <strong>{chunkDetail.document_id}</strong>
              </div>
              <div className="info-item">
                <span className="muted">document_version_id</span>
                <strong>{chunkDetail.document_version_id ?? "-"}</strong>
              </div>
              <div className="info-item">
                <span className="muted">build_id</span>
                <strong>{chunkDetail.build_id ?? "-"}</strong>
              </div>
              <div className="info-item">
                <span className="muted">chunk_index</span>
                <strong>{chunkDetail.chunk_index}</strong>
              </div>
              <div className="info-item">
                <span className="muted">token_count</span>
                <strong>{chunkDetail.token_count}</strong>
              </div>
            </div>

            <h4>Chunk Text</h4>
            <pre>{chunkDetail.chunk_text || chunkDetail.chunk_text_preview || "-"}</pre>

            <h4>Metadata</h4>
            <details open>
              <summary>Chunk Metadata</summary>
              <pre>{JSON.stringify(selectedChunkMetadata, null, 2)}</pre>
            </details>
          </>
        ) : null}
      </article>

      <article className="panel">
        <h3>Vector Detail</h3>
        {!selectedChunkId ? <p className="muted">Select a chunk to inspect vector detail.</p> : null}
        {selectedChunkId && chunkVectorDetailLoading ? <p className="muted">Loading vector detail...</p> : null}
        {chunkVectorDetailError ? <p className="error-text">{chunkVectorDetailError}</p> : null}
        {chunkVectorDetail ? (
          <>
            <div className="info-grid">
              <div className="info-item">
                <span className="muted">vector_point_id</span>
                <strong>{chunkVectorDetail.vector_point_id}</strong>
              </div>
              <div className="info-item">
                <span className="muted">vector_dimension</span>
                <strong>{chunkVectorDetail.vector_dimension}</strong>
              </div>
              <div className="info-item">
                <span className="muted">embedding_model_name</span>
                <strong>
                  {chunkVectorDetail.embedding_model_name ?? chunkDetail?.embedding_model ?? "-"}
                </strong>
              </div>
              <div className="info-item">
                <span className="muted">vector_collection</span>
                <strong>{chunkVectorDetail.vector_collection}</strong>
              </div>
              <div className="info-item">
                <span className="muted">found</span>
                <strong>{String(chunkVectorDetail.found)}</strong>
              </div>
            </div>

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
    </section>
  );
}
