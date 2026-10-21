import httpx 

http_client: httpx.AsyncClient | None = None

def create_http_client() -> httpx.AsyncClient:
    global http_client
    http_client = httpx.AsyncClient(headers={"user-Agent": "Mozilla/5.0"}, follow_redirects=True)
    return http_client

def get_http_client() -> httpx.AsyncClient:
    return http_client if http_client is not None else create_http_client()


async def close_http_client() -> None:
    global http_client
    if http_client is not None:
        await http_client.aclose()
        http_client = None