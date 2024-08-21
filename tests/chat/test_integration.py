import asyncio

import pytest


async def request_session_id(client):
    response = await client.post("/api/chat/session")

    return response.json().get("session_id")


async def request_stream_answer(client, headers, question):
    payload = {"question": question}

    answer = ""
    async with client.stream("POST", "/api/chat", headers=headers, json=payload) as r:
        async for chunk in r.aiter_bytes():
            answer += chunk.decode("utf-8")

    return answer


async def request_chat_histories(client, headers):
    response = await client.get("/api/chat/histories", headers=headers)
    assert response.status_code == 200

    return response.json()["histories"]


@pytest.mark.asyncio
async def test_integration(test_client, app):
    # session_id 발급
    session_id = await request_session_id(test_client)
    assert session_id
    headers = {"x-chat-session-id": session_id}

    # 질문하기
    question = "토큰이 중복 발급되었을 경우 어떻게 되나요?"
    question = "비정기적으로는?"
    question = "마이데이터 가이드라인의 목적에 대해서 알려줘"
    question = "x-api-tran-id에 대해 알려주세요."
    question = "개인신용정보 전송 내역 관리・보관에 관한 관련 법령을 알려줘"
    question = "토큰이 중복 발급되었을 경우 어떻게 해야 하나요?"
    question = "고객요청에 의한 정기적 전송 예시를 알려주세요."
    question = "정보 전송 요구 연장은 언제 가능한가요?"
    question = "API 스펙 중 aNS는 어떤 것을 뜻하나요?"

    answer = await request_stream_answer(test_client, headers, question)
    assert answer
    print(answer, end="\n")

    # 히스토리 보기
    chat_histories = await request_chat_histories(test_client, headers)
    assert chat_histories
    print(chat_histories)


@pytest.mark.asyncio
async def test_integration_with_history(test_client, app):
    # session_id 발급
    session_id = await request_session_id(test_client)
    assert session_id
    headers = {"x-chat-session-id": session_id}

    # 질문 1
    question = "고객요청에 의한 정기적 전송 예시를 알려주세요."
    answer = await request_stream_answer(test_client, headers, question)
    assert answer
    print(answer, end="\n")

    # 이어서 질문 2 (컨텍스트를 이해하는가?)
    question = "비정기적으로는?"
    answer = await request_stream_answer(test_client, headers, question)
    assert answer
    print(answer, end="\n")

    # 히스토리 보기
    chat_histories = await request_chat_histories(test_client, headers)
    assert chat_histories

    for history in chat_histories:
        if history["role"] == "human":
            print(f"Q: {history['content']}")


@pytest.mark.skip(reason="pinecine 테스트를 위한 코드")
@pytest.mark.asyncio
async def test_integration_pinecone(pinecone_test_client, app, pinecone_vectorstore):
    # session_id 발급
    session_id = await request_session_id(pinecone_test_client)
    assert session_id
    headers = {"x-chat-session-id": session_id}

    # 질문하기
    question = "API 스펙 중 aNS는 어떤 것을 뜻하나요?"

    answer = await request_stream_answer(pinecone_test_client, headers, question)
    assert answer
    print(answer, end="\n", flush=True)

    # 히스토리 보기
    chat_histories = await request_chat_histories(pinecone_test_client, headers)
    assert chat_histories
    print(chat_histories)

    await asyncio.sleep(2)
