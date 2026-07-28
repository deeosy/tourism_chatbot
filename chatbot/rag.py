import json
import re
from pathlib import Path

DB_PATH = Path("data/chromadb")

_knowledge: list[dict] | None = None

# Map region-related keywords to their canonical region names
_REGION_KEYWORDS = {
    "accra": ["accra", "greater accra", "capital", "labadi", "jamestown", "osu", "kotoka"],
    "central region": ["cape coast", "central", "elmina", "kakum", "castle", "slave"],
    "ashanti region": ["kumasi", "ashanti", "manhyia", "kejetia", "bonwire", "kente"],
    "volta region": ["volta", "ho", "wli", "afadjato", "tafi atome", "monkey sanctuary"],
    "northern region": ["northern", "tamale", "mole", "larabanga", "safari", "elephant", "savannah"],
    "western region": ["western", "busua", "axim", "nzulezu", "surf", "dixcove"],
    "eastern region": ["eastern", "akosombo", "lake volta", "boti", "akwapim", "koforidua"],
}

_ITINERARY_KEYWORDS = {"itinerary", "plan", "trip", "days", "route", "schedule", "tour", "visit"}


def _load_knowledge() -> list[dict]:
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


def _detect_regions(query: str) -> list[str]:
    """Return canonical region names mentioned in the query."""
    query_lower = query.lower()
    matched = []
    for region, keywords in _REGION_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                matched.append(region)
                break
    return matched


def _is_itinerary_query(query: str) -> bool:
    """Check if the query is about itinerary/trip planning."""
    words = set(re.findall(r"[a-zA-Z]{3,}", query.lower()))
    return bool(words & _ITINERARY_KEYWORDS)


def _score_entry(entry: dict, query_words: set[str], matched_regions: list[str]) -> int:
    """Score how relevant a knowledge entry is to the user's query."""
    text = f"{entry['attraction']} {entry['region']} {entry['type']} {entry['description']} {entry.get('details', '')}".lower()
    score = 0
    for word in query_words:
        if len(word) < 3:
            continue
        score += text.count(word) * 2

    # Major boost if entry's region matches a detected region
    if entry["region"] in matched_regions or entry["region"].lower() in [r.lower() for r in matched_regions]:
        score += 15

    # Boost for "all regions" reference entries on itinerary queries
    if entry["region"] == "All Regions":
        score += 5

    return score


async def query_knowledge_base(query: str, n_results: int = 5) -> str | None:
    kb = _load_knowledge()
    if not kb:
        return None

    query_words = set(re.findall(r"[a-zA-Z]{3,}", query.lower()))
    matched_regions = _detect_regions(query)
    is_itinerary = _is_itinerary_query(query)

    # Add specific multi-word patterns for better matching
    if "cape coast castle" in query.lower() or "slave castle" in query.lower() or "door of no return" in query.lower():
        query_words.add("cape_coast_castle")
    if "elmina castle" in query.lower() or "st george" in query.lower():
        query_words.add("elmina_castle")
    if "canopy walkway" in query.lower():
        query_words.add("canopy_walkway")

    # Score and sort entries
    scored = [(_score_entry(e, query_words, matched_regions), e) for e in kb]
    scored.sort(key=lambda x: -x[0])

    # If we detected regions, ensure at least 2 entries from those regions show up
    forced_entries = []
    if matched_regions:
        region_entries = [
            e for s, e in scored
            if e["region"] in matched_regions and e not in forced_entries
        ]
        forced_entries.extend(region_entries[:3])

    # If itinerary query, ensure the travel overview is included
    if is_itinerary:
        overview = next((e for e in kb if e["attraction"] == "Region Travel Times Overview"), None)
        if overview and overview not in forced_entries:
            forced_entries.append(overview)

    # Build the final list: forced entries first, then highest-scored non-duplicates
    seen = {id(e) for e in forced_entries}
    remaining = [e for s, e in scored if id(e) not in seen and s > 0]
    top = forced_entries + remaining[:max(0, n_results - len(forced_entries))]

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
            times = "\n".join(
                f"  {k.replace('_', ' ').title()}: {v}"
                for k, v in entry["travel_times"].items()
            )
            part += f"\nTravel times:\n{times}"
        context_parts.append(part)

    return "\n\n".join(context_parts)


def is_rag_available() -> bool:
    kb = _load_knowledge()
    if kb:
        return True
    return Path("data/chromadb").exists() and any(Path("data/chromadb").iterdir())
