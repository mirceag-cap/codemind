# LangGraph StateGraph setup — skeleton with MemorySaver checkpointer

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import GraphState


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


# Compiled once at module import time — no lazy initialisation needed
_graph = _build_graph()


def get_graph():
    """Return the compiled graph singleton."""
    return _graph
