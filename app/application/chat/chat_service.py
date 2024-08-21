import uuid

from app.application.chat.chat_dto import GetChatHistoryDto
from app.application.port.chat_engine import ChatEngine


class ChatService:
    def __init__(self, chat_engine: ChatEngine):
        self.chat_engine = chat_engine

    def create_session_id(self):
        return str(uuid.uuid4())

    async def get_chat_histories(self, session_id: str) -> list[GetChatHistoryDto]:
        histories = await self.chat_engine.find_chat_histories(session_id)

        return [GetChatHistoryDto(role=history.type, content=history.content) for history in histories]

    async def get_chat_stream(self, session_id: str, user_message: str):
        return await self.chat_engine.generate_chat_stream(session_id, user_message)
