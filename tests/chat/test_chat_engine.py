import asyncio
from uuid import uuid4

import pytest

from app.application.port.chat_engine import ChatEngine
from app.infrastructure.langchain.chat_engine_langchain_impl import (
    ChatEngineLangchainImpl,
)


@pytest.mark.asyncio
async def test_chat_engine(app, settings, openai_llm_model, pinecone_docstore, pinecone_vectorstore):
    chat_engine: ChatEngine = ChatEngineLangchainImpl(
        llm=openai_llm_model,
        docstore=pinecone_docstore,
        vectorstore=pinecone_vectorstore,
        history_db_url=settings.redis_url,
        max_history_k=settings.max_history_k,
    )

    session_id = str(uuid4())
    question = "정보 전송 요구 연장은 언제 가능한가요?"

    chat_stream = await chat_engine.generate_chat_stream(session_id, question)

    answer = ""
    async for chunk in chat_stream:
        answer += chunk

    assert answer
    print(answer)

    await asyncio.sleep(2)  # aadd_message가 비동기로 동작하기 때문에 잠시 기다림
