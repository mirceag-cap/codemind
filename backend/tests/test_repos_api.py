# Integration tests for GET /api/v1/repos (Issue #3)

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.repos import weaviate_client


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """Ensure dependency_overrides is reset after every test."""
    yield
    app.dependency_overrides.clear()


def _make_mock_client(repo_names: list[str]) -> MagicMock:
    """Build a mock Weaviate client that returns the given repo names."""
    groups = []
    for name in repo_names:
        group = MagicMock()
        group.grouped_by.value = name
        groups.append(group)

    aggregate_response = MagicMock()
    aggregate_response.groups = groups

    collection = MagicMock()
    collection.aggregate.over_all.return_value = aggregate_response

    client = MagicMock()
    client.collections.get.return_value = collection
    return client


def _override(repo_names: list[str]) -> None:
    """Override the weaviate_client dependency with a mock."""
    mock_client = _make_mock_client(repo_names)
    app.dependency_overrides[weaviate_client] = lambda: mock_client


def test_list_repos_returns_200():
    """GET /api/v1/repos returns HTTP 200."""
    _override(["myrepo"])
    with TestClient(app) as c:
        response = c.get("/api/v1/repos")
    assert response.status_code == 200


def test_list_repos_returns_expected_list():
    """GET /api/v1/repos returns distinct repo names from Weaviate with exact schema."""
    repos = ["myrepo", "otherrepo"]
    _override(repos)
    with TestClient(app) as c:
        response = c.get("/api/v1/repos")
    data = response.json()
    assert set(data.keys()) == {"repos"}
    assert sorted(data["repos"]) == sorted(repos)


def test_list_repos_empty_when_no_data():
    """GET /api/v1/repos returns an empty list when Weaviate has no repos."""
    _override([])
    with TestClient(app) as c:
        response = c.get("/api/v1/repos")
    assert response.status_code == 200
    assert response.json() == {"repos": []}


def test_list_repos_cors_header_for_frontend_origin():
    """CORS allows the frontend dev server origin (http://localhost:5173)."""
    _override(["repo"])
    with TestClient(app) as c:
        response = c.get(
            "/api/v1/repos",
            headers={"Origin": "http://localhost:5173"},
        )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
