from openai import AsyncOpenAI
from .config import get_config, load_system_prompt
from .rag import query_knowledge_base


_system_prompt: str | None = None
_client: AsyncOpenAI | None = None


def _ensure_llm():
    global _system_prompt, _client
    cfg = get_config()
    if cfg["is_configured"] and _client is None:
        _client = AsyncOpenAI(api_key=cfg["api_key"])
    if _system_prompt is None:
        _system_prompt = load_system_prompt()


async def generate_llm_response(message: str) -> str | None:
    _ensure_llm()
    if _client is None:
        return None

    cfg = get_config()

    rag_context = await query_knowledge_base(message, n_results=5)
    context_block = ""
    if rag_context:
        context_block = (
            "\n\nRelevant information from the knowledge base:\n" + rag_context
        )

    try:
        resp = await _client.chat.completions.create(
            model=cfg["model"],
            messages=[
                {"role": "system", "content": _system_prompt},
                {"role": "user", "content": message + context_block},
            ],
            temperature=0.7,
            max_tokens=800,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Sorry, I ran into an issue connecting to the AI: {e}"
