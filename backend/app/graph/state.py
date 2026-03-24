# Shared state that flows through every LangGraph node

from typing import Annotated
from typing_extensions import TypedDict, NotRequired
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    # Conversation history — append-only via add_messages reducer
    messages: Annotated[list[BaseMessage], add_messages]
    # Which repo the user is querying
    repo_name: str
    # Code chunks retrieved by the RAG/code-writer agents (set by agent nodes)
    retrieved_chunks: NotRequired[list[str]]
    # Routing decision set by the Supervisor node (absent until Supervisor runs)
    route: NotRequired[str]
