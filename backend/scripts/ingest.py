# CLI script — ingests a local codebase directory into Weaviate

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.vectordb.schema import get_client, create_schema
from app.rag.ingestion import ingest_codebase


def main():
    # default to ingesting the backend/app directory itself
    # so we can test with code we already have
    root_path = sys.argv[1] if len(sys.argv) > 1 else "./app"
    repo_name = sys.argv[2] if len(sys.argv) > 2 else "codemind-backend"

    print(f"🚀 Ingesting '{repo_name}' from: {root_path}")

    with get_client() as client:
        # ensure schema exists before inserting
        create_schema(client)
        ingest_codebase(root_path, repo_name, client)


if __name__ == "__main__":
    main()
