from langchain_core.tools import tool
from src.clients import get_http_client
from src.config import settings
import httpx
from urllib.parse import parse_qs, urlparse
from bs4 import BeautifulSoup

def resolve_ddg_url(url: str) -> str:
    """Resolve a DDG URL"""
    if url.startswith("//"):
        url = f"https:{url}"
    parsed = urlparse(url)
    if parsed.netloc.endswith("duckduckgo.com"):
        target = parse_qs(parsed.query).get("uddg")
        if target:
            return target[0]
    return url

@tool
async def duckduckgo_web_search(query: str, max_results: int = 1) -> str:
    """Search DuckDuckGo and return result titles, URLs, and snippets."""
    if not query.strip():
        return "Please pass a non-empty search query"
    if max_results not in range(1, 2):
        return "The max_results must be 1"

    try:
        response = await get_http_client().post(
            settings.ddg_html_url, data={"q": query}, timeout=15.0
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        return f"DuckDuckGo Web Search Failed {error}"

    results: list[str] = []
    soup = BeautifulSoup(response.text, "html.parser")
    for item in soup.select(".result"):
        classes = item.get("class") or []
        link = item.select_one(".result__a")

        if link is None or "result--ad" in classes:
            continue

        href = link.get("href", "")
        if not isinstance(href, str):
            continue

        url = resolve_ddg_url(href)

        snippet = item.select_one(".result__snippet")

        results.append(
            f"Title: {link.get_text(' ', strip=True)}\n"
            f"URL: {url}\n"
            f"Snippets: {snippet.get_text(' ', strip=True) if snippet else ''}"
        )
        if len(results) >= max_results:
            break
    return "\n".join(results) if results else "No DDG Web Search Results were found"
