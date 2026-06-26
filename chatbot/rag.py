import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path("data/chromadb")
COLLECTION_NAME = "ghana_tourism"
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

_client = None
_collection = None


def _ensure_db():
    global _client, _collection
    if _client is not None:
        return

    if not DB_PATH.exists():
        _client = None
        return

    # Connect to the local ChromaDB persistent store
    _client = chromadb.PersistentClient(
        path=str(DB_PATH),
        settings=Settings(anonymized_telemetry=False),
    )

    try:
        _collection = _client.get_collection(COLLECTION_NAME)
    except Exception:
        _collection = None


# Queries the ChromaDB vector store for chunks most similar to the user's question.
# Uses OpenAI embeddings via ChromaDB's built-in embedding function.
# Returns a formatted string of the top N results (with source attribution).
async def query_knowledge_base(query: str, n_results: int = 5) -> str | None:
    _ensure_db()
    if _collection is None:
        return None

    try:
        results = _collection.query(query_texts=[query], n_results=n_results)
    except Exception:
        return None

    if not results["documents"] or not results["documents"][0]:
        return None

    # Format each chunk with its source location for transparency
    context_parts = []
    for i, (doc, meta) in enumerate(
        zip(results["documents"][0], results["metadatas"][0])
    ):
        location = f"{meta['attraction']} ({meta['region']})"
        context_parts.append(f"[Source {i + 1}: {location}]\n{doc.strip()}")

    return "\n\n".join(context_parts)


# Quick check: is the vector store available on disk?
def is_rag_available() -> bool:
    return DB_PATH.exists() and any(DB_PATH.iterdir())
