import re
from .engine import (
    INTENTS,
    REGIONS,
    TOPICS,
    similarity,
    get_itinerary_reply,
    get_practical_reply,
)
from .search import search_web
from .llm import generate_llm_response
from .config import get_config


def _is_llm_configured() -> bool:
    return get_config()["is_configured"]


# Counts how many keywords from a list appear in the user's text.
# Returns a score (1 point per keyword found).
def _match_keywords(text: str, keywords: list[str]) -> float:
    text_lower = text.lower()
    score = 0.0
    for kw in keywords:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, text_lower):
            score += 1.0
    return score


# Check if the message matches a simple greeting/thanks/goodbye intent.
# Returns the corresponding response immediately if matched.
def _check_intents(text: str) -> str | None:
    for intent_name, intent in INTENTS.items():
        for pattern in intent["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                return intent["response"]
    return None


# Find the best-matching region from the user's text.
# Returns a tuple of (region_response, optional_subtopic_response).
def _match_region(text: str) -> tuple[str, str | None] | None:
    best_score = 0.0
    best_key = None
    best_subtopic = None

    for key, region in REGIONS.items():
        score = _match_keywords(text, region["keywords"])
        if score > best_score:
            best_score = score
            best_key = key

    if best_key and best_score >= 1.0:
        region = REGIONS[best_key]
        # Check if a specific subtopic within the region was mentioned
        for sub_name, sub_text in region.get("subtopics", {}).items():
            pattern = r"\b" + re.escape(sub_name) + r"\b"
            if re.search(pattern, text.lower()):
                best_subtopic = sub_text
                break
        return (region["response"], best_subtopic)

    return None


# Match non-itinerary topics (food, visa, transport, safety, etc.)
def _match_topic(text: str) -> str | None:
    best_score = 0.0
    best_key = None

    for key, topic in TOPICS.items():
        if topic.get("is_itinerary"):
            continue  # itinerary is handled separately
        score = _match_keywords(text, topic["keywords"])
        if score > best_score:
            best_score = score
            best_key = key

    if best_key and best_score >= 1.0:
        return TOPICS[best_key]["response"]

    return None


# Check if the user is asking for an itinerary (trip plan).
def _check_itinerary(text: str) -> str | None:
    for key, topic in TOPICS.items():
        if topic.get("is_itinerary"):
            score = _match_keywords(text, topic["keywords"])
            if score >= 1.0:
                return get_itinerary_reply(text)
    return None


# Check if the user is asking about practical info (money, SIM cards, etc.)
def _check_practical(text: str) -> str | None:
    return get_practical_reply(text)


# ----- Main entry point -----
# Called by Gradio when the user submits a message.
# Tries strategies in order of quality:
#   1. LLM (OpenAI) with RAG context  ─ best answer
#   2. Simple intent matching          ─ fast for greetings
#   3. Itinerary builder               ─ for trip planning
#   4. Region matching                 ─ for destination questions
#   5. Topic matching                  ─ for food/visa/etc.
#   6. Practical info                  ─ for costs/SIM cards
#   7. Web search (DuckDuckGo)        ─ fallback for unknown queries
#   8. Generic "tell me more" prompt   ─ last resort
async def generate_response(message: str) -> str:
    text = message.strip()

    if not text:
        return "Ask me anything about travelling to Ghana!"

    # 1. If an OpenAI API key is configured, use the LLM (best quality)
    if _is_llm_configured():
        llm_reply = await generate_llm_response(text)
        if llm_reply:
            return llm_reply

    # 2. Rule-based fallbacks (work without an API key too)
    intent_reply = _check_intents(text)
    if intent_reply:
        return intent_reply

    itinerary_reply = _check_itinerary(text)
    if itinerary_reply:
        return itinerary_reply

    region_match = _match_region(text)
    if region_match:
        main_response, subtopic = region_match
        if subtopic:
            return subtopic
        return main_response

    topic_reply = _match_topic(text)
    if topic_reply:
        return topic_reply

    practical_reply = _check_practical(text)
    if practical_reply:
        return practical_reply

    # 3. Web search as a final fallback
    web_result = await search_web(f"Ghana tourism {text}")
    if web_result:
        return (
            "I searched online for the latest info on that. Here's what I found:\n\n"
            f"{web_result}\n\n"
            "Want me to dig deeper or help with something else about Ghana?"
        )

    # 4. If nothing matched, prompt the user for more detail
    return (
        "That's a great question! I want to make sure I give you good info.\n\n"
        "Could you tell me more about what you're looking for? For example:\n"
        "- A specific **destination** (Accra, Kumasi, Cape Coast, etc.)\n"
        "- **Activities** (beaches, hiking, history, food)\n"
        "- **Practical info** (visas, transport, safety, best time)\n"
        "- Or I can help **plan an itinerary** - just tell me how many days you have!"
    )
