# Integration tests for GET /api/v1/repos (Issue #3)

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.repos import weaviate_client


def _make_mock_client(repo_names: list[str]) -> MagicMock:
    """Build a mock Weaviate client that returns the given repo names."""
    # Build group objects matching the shape returned by aggregate.over_all
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


@pytest.fixture
def client_with_repos(request):
    """Return a TestClient with the Weaviate dependency overridden."""
    repo_names = request.param if hasattr(request, "param") else ["repo-a", "repo-b"]
    mock_client = _make_mock_client(repo_names)

    app.dependency_overrides[weaviate_client] = lambda: mock_client
    with TestClient(app) as c:
        yield c, repo_names
    app.dependency_overrides.clear()


def test_list_repos_returns_200():
    """GET /api/v1/repos returns HTTP 200."""
    mock_client = _make_mock_client(["myrepo"])
    app.dependency_overrides[weaviate_client] = lambda: mock_client
    try:
        with TestClient(app) as c:
            response = c.get("/api/v1/repos")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_list_repos_returns_expected_list():
    """GET /api/v1/repos returns distinct repo names from Weaviate."""
    repos = ["myrepo", "otherrepo"]
    mock_client = _make_mock_client(repos)
    app.dependency_overrides[weaviate_client] = lambda: mock_client
    try:
        with TestClient(app) as c:
            response = c.get("/api/v1/repos")
        data = response.json()
        assert "repos" in data
        assert sorted(data["repos"]) == sorted(repos)
    finally:
        app.dependency_overrides.clear()


def test_list_repos_empty_when_no_data():
    """GET /api/v1/repos returns an empty list when Weaviate has no repos."""
    mock_client = _make_mock_client([])
    app.dependency_overrides[weaviate_client] = lambda: mock_client
    try:
        with TestClient(app) as c:
            response = c.get("/api/v1/repos")
        assert response.status_code == 200
        assert response.json() == {"repos": []}
    finally:
        app.dependency_overrides.clear()


def test_list_repos_cors_header_present():
    """Response includes CORS header for the frontend dev server origin."""
    mock_client = _make_mock_client(["repo"])
    app.dependency_overrides[weaviate_client] = lambda: mock_client
    try:
        with TestClient(app) as c:
            response = c.get(
                "/api/v1/repos",
                headers={"Origin": "http://localhost:5173"},
            )
        assert "access-control-allow-origin" in response.headers
    finally:
        app.dependency_overrides.clear()
