from typing import Annotated

from pydantic import BaseModel, Field

from app.application.chat.chat_dto import GetChatHistoryDto


class CreateSessionIdResponse(BaseModel):
    session_id: Annotated[str, Field(..., description="Session ID for chat")]


class GenerateChatStreamRequest(BaseModel):
    question: Annotated[
        str, Field(..., description="Message to chat with AI agent", example="API 스펙 중 aNS는 어떤 것을 뜻하나요?")
    ]


class GetChatHistoriesResponse(BaseModel):
    histories: Annotated[list[GetChatHistoryDto], Field([], description="QnA history")]
