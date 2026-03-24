# GET /api/v1/repos — returns distinct repo names currently in Weaviate

from collections.abc import Iterator

import weaviate
import weaviate.classes as wvc

from fastapi import APIRouter, Depends

from app.vectordb.schema import get_client, COLLECTION_NAME

router = APIRouter()


# ── Dependency ─────────────────────────────────────────────────────────────────


def weaviate_client() -> Iterator[weaviate.WeaviateClient]:
    """FastAPI dependency that opens and closes a Weaviate connection per request.

    weaviate.WeaviateClient supports the context manager protocol
    (__enter__/__exit__) as of weaviate-client v4, which is the version
    pinned in pyproject.toml (>=4.6.0).
    """
    with get_client() as client:
        yield client


# ── Endpoint ───────────────────────────────────────────────────────────────────


@router.get("/repos")
async def list_repos(
    client: weaviate.WeaviateClient = Depends(weaviate_client),
) -> dict[str, list[str]]:
    """
    Returns the distinct set of repo_name values in the Weaviate CodeChunk
    collection. Feeds the repo selector dropdown in the chat UI.
    """
    collection = client.collections.get(COLLECTION_NAME)

    response = collection.aggregate.over_all(
        group_by=wvc.aggregate.GroupByAggregate(prop="repo_name"),
        total_count=True,
    )

    repos = [group.grouped_by.value for group in response.groups]
    return {"repos": repos}
