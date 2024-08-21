from pydantic import BaseModel


class GetChatHistoryDto(BaseModel):
    role: str
    content: str
