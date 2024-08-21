from httpx import AsyncClient


async def get_http_client(base_url: str = None, timeout: int = 30):
    if base_url:
        http_client = AsyncClient(base_url=base_url, timeout=timeout)
    else:
        http_client = AsyncClient(timeout=timeout)
    yield http_client
    await http_client.aclose()
