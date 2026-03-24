# Parses source code files into semantic chunks using tree-sitter AST parsing

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser


# ── Data model ────────────────────────────────────────────────────────────────


@dataclass
class CodeChunk:
    """A single semantic unit of code extracted from a source file."""

    content: str  # the raw source code of this chunk
    file_path: str  # relative path to the source file
    repo_name: str  # which repo this came from
    language: str  # python | javascript | typescript
    chunk_type: str  # function | class | module (fallback)
    symbol_name: str  # name of the function or class, or filename for module
    docstring: str  # extracted docstring/leading comment, or empty string
    start_line: int  # 1-indexed line where this chunk starts
    end_line: int  # 1-indexed line where this chunk ends


# ── Language setup ────────────────────────────────────────────────────────────

# Maps file extensions to (tree-sitter language module, language name)
# We build the Language object lazily so startup is fast
_LANGUAGE_MAP: dict[str, tuple] = {
    ".py": (tspython.language(), "python"),
    ".js": (tsjavascript.language(), "javascript"),
    ".ts": (tstypescript.language_typescript(), "typescript"),
    ".tsx": (tstypescript.language_tsx(), "typescript"),
}

# Node types that represent a meaningful chunk in each language
# These are the tree-sitter node type names for function/class definitions
_CHUNK_NODE_TYPES = {
    "python": {"function_definition", "class_definition"},
    "javascript": {
        "function_declaration",
        "class_declaration",
        "arrow_function",
        "method_definition",
    },
    "typescript": {
        "function_declaration",
        "class_declaration",
        "arrow_function",
        "method_definition",
    },
}


def _get_parser(extension: str) -> tuple[Parser, str] | None:
    """Returns a configured tree-sitter Parser and language name for a file extension."""
    entry = _LANGUAGE_MAP.get(extension.lower())
    if not entry:
        return None
    lang_obj, lang_name = entry
    parser = Parser(Language(lang_obj))
    return parser, lang_name


# ── Docstring extraction ───────────────────────────────────────────────────────


def _extract_docstring(node, source_bytes: bytes, language: str) -> str:
    """
    Tries to extract a docstring or leading comment from a function/class node.
    Returns empty string if none found.
    """
    if language == "python":
        # In Python, docstrings are the first expression_statement child
        # containing a string node inside the function/class body
        for child in node.children:
            if child.type == "block":
                for block_child in child.children:
                    if block_child.type == "expression_statement":
                        for expr_child in block_child.children:
                            if expr_child.type == "string":
                                raw = source_bytes[
                                    expr_child.start_byte : expr_child.end_byte
                                ].decode("utf-8", errors="replace")
                                # strip the triple quotes
                                return raw.strip("\"' \n").strip()
    return ""


def _extract_symbol_name(node, source_bytes: bytes) -> str:
    """Extracts the name identifier from a function or class node."""
    for child in node.children:
        if child.type == "identifier":
            return source_bytes[child.start_byte : child.end_byte].decode(
                "utf-8", errors="replace"
            )
    return "unknown"


# ── Core parsing logic ────────────────────────────────────────────────────────


def parse_file(
    file_path: str,
    source_code: str,
    repo_name: str,
) -> list[CodeChunk]:
    """
    Parses a source file into a list of CodeChunks.
    Each top-level function and class becomes its own chunk.
    Falls back to a single whole-file chunk if no definitions are found.
    """
    ext = Path(file_path).suffix
    parser_result = _get_parser(ext)

    if parser_result is None:
        # unsupported file type — return as a single raw chunk
        return [_whole_file_chunk(file_path, source_code, repo_name, "unknown")]

    parser, language = parser_result
    source_bytes = source_code.encode("utf-8")

    # parse() returns the root node of the AST
    tree = parser.parse(source_bytes)
    root = tree.root_node

    chunk_types = _CHUNK_NODE_TYPES.get(language, set())
    chunks: list[CodeChunk] = []

    # walk only the top-level children of the file
    # we don't recurse into nested functions to keep chunks focused
    for node in root.children:
        if node.type not in chunk_types:
            continue

        content = source_bytes[node.start_byte : node.end_byte].decode(
            "utf-8", errors="replace"
        )
        symbol_name = _extract_symbol_name(node, source_bytes)
        docstring = _extract_docstring(node, source_bytes, language)

        # tree-sitter uses 0-indexed rows, convert to 1-indexed for humans
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        chunk_type = "function" if "function" in node.type else "class"

        chunks.append(
            CodeChunk(
                content=content,
                file_path=file_path,
                repo_name=repo_name,
                language=language,
                chunk_type=chunk_type,
                symbol_name=symbol_name,
                docstring=docstring,
                start_line=start_line,
                end_line=end_line,
            )
        )

    # fallback: if the file has no top-level functions/classes (e.g. a config
    # file or a script), store the whole file as a single module chunk
    if not chunks:
        return [_whole_file_chunk(file_path, source_code, repo_name, language)]

    return chunks


def _whole_file_chunk(
    file_path: str,
    source_code: str,
    repo_name: str,
    language: str,
) -> CodeChunk:
    """Creates a single chunk representing the entire file."""
    lines = source_code.splitlines()
    return CodeChunk(
        content=source_code,
        file_path=file_path,
        repo_name=repo_name,
        language=language,
        chunk_type="module",
        symbol_name=Path(file_path).name,
        docstring="",
        start_line=1,
        end_line=len(lines),
    )
