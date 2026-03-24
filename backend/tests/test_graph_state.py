# Tests for Graph State & Skeleton (Issue #2)

import pytest
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages

from app.graph.state import GraphState
from app.graph.graph import get_graph


# ── State field tests ──────────────────────────────────────────────────────────


def test_graph_state_fields_exist():
    """GraphState has the required keys."""
    required = {"messages", "repo_name", "retrieved_chunks", "route"}
    assert required == set(GraphState.__annotations__.keys())


def test_add_messages_appends():
    """add_messages reducer appends rather than replaces."""
    existing = [HumanMessage(content="hello")]
    new_msg = AIMessage(content="world")

    result = add_messages(existing, [new_msg])

    assert len(result) == 2
    assert result[0].content == "hello"
    assert result[1].content == "world"


def test_add_messages_does_not_replace():
    """add_messages with two calls accumulates all messages."""
    msgs = [HumanMessage(content="first")]
    after_first = add_messages([], msgs)
    after_second = add_messages(after_first, [HumanMessage(content="second")])

    assert len(after_second) == 2


# ── Graph invocation test ─────────────────────────────────────────────────────


def test_get_graph_returns_singleton():
    """get_graph() returns the same object on repeated calls."""
    g1 = get_graph()
    g2 = get_graph()
    assert g1 is g2


def test_graph_invoke_without_error():
    """Graph can be invoked with minimal input and returns without raising."""
    graph = get_graph()
    config = {"configurable": {"thread_id": "test-thread"}}
    result = graph.invoke(
        {"messages": [HumanMessage(content="hello")], "repo_name": "test"},
        config=config,
    )
    # messages should still be present after invocation
    assert "messages" in result
    assert len(result["messages"]) >= 1
