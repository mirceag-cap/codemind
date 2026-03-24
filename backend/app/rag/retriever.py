# Retrieval layer — queries Weaviate using semantic and hybrid search

from dataclasses import dataclass
import weaviate
import weaviate.classes as wvc

from app.vectordb.schema import get_client, COLLECTION_NAME


# ── Result model ───────────────────────────────────────────────────────────────


@dataclass
class RetrievedChunk:
    """A code chunk returned from a search, with its relevance score."""

    content: str
    file_path: str
    repo_name: str
    language: str
    chunk_type: str
    symbol_name: str
    docstring: str
    start_line: int
    end_line: int
    score: float  # relevance score from Weaviate (higher = more relevant)


# ── Search functions ───────────────────────────────────────────────────────────


def semantic_search(
    client: weaviate.WeaviateClient,
    query: str,
    repo_name: str | None = None,
    limit: int = 5,
) -> list[RetrievedChunk]:
    """
    Pure vector similarity search.
    Finds chunks whose meaning is closest to the query.
    Optionally filters to a specific repo.
    """
    collection = client.collections.get(COLLECTION_NAME)

    # build optional repo filter — lets us scope search to one codebase
    filters = None
    if repo_name:
        filters = wvc.query.Filter.by_property("repo_name").equal(repo_name)

    results = collection.query.near_text(
        query=query,
        limit=limit,
        filters=filters,
        # return_metadata tells Weaviate to include the certainty score
        return_metadata=wvc.query.MetadataQuery(certainty=True),
    )

    return [_to_retrieved_chunk(obj) for obj in results.objects]


def hybrid_search(
    client: weaviate.WeaviateClient,
    query: str,
    repo_name: str | None = None,
    limit: int = 5,
    alpha: float = 0.75,
) -> list[RetrievedChunk]:
    """
    Hybrid search — blends vector similarity with BM25 keyword matching.
    alpha=0.75 means 75% vector, 25% keyword. Best default for code search.
    """
    collection = client.collections.get(COLLECTION_NAME)

    filters = None
    if repo_name:
        filters = wvc.query.Filter.by_property("repo_name").equal(repo_name)

    results = collection.query.hybrid(
        query=query,
        alpha=alpha,  # blend ratio: higher = more semantic, lower = more keyword
        limit=limit,
        filters=filters,
        return_metadata=wvc.query.MetadataQuery(score=True),
    )

    return [_to_retrieved_chunk(obj) for obj in results.objects]


def retrieve(
    query: str,
    repo_name: str | None = None,
    limit: int = 5,
    use_hybrid: bool = True,
) -> list[RetrievedChunk]:
    """
    Main retrieval function — this is what the agents call.
    Opens its own Weaviate connection, runs hybrid or semantic search,
    and returns ranked chunks.

    We open/close the client here so agents don't need to manage connections.
    """
    with get_client() as client:
        if use_hybrid:
            return hybrid_search(client, query, repo_name, limit)
        return semantic_search(client, query, repo_name, limit)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _to_retrieved_chunk(obj) -> RetrievedChunk:
    """Converts a raw Weaviate result object into a clean RetrievedChunk."""
    props = obj.properties

    # hybrid search returns .score, semantic search returns .certainty
    # handle both gracefully
    score = 0.0
    if obj.metadata:
        score = obj.metadata.score or obj.metadata.certainty or 0.0

    return RetrievedChunk(
        content=props.get("content", ""),
        file_path=props.get("file_path", ""),
        repo_name=props.get("repo_name", ""),
        language=props.get("language", ""),
        chunk_type=props.get("chunk_type", ""),
        symbol_name=props.get("symbol_name", ""),
        docstring=props.get("docstring", ""),
        start_line=int(props.get("start_line", 0)),
        end_line=int(props.get("end_line", 0)),
        score=float(score),
    )


def format_chunks_for_llm(chunks: list[RetrievedChunk]) -> str:
    """
    Formats retrieved chunks into a clean string for injection into an LLM prompt.
    Each chunk gets a header showing its origin so the LLM can cite it.
    """
    if not chunks:
        return "No relevant code found."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        header = (
            f"--- Chunk {i}: {chunk.symbol_name} "
            f"({chunk.file_path} lines {chunk.start_line}-{chunk.end_line}) ---"
        )
        parts.append(f"{header}\n{chunk.content}")

    # join chunks with clear separators so the LLM sees distinct boundaries
    return "\n\n".join(parts)
