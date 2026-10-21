from langchain_core.tools import tool
import httpx
from urllib.parse import parse_qs, urlparse
from bs4 import BeautifulSoup
from src.clients import get_http_client


@tool
async def read_contents_from_webpage(url: str) -> str:
    """Download a webpage and extract its content
    
    Args: 
        url: Webpage url.
    Returns: 
        Extracted Webpage Text"""
    
    if url.startswith("//"):
        url = f"https:{url}"

    #Extracting the real URL from DDG Re-direct URL
    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc:
        params = parse_qs(parsed.query)
        if "uddg" in params:
            url = params["uddg"][0]

    try:
        response = await get_http_client().get(url, timeout=15.0)
        response.raise_for_status()
    except httpx.HTTPError as error:
        return f"Webpage download failed: {error}"

    soup = BeautifulSoup(response.text, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    for element in soup.select('[class*="line_number"]'):
        element.decompose()

    text = soup.get_text("\n", strip=True)
    return f"Source URL: {url}\n\n{text[:10000]}"
