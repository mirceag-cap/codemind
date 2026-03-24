# One-off script — creates the Weaviate schema for CodeMind

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.vectordb.schema import get_client, create_schema


def main():
    print("Connecting to Weaviate...")
    # `with` block ensures the client connection is closed cleanly after use
    with get_client() as client:
        print(f"Connected ✅  (Weaviate ready: {client.is_ready()})")
        create_schema(client)


def wait_for_weaviate(client, retries=10, delay=2):
    """Polls Weaviate until it's ready or gives up after retries."""
    for i in range(retries):
        if client.is_ready():
            return True
        print(f"  ⏳ Weaviate not ready yet, retrying ({i + 1}/{retries})...")
        time.sleep(delay)
    return False


def main():
    print("Connecting to Weaviate...")
    with get_client() as client:
        ready = wait_for_weaviate(client)
        if not ready:
            print("❌ Weaviate did not become ready in time. Is Docker running?")
            return
        print(f"Connected ✅  (Weaviate ready: True)")
        create_schema(client)


if __name__ == "__main__":
    main()
