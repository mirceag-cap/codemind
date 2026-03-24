# LangGraph StateGraph setup — skeleton with MemorySaver checkpointer

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import GraphState

# Module-level singleton — compiled once at import time
_graph = None


def _build_graph():
    """Build and compile the StateGraph with a MemorySaver checkpointer."""
    builder = StateGraph(GraphState)

    # Placeholder no-op node — real agent nodes are wired in by later tickets
    def noop(state: GraphState) -> dict:
        return {}

    builder.add_node("noop", noop)
    builder.set_entry_point("noop")
    builder.add_edge("noop", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


def get_graph():
    """Return the compiled graph singleton, initialising it on first call."""
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph
