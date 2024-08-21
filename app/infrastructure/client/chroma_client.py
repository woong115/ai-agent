import chromadb


async def get_chroma_client(host: str, port: int):
    client = await chromadb.AsyncHttpClient(host=host, port=port)
    yield client
