import httpx
from urllib.parse import quote_plus


async def search_web(query: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            encoded = quote_plus(query)
            url = f"https://lite.duckduckgo.com/lite?q={encoded}"
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None

            import re

            snippets = re.findall(
                r'class="result-snippet">(.*?)</(?:a|td)>',
                resp.text,
                re.DOTALL,
            )
            if not snippets:
                snippets = re.findall(
                    r'class="result__snippet">(.*?)</(?:a|td)>',
                    resp.text,
                    re.DOTALL,
                )

            if snippets:
                clean = []
                for s in snippets[:3]:
                    text = re.sub(r"<[^>]+>", "", s).strip()
                    if text:
                        clean.append(text)
                if clean:
                    return "\n\n".join(clean)

            return None
    except Exception:
        return None
