import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_config() -> dict:
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    is_configured = bool(api_key) and api_key != "your-openai-api-key-here"

    return {
        "api_key": api_key,
        "model": model,
        "is_configured": is_configured,
    }


def load_system_prompt() -> str:
    skill_path = Path(__file__).resolve().parent.parent / "skill.md"
    if skill_path.exists():
        content = skill_path.read_text(encoding="utf-8")
        front_matter_end = content.find("---", 3)
        if front_matter_end != -1:
            content = content[front_matter_end + 3 :].strip()
        return content
    return "You are a knowledgeable, friendly local guide to Ghana."
