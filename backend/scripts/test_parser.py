# Quick test — parses a sample Python snippet and prints the chunks

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.parser import parse_file

SAMPLE_CODE = '''
def add(a: int, b: int) -> int:
    """Adds two numbers together."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiplies two numbers."""
    return a * b

class Calculator:
    """A simple calculator class."""

    def divide(self, a: int, b: int) -> float:
        return a / b
'''

chunks = parse_file(
    file_path="sample/math_utils.py",
    source_code=SAMPLE_CODE,
    repo_name="test-repo",
)

print(f"\n📦 Found {len(chunks)} chunks:\n" + "─" * 50)
for chunk in chunks:
    print(f"\n  [{chunk.chunk_type}] {chunk.symbol_name}")
    print(f"  Lines  : {chunk.start_line}–{chunk.end_line}")
    print(f"  Docstring: {chunk.docstring or '(none)'}")
    print(f"  Preview: {chunk.content[:60].strip()}...")
print("\n" + "─" * 50)
