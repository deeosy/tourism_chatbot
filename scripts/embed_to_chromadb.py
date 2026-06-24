"""
Embed chunks and store in ChromaDB.
Uses OpenAI embeddings when API key is configured,
falls back to Chroma's built-in all-MiniLM-L6-v2 otherwise.
"""

import json
import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

CHUNKS_PATH = Path("data/chunks/chunked_knowledge_base.json")
DB_PATH = Path("data/chromadb")
COLLECTION_NAME = "ghana_tourism"
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


def get_embedding_function():
    api_key = os.getenv("OPENAI_API_KEY", "")
    is_configured = bool(api_key) and api_key != "your-openai-api-key-here"

    if is_configured:
        from chromadb.utils import embedding_functions as ef

        return (
            ef.OpenAIEmbeddingFunction(api_key=api_key, model_name=EMBEDDING_MODEL),
            EMBEDDING_MODEL,
        )
    else:
        from chromadb.utils import embedding_functions as ef

        return (
            ef.DefaultEmbeddingFunction(),
            "all-MiniLM-L6-v2",
        )


def embed_texts_fn(api_key, texts):
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [r.embedding for r in resp.data]


def main():
    chunks_data = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    chunks = chunks_data["chunks"]

    print(f"Loading {len(chunks)} chunks...")

    embedding_fn, model_name = get_embedding_function()
    print(f"Using embedding model: {model_name}")

    client = chromadb.PersistentClient(
        path=str(DB_PATH),
        settings=Settings(anonymized_telemetry=False),
    )

    existing = client.list_collections()
    coll_names = [c.name for c in existing]
    if COLLECTION_NAME in coll_names:
        print(f"Collection '{COLLECTION_NAME}' exists. Deleting and recreating...")
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={
            "description": "Ghana tourism knowledge base chunks",
            "model": model_name,
        },
    )

    ids = []
    documents = []
    metadatas = []

    for c in chunks:
        ids.append(c["chunk_id"])
        documents.append(c["text"])
        metadatas.append(
            {
                "region": c["region"],
                "attraction": c["attraction"],
                "chunk_index": c["chunk_index"],
                "total_chunks": c["total_chunks_for_entry"],
                "char_count": c["char_count"],
            }
        )

    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch_end = min(i + batch_size, len(ids))
        print(f"  Adding batch {i // batch_size + 1} ({i}-{batch_end - 1})...")

        collection.add(
            ids=ids[i:batch_end],
            documents=documents[i:batch_end],
            metadatas=metadatas[i:batch_end],
        )

    stored = collection.count()
    print(f"\nDone! {stored} chunks stored in '{COLLECTION_NAME}'")
    print(f"Database location: {DB_PATH.resolve()}")

    print("\nSample query test:")
    results = collection.query(query_texts=["What is Cape Coast Castle?"], n_results=3)
    for i, (doc, meta, dist) in enumerate(
        zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
    ):
        print(f"\n  Result {i + 1} (distance: {dist:.3f}):")
        print(
            f"    [{meta['region']}] {meta['attraction']} (chunk {meta['chunk_index']}/{meta['total_chunks']})"
        )
        print(f"    {doc[:100]}...")


if __name__ == "__main__":
    main()
