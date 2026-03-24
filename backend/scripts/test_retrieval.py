# Tests retrieval against the chunks we already ingested

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.retriever import retrieve, format_chunks_for_llm

queries = [
    "how are settings loaded from environment variables?",
    "function that parses source code into chunks",
    "weaviate client connection",
]

for query in queries:
    print(f"\n🔍 Query: '{query}'")
    print("─" * 60)

    chunks = retrieve(
        query=query,
        repo_name="codemind-backend",
        limit=2,
    )

    for chunk in chunks:
        print(f"  [{chunk.score:.3f}] {chunk.symbol_name} "
              f"({chunk.file_path}:{chunk.start_line})")

print("\n\n📋 Formatted for LLM:")
print("─" * 60)
chunks = retrieve("load configuration from env file", repo_name="codemind-backend", limit=2)
print(format_chunks_for_llm(chunks))
