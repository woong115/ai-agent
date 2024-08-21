from dependency_injector import containers
from dependency_injector.providers import Resource, Singleton
from langchain.storage import LocalFileStore
from langchain.storage._lc_store import create_kv_docstore
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import UpstageEmbeddings

from app.application.chat.chat_service import ChatService
from app.application.sample_service import SampleService
from app.infrastructure.langchain.chat_engine_langchain_impl import (
    ChatEngineLangchainImpl,
)
from app.settings import settings


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["app.infrastructure.http"],
    )

    # 1. db clients or models, etc...
    llm = Singleton(
        ChatOpenAI,
        model=settings.openai_llm_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )

    ## openai embedding
    embeddings = Singleton(OpenAIEmbeddings, model=settings.openai_embedding_model)
    ## upsage embedding
    # embeddings = Singleton(UpstageEmbeddings, model=settings.upstage_embedding_model)

    ## Chroma vectorstore
    docstore = Resource(create_kv_docstore, LocalFileStore(settings.chroma_persist_directory))
    vectorstore = Singleton(
        Chroma,
        persist_directory=settings.chroma_persist_directory,
        embedding_function=embeddings,
        collection_name=settings.chroma_collection_name,
    )
    ## Pinecone vectorstore
    # docstore = Resource(create_kv_docstore, LocalFileStore(settings.pinecone_persist_directory))
    # vectorstore = Singleton(
    #     PineconeVectorStore,
    #     pinecone_api_key=settings.pinecone_api_key,
    #     embedding=embeddings,
    #     index=settings.pinecone_index_name,
    # )

    # utils
    chat_engine = Singleton(
        ChatEngineLangchainImpl,
        llm=llm,
        docstore=docstore,
        vectorstore=vectorstore,
        history_db_url=settings.redis_url,
        max_history_k=settings.max_history_k,
    )

    # services
    chat_service = Singleton(ChatService, chat_engine=chat_engine)
    sample_service = Singleton(SampleService)
