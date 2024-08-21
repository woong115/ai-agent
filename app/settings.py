from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    stage: str = "local"
    debug: bool = True
    self_host: str = "http://api:5000"

    redis_url: str = "redis://redis"
    chroma_persist_directory: str = "store/chroma"
    chroma_collection_name: str = "mydata"

    pinecone_api_key: str
    pinecone_persist_directory: str = "store/pinecone"
    pinecone_index_name: str = "mydata-index"

    openai_api_key: str
    openai_llm_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-large"

    # upstage_api_key: str
    # upstage_embedding_model: str = "solar-embedding-1-large"

    # langchain_tracing_v2: str
    # langchain_endpoint: str
    # langchain_api_key: str
    # langchain_project: str

    max_history_k: int = 10
    pdf_dir: str = "pdfs"
    preprocessed_markdown_dir: str = "app/static/data"
    docstore_dir: str = "store/docstore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
