from datetime import datetime

from openai import AsyncOpenAI
from .config import get_config, load_system_prompt
from .rag import query_knowledge_base

# Module-level cache for the OpenAI client and system prompt
_system_prompt: str | None = None
_client: AsyncOpenAI | None = None


def _ensure_llm():
    global _system_prompt, _client
    cfg = get_config()
    if cfg["is_configured"] and _client is None:
        _client = AsyncOpenAI(api_key=cfg["api_key"])
    if _system_prompt is None:
        _system_prompt = load_system_prompt()


# Injects the current date into the system prompt so the LLM knows what "now" is.
def _inject_date(prompt: str) -> str:
    today = datetime.now().strftime("%A, %B %d, %Y")
    return (
        f"Today's date is {today}. When the user mentions dates or seasons, "
        f"use today as your reference point.\n\n"
        f"IMPORTANT: When the user's message includes a 'Relevant information from "
        f"the knowledge base' section, that data is verified and accurate — especially "
        f"travel times, distances, prices, and opening hours. ALWAYS use that "
        f"information over your own training data when there is any conflict.\n\n"
        f"{prompt}"
    )


# Sends the user's message to OpenAI along with relevant RAG context and history.
# Returns the LLM's response, or None if the API is not configured.
async def generate_llm_response(
    message: str, history: list[list[str]] | None = None
) -> str | None:
    _ensure_llm()
    if _client is None:
        return None

    cfg = get_config()

    # Retrieve relevant context from the knowledge base
    rag_context = await query_knowledge_base(message, n_results=5)
    if rag_context:
        message = f"{message}\n\nRelevant information from the knowledge base:\n{rag_context}"

    # Build conversation messages: system + history + current user message
    messages = [
        {"role": "system", "content": _inject_date(_system_prompt)},
    ]

    if history:
        for user_msg, bot_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": bot_msg})

    messages.append({"role": "user", "content": message})

    try:
        resp = await _client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Sorry, I ran into an issue connecting to the AI: {e}"
