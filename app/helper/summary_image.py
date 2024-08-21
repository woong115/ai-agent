import base64
import os

import httpx
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI


def summary_image(image_path):
    image_data = base64.b64encode(open(image_path, "rb").read()).decode("utf-8")
    llm = ChatOpenAI(model="gpt-4o")
    message = HumanMessage(
        content=[
            {"type": "text", "text": "제공된 이미지를 요약해주세요."},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ],
    )
    response = llm.invoke([message])

    return response.content


if __name__ == "__main__":
    image_path = (
        "app/static/data/금융분야 마이데이터 기술 가이드라인/images/금융분야 마이데이터 기술 가이드라인.pdf-16-4.png"
    )
    result = summary_image(image_path)

    print(result)
