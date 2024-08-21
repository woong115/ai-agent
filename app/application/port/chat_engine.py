from abc import ABC, abstractmethod


class ChatEngine(ABC):
    @abstractmethod
    async def generate_chat_stream(self, session_id: str, user_message: str): ...

    @abstractmethod
    async def find_chat_histories(self, session_id: str): ...
