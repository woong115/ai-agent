import os

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from langchain.storage import LocalFileStore
from langchain.storage._lc_store import create_kv_docstore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore


@pytest.fixture(scope="function")
def openai_embeddings(settings):
    yield OpenAIEmbeddings(model=settings.openai_embedding_model)


@pytest.fixture(scope="function")
def pinecone_vectorstore(settings, openai_embeddings):
    yield PineconeVectorStore(
        pinecone_api_key=settings.pinecone_api_key,
        embedding=openai_embeddings,
        index_name=settings.pinecone_index_name,
    )


@pytest.fixture(scope="function")
def pinecone_docstore(settings, openai_embeddings):
    yield create_kv_docstore(LocalFileStore(settings.pinecone_persist_directory))


@pytest.fixture(scope="function")
def openai_llm_model(settings):
    yield ChatOpenAI(
        model=settings.openai_llm_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )


@pytest_asyncio.fixture
async def pinecone_test_client(app, pinecone_vectorstore):
    """해당 fixture는 pinecone vectorstore를 사용하여 테스트하기 위한 클라이언트입니다."""
    app.container.vectorstore.override(pinecone_vectorstore)
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
            yield test_client
