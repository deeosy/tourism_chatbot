"""
Chunk the corrected knowledge base into overlapping segments for RAG.
Uses sliding-window overlap at the word level.
"""

import json
import re
from pathlib import Path

INPUT_PATH = Path("data/processed/corrected_knowledge_base.json")
OUTPUT_PATH = Path("data/chunks/chunked_knowledge_base.json")

DEFAULT_CHUNK_SIZE = 600
DEFAULT_OVERLAP_PCT = 15.0


def clean_content(text: str) -> str:
    text = re.sub(r"^Ghana Tourism Knowledge Unit\s*\n+", "", text).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text_sliding(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap_percentage: float = DEFAULT_OVERLAP_PCT,
) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunk_chars = chunk_size
    overlap_chars = max(1, int(chunk_size * overlap_percentage / 100))
    min_chunk = chunk_size // 3

    chunks = []
    start = 0

    while start < len(words):
        chars = 0
        end = start
        for w in words[start:]:
            chars += len(w) + 1
            if chars > chunk_chars:
                break
            end += 1

        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        remaining_chars = sum(len(w) + 1 for w in words[end:])
        if remaining_chars <= overlap_chars:
            break

        overlap_used = 0
        new_start = end
        for j in range(end - 1, start - 1, -1):
            overlap_used += len(words[j]) + 1
            if overlap_used > overlap_chars:
                new_start = j + 1
                break

        remaining_from_new = sum(len(w) + 1 for w in words[new_start:])
        if remaining_from_new < min_chunk:
            break

        if new_start <= start:
            new_start = start + 1
        if new_start >= len(words):
            break

        start = new_start

    return chunks


def main():
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    chapters = data["chapters"]

    all_chunks = []
    total_original = 0
    region_counts = {}
    attraction_entries = {}
    entry_counter: dict[str, int] = {}

    for ch in chapters:
        content = clean_content(ch["content"])
        region = ch["region"]
        attraction = ch["attraction"]

        if region == "Unknown" and attraction == "Unknown":
            continue
        if not content:
            continue

        total_original += 1

        entry_key = f"{region}_{attraction}"
        entry_counter[entry_key] = entry_counter.get(entry_key, 0) + 1
        entry_seq = entry_counter[entry_key]

        text_chunks = chunk_text_sliding(
            content,
            chunk_size=DEFAULT_CHUNK_SIZE,
            overlap_percentage=DEFAULT_OVERLAP_PCT,
        )

        for i, chunk in enumerate(text_chunks):
            prefix = region.replace(" ", "_") + "_" + attraction.replace(" ", "_")
            cid = f"{prefix}_e{entry_seq}_c{i + 1}"
            all_chunks.append(
                {
                    "chunk_id": cid,
                    "region": region,
                    "attraction": attraction,
                    "chunk_index": i + 1,
                    "total_chunks_for_entry": len(text_chunks),
                    "text": chunk,
                    "char_count": len(chunk),
                    "word_count": len(chunk.split()),
                }
            )

        region_counts[region] = region_counts.get(region, 0) + len(text_chunks)
        attraction_entries[attraction] = attraction_entries.get(attraction, 0) + 1

    output = {
        "chunk_config": {
            "chunk_size_chars": DEFAULT_CHUNK_SIZE,
            "overlap_percentage": DEFAULT_OVERLAP_PCT,
            "overlap_chars": int(DEFAULT_CHUNK_SIZE * DEFAULT_OVERLAP_PCT / 100),
        },
        "stats": {
            "total_entries": total_original,
            "total_chunks": len(all_chunks),
            "unique_regions": len(set(c["region"] for c in all_chunks)),
            "unique_attractions": len(set(c["attraction"] for c in all_chunks)),
            "avg_chunks_per_entry": round(len(all_chunks) / max(total_original, 1), 1),
        },
        "chunks": all_chunks,
    }

    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Chunking complete:")
    print(f"  Entries processed: {total_original}")
    print(f"  Total chunks: {len(all_chunks)}")
    print(
        f"  Chunk size: {DEFAULT_CHUNK_SIZE} chars with {DEFAULT_OVERLAP_PCT}% overlap ({int(DEFAULT_CHUNK_SIZE * DEFAULT_OVERLAP_PCT / 100)} chars)"
    )
    print(
        f"  Avg chunks per entry: {round(len(all_chunks) / max(total_original, 1), 1)}"
    )
    print()
    print("Per region:")
    for r in sorted(region_counts):
        print(f"  {r}: {region_counts[r]} chunks")
    print()
    print("Per attraction:")
    for a in sorted(attraction_entries):
        print(f"  {a}: {attraction_entries[a]} entries")


if __name__ == "__main__":
    main()
