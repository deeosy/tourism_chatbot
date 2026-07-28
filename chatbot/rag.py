import json
import re
from pathlib import Path

DB_PATH = Path("data/chromadb")

_knowledge: list[dict] | None = None


def _load_knowledge() -> list[dict]:
    """Load the curated knowledge base from JSON."""
    global _knowledge
    if _knowledge is not None:
        return _knowledge

    kb_path = Path("data/processed/knowledge_base.json")
    if kb_path.exists():
        with open(kb_path, encoding="utf-8") as f:
            _knowledge = json.load(f)
    else:
        _knowledge = []

    return _knowledge


def _score_entry(entry: dict, query_words: set[str]) -> int:
    """Score how relevant a knowledge entry is to the user's query."""
    score = 0
    text = f"{entry['attraction']} {entry['region']} {entry['type']} {entry['description']} {entry.get('details', '')}".lower()
    for word in query_words:
        if len(word) < 3:
            continue
        count = text.count(word)
        score += count
    return score


# Queries the curated knowledge base (JSON) for the most relevant entries
# matching the user's question. Falls back to ChromaDB if no JSON exists.
async def query_knowledge_base(query: str, n_results: int = 5) -> str | None:
    kb = _load_knowledge()
    if not kb:
        return None

    # Tokenize query into meaningful words
    query_words = set(re.findall(r"[a-zA-Z]{3,}", query.lower()))
    # Add specific multi-word patterns
    if "cape coast castle" in query.lower() or "slave castle" in query.lower() or "door of no return" in query.lower():
        query_words.add("cape_coast_castle")
    if "elmina castle" in query.lower() or "st george" in query.lower():
        query_words.add("elmina_castle")
    if "canopy walkway" in query.lower():
        query_words.add("canopy_walkway")

    # Score and sort entries
    scored = [(_score_entry(e, query_words), e) for e in kb]
    scored.sort(key=lambda x: -x[0])

    # Take top results (only if they have a positive score)
    top = [e for s, e in scored if s > 0][:n_results]

    if not top:
        return None

    # Format results
    context_parts = []
    for i, entry in enumerate(top):
        price = entry.get("practical", {}).get("price_range", "")
        hours = entry.get("practical", {}).get("hours", "")
        part = f"[{i + 1}: {entry['attraction']} ({entry['region']})] {entry['description']}"
        if entry.get("details"):
            part += f"\nDetails: {entry['details']}"
        if hours:
            part += f"\nHours: {hours}"
        if price:
            part += f"\nPrice: {price}"
        if entry.get("travel_times"):
            times = "\n".join(f"  {k.replace('_', ' ').title()}: {v}" for k, v in entry["travel_times"].items())
            part += f"\nTravel times:\n{times}"
        context_parts.append(part)

    return "\n\n".join(context_parts)


# Quick check: is any knowledge source available?
def is_rag_available() -> bool:
    kb = _load_knowledge()
    if kb:
        return True
    return Path("data/chromadb").exists() and any(Path("data/chromadb").iterdir())
