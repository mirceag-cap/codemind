# Clones a GitHub repo, ingests it into Weaviate, then cleans up

import sys
import os
import subprocess
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.vectordb.schema import get_client, create_schema
from app.rag.ingestion import ingest_codebase


def clone_repo(github_url: str, target_dir: str) -> bool:
    """
    Clones a GitHub repo into target_dir using git.
    Returns True on success, False on failure.
    """
    print(f"📥 Cloning {github_url}...")
    result = subprocess.run(
        ["git", "clone", "--depth=1", github_url, target_dir],
        # depth=1 fetches only the latest commit — much faster than full history
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"❌ Clone failed:\n{result.stderr}")
        return False

    print(f"✅ Cloned into {target_dir}")
    return True


def repo_name_from_url(url: str) -> str:
    """Extracts a clean repo name from a GitHub URL."""
    # e.g. https://github.com/tiangolo/fastapi → fastapi
    name = url.rstrip("/").split("/")[-1]
    # strip .git suffix if present
    if name.endswith(".git"):
        name = name[:-4]
    return name


def main():
    if len(sys.argv) < 2:
        print("Usage: python ingest_github.py <github_url> [repo_name]")
        print("Example: python ingest_github.py https://github.com/tiangolo/fastapi")
        sys.exit(1)

    github_url = sys.argv[1]
    repo_name = sys.argv[2] if len(sys.argv) > 2 else repo_name_from_url(github_url)

    # create a temp directory — we control when it gets deleted
    tmp_dir = tempfile.mkdtemp(prefix="codemind_")

    try:
        # step 1: clone
        success = clone_repo(github_url, tmp_dir)
        if not success:
            return

        # step 2: ingest
        print(f"\n🚀 Ingesting repo '{repo_name}'...")
        with get_client() as client:
            create_schema(client)
            summary = ingest_codebase(
                root_path=tmp_dir,
                repo_name=repo_name,
                client=client,
            )

        print(f"\n🎉 Done! Summary: {summary}")

    finally:
        # always clean up the cloned repo regardless of success or failure
        # without this, large repos would accumulate on disk silently
        print(f"\n🧹 Cleaning up {tmp_dir}...")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        print("Done.")


if __name__ == "__main__":
    main()
