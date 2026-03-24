# Ingestion pipeline — walks a codebase, parses files, inserts chunks into Weaviate

from pathlib import Path
from typing import Generator
import weaviate

from app.rag.parser import parse_file, CodeChunk
from app.vectordb.schema import get_client, COLLECTION_NAME

_MAX_CHARS = 8192 * 3


# ── Directory walking ──────────────────────────────────────────────────────────

# Folders that never contain useful source code — always skip
_SKIP_DIRS = {
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".next",
    "coverage",
    "eggs",
    ".eggs",
    "*.egg-info",
}

# File extensions we know how to parse
_SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".tsx"}


def walk_codebase(root_path: str) -> Generator[tuple[str, str], None, None]:
    """
    Recursively walks a directory and yields (file_path, source_code) tuples
    for every supported source file found.

    Yields relative paths so chunk metadata stays portable across machines.
    """
    root = Path(root_path).resolve()

    for file_path in root.rglob("*"):
        # skip directories and unsupported file types
        if not file_path.is_file():
            continue
        if file_path.suffix not in _SUPPORTED_EXTENSIONS:
            continue

        # skip any file whose path contains a noise directory
        # e.g. skip /project/node_modules/lodash/index.js
        if any(skip in file_path.parts for skip in _SKIP_DIRS):
            continue

        try:
            source_code = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  ⚠️  Could not read {file_path}: {e}")
            continue

        # yield a path relative to the root so it's repo-portable
        relative_path = str(file_path.relative_to(root))
        yield relative_path, source_code


# ── Weaviate insertion ─────────────────────────────────────────────────────────


def _truncate_chunk(chunk: CodeChunk) -> CodeChunk:
    """
    Truncates a chunk's content if it exceeds the embedding model's token limit.
    Keeps the beginning of the chunk — where the function signature and
    docstring live — which is the most semantically meaningful part.
    """
    if len(chunk.content) <= _MAX_CHARS:
        return chunk

    truncated_content = chunk.content[:_MAX_CHARS] + "\n# ... (truncated)"
    # return a new dataclass instance with truncated content
    return CodeChunk(
        content=truncated_content,
        file_path=chunk.file_path,
        repo_name=chunk.repo_name,
        language=chunk.language,
        chunk_type=chunk.chunk_type,
        symbol_name=chunk.symbol_name,
        docstring=chunk.docstring,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
    )


def insert_chunks(
    client: weaviate.WeaviateClient,
    chunks: list[CodeChunk],
    batch_size: int = 50,
) -> dict[str, int]:
    """
    Inserts a list of CodeChunks into Weaviate using batch insertion.
    Returns a summary dict with counts of successes and failures.
    """
    collection = client.collections.get(COLLECTION_NAME)
    success_count = 0
    failure_count = 0

    # process chunks in batches to reduce API overhead
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]

        # use Weaviate's context manager batch for automatic flushing
        with collection.batch.dynamic() as wv_batch:
            for chunk in batch:
                try:
                    chunk = _truncate_chunk(chunk)
                    wv_batch.add_object(
                        properties={
                            "content": chunk.content,
                            "file_path": chunk.file_path,
                            "repo_name": chunk.repo_name,
                            "language": chunk.language,
                            "chunk_type": chunk.chunk_type,
                            "symbol_name": chunk.symbol_name,
                            "docstring": chunk.docstring,
                            "start_line": chunk.start_line,
                            "end_line": chunk.end_line,
                        }
                    )
                    success_count += 1
                except Exception as e:
                    print(f"  ⚠️  Failed to insert chunk {chunk.symbol_name}: {e}")
                    failure_count += 1

    return {"success": success_count, "failure": failure_count}


# ── Full pipeline ──────────────────────────────────────────────────────────────


def ingest_codebase(
    root_path: str,
    repo_name: str,
    client: weaviate.WeaviateClient,
) -> dict:
    """
    Full ingestion pipeline:
    1. Walk the directory for supported source files
    2. Parse each file into CodeChunks
    3. Batch-insert all chunks into Weaviate

    Returns a summary of what was processed.
    """
    all_chunks: list[CodeChunk] = []
    file_count = 0
    skipped_count = 0

    print(f"\n🔍 Scanning: {root_path}")

    for file_path, source_code in walk_codebase(root_path):
        # skip empty files — nothing useful to embed
        if not source_code.strip():
            skipped_count += 1
            continue

        chunks = parse_file(
            file_path=file_path,
            source_code=source_code,
            repo_name=repo_name,
        )

        all_chunks.extend(chunks)
        file_count += 1
        print(f"  ✅ {file_path} → {len(chunks)} chunk(s)")

    print(f"\n📦 Parsed {file_count} files → {len(all_chunks)} total chunks")
    print(f"⬆️  Inserting into Weaviate...")

    result = insert_chunks(client, all_chunks)

    summary = {
        "files_parsed": file_count,
        "files_skipped": skipped_count,
        "chunks_total": len(all_chunks),
        "chunks_inserted": result["success"],
        "chunks_failed": result["failure"],
    }

    print(f"\n✅ Ingestion complete: {summary}")
    return summary
