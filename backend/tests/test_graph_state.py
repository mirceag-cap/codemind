# Tests for Graph State & Skeleton (Issue #2)

from typing import get_type_hints
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages

from app.graph.state import GraphState
from app.graph.graph import get_graph


# ── State field tests ──────────────────────────────────────────────────────────


def test_graph_state_fields_exist():
    """GraphState has (at least) the four required fields."""
    required = {"messages", "repo_name", "retrieved_chunks", "route"}
    # Use issubset so adding fields in future tickets doesn't break this test
    assert required.issubset(set(get_type_hints(GraphState).keys()))


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
    """Graph can be invoked with only the required fields and returns without raising.

    retrieved_chunks and route are NotRequired — they are absent on the first
    turn and populated later by agent nodes, so omitting them here is valid.
    """
    graph = get_graph()
    config = {"configurable": {"thread_id": "test-thread-invoke"}}
    result = graph.invoke(
        {"messages": [HumanMessage(content="hello")], "repo_name": "test"},
        config=config,
    )
    assert "messages" in result
    assert len(result["messages"]) >= 1
