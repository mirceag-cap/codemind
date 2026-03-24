# Smoke test — imports every major module to confirm the package tree is healthy

import sys
import os

# allows running this script directly from backend/ without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_import(label: str, import_fn):
    """Runs an import and prints pass/fail clearly."""
    try:
        import_fn()
        print(f"  ✅ {label}")
    except Exception as e:
        print(f"  ❌ {label} — {e}")


print("\n🔍 CodeMind Smoke Test\n" + "─" * 40)

# Core config
test_import("app.core.config", lambda: __import__("app.core.config"))

# API layer
test_import("app.api.health", lambda: __import__("app.api.health"))

# Agent packages (empty __init__.py — just confirms folder is importable)
test_import("app.agents", lambda: __import__("app.agents"))
test_import("app.agents.supervisor", lambda: __import__("app.agents.supervisor"))
test_import("app.agents.rag_agent", lambda: __import__("app.agents.rag_agent"))
test_import("app.agents.code_writer", lambda: __import__("app.agents.code_writer"))
test_import("app.agents.debug_agent", lambda: __import__("app.agents.debug_agent"))

# RAG, graph, vectordb, prompts, evals
test_import("app.rag", lambda: __import__("app.rag"))
test_import("app.graph", lambda: __import__("app.graph"))
test_import("app.vectordb", lambda: __import__("app.vectordb"))
test_import("app.prompts", lambda: __import__("app.prompts"))
test_import("app.evals", lambda: __import__("app.evals"))

# Third-party libraries we'll use heavily
test_import("langchain", lambda: __import__("langchain"))
test_import("langgraph", lambda: __import__("langgraph"))
test_import("langsmith", lambda: __import__("langsmith"))
test_import("weaviate", lambda: __import__("weaviate"))
test_import("fastapi", lambda: __import__("fastapi"))
test_import("tree_sitter", lambda: __import__("tree_sitter_python"))

print("\n" + "─" * 40)
print("Smoke test complete.\n")
