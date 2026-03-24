# Defines the Weaviate schema for CodeChunk — the core unit of indexed code

import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType, Configure, VectorDistances
from app.core.config import settings


COLLECTION_NAME = "CodeChunk"


def get_client() -> weaviate.WeaviateClient:
    """Creates and returns a connected Weaviate client."""
    return weaviate.connect_to_local(
        host="localhost",
        port=8080,
        grpc_port=50051,  # explicitly set gRPC port
        headers={"X-OpenAI-Api-Key": settings.openai_api_key},
    )


def create_schema(client: weaviate.WeaviateClient) -> None:
    """
    Creates the CodeChunk collection in Weaviate if it doesn't already exist.
    Safe to call multiple times — skips creation if collection exists.
    """

    # check if collection already exists to avoid overwriting data
    if client.collections.exists(COLLECTION_NAME):
        print(f"✅ Collection '{COLLECTION_NAME}' already exists — skipping creation.")
        return

    client.collections.create(
        name=COLLECTION_NAME,
        # text2vec-openai tells Weaviate to auto-embed using OpenAI
        vectorizer_config=Configure.Vectorizer.text2vec_openai(
            model="text-embedding-3-small",
        ),
        # cosine distance measures the angle between vectors
        vector_index_config=Configure.VectorIndex.hnsw(
            distance_metric=VectorDistances.COSINE
        ),
        properties=[
            Property(
                name="content",
                data_type=DataType.TEXT,
                description="The raw source code text of this chunk",
            ),
            Property(
                name="file_path",
                data_type=DataType.TEXT,
                description="Relative path to the file this chunk came from",
                # we never search by file_path semantically, so skip embedding it
                skip_vectorization=True,
            ),
            Property(
                name="repo_name",
                data_type=DataType.TEXT,
                description="Name of the repository this chunk belongs to",
                skip_vectorization=True,
            ),
            Property(
                name="language",
                data_type=DataType.TEXT,
                description="Programming language (python, javascript, typescript)",
                skip_vectorization=True,
            ),
            Property(
                name="chunk_type",
                data_type=DataType.TEXT,
                description="Type of code unit: function | class | module",
                skip_vectorization=True,
            ),
            Property(
                name="symbol_name",
                data_type=DataType.TEXT,
                description="Name of the function or class, if applicable",
                skip_vectorization=True,
            ),
            Property(
                name="docstring",
                data_type=DataType.TEXT,
                description="Extracted docstring or leading comment, if present",
                # docstrings add semantic meaning — include them in the embedding
                skip_vectorization=False,
            ),
            Property(
                name="start_line",
                data_type=DataType.INT,
                description="Line number where this chunk starts in the file",
                skip_vectorization=True,
            ),
            Property(
                name="end_line",
                data_type=DataType.INT,
                description="Line number where this chunk ends in the file",
                skip_vectorization=True,
            ),
        ],
    )

    print(f"✅ Collection '{COLLECTION_NAME}' created successfully.")


def delete_schema(client: weaviate.WeaviateClient) -> None:
    """
    Deletes the CodeChunk collection entirely.
    Useful for resetting the vector DB during development.
    """
    if client.collections.exists(COLLECTION_NAME):
        client.collections.delete(COLLECTION_NAME)
        print(f"🗑️  Collection '{COLLECTION_NAME}' deleted.")
    else:
        print(f"ℹ️  Collection '{COLLECTION_NAME}' doesn't exist — nothing to delete.")
