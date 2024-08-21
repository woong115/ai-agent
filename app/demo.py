import asyncio

import streamlit as st
from httpx import AsyncClient

from app.helper.regex import search_markdown_image_tag
from settings import settings

st.set_page_config(page_title="마이데이터 챗봇", page_icon="🏦")

st.title("마이데이터 챗봇 🏦")
st.caption("마이데이터에 관한 질문을 해주세요.")


async def get_session_id():
    async with AsyncClient(base_url=settings.self_host, timeout=30) as session:
        response = await session.post("/api/chat/session")
        return response.json()["session_id"]


async def get_answer_stream(session_id, user_question):
    headers = {"x-chat-session-id": session_id}
    payload = {"question": user_question}
    async with AsyncClient(base_url=settings.self_host, timeout=30) as session:
        async with session.stream("POST", "/api/chat", headers=headers, json=payload) as r:
            async for chunk in r.aiter_bytes():
                yield chunk.decode("utf-8")


def st_display_image_if_exists(chat, image, answer):
    image_tag, image_path = search_markdown_image_tag(answer)
    if image_tag:
        try:
            image.image(image_path)
        except:
            ...
        answer = answer.replace(image_tag, "")
    chat.markdown(answer)


async def main():
    if "session_id" not in st.session_state:
        st.session_state.session_id = await get_session_id()

    if "message_list" not in st.session_state:
        st.session_state.message_list = []

    for message in st.session_state.message_list:
        with st.chat_message(message["role"]):
            chat = st.empty()
            content = message["content"]
            chat.markdown(content)
            if message["role"] == "ai":
                image = st.empty()
                st_display_image_if_exists(chat, image, content)

        image = st.empty()  # 채팅 입력시 이전 이미지 보여지는 버그 해결을 위한 코드

    if user_question := st.chat_input(placeholder="궁금한 내용을 질문해주세요!"):
        with st.chat_message("user"):
            st.markdown(user_question)
        st.session_state.message_list.append({"role": "user", "content": user_question})

        with st.spinner("답변을 생성하는 중입니다"):
            with st.chat_message("ai"):
                text = ""
                chat = st.empty()
                image = st.empty()
                async for chunk in get_answer_stream(st.session_state.session_id, user_question):
                    text += chunk
                    chat.markdown(text)

                print(text, flush=True)
                st.session_state.message_list.append({"role": "ai", "content": text})
                st_display_image_if_exists(chat, image, text)


if __name__ == "__main__":
    question = "토큰이 중복 발급되었을 경우 어떻게 되나요?"
    question = "정보 전송 요구 연장은 언제 가능한가요?"
    question = "마이데이터 가이드라인의 목적에 대해서 알려줘"
    question = "x-api-tran-id에 대해 알려주세요."
    question = "API 스펙 중 aNS는 어떤 것을 뜻하나요?"
    question = "개인신용정보 전송 내역 관리・보관에 관한 관련 법령을 알려줘"
    question = "토큰이 중복 발급되었을 경우 어떻게 해야 하나요?"
    question = "고객요청에 의한 정기적 전송 예시를 알려주세요."
    question = "비정기적은?"

    asyncio.run(main())
