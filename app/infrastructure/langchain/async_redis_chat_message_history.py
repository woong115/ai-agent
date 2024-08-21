import asyncio
import json
from typing import List, Optional

import redis.asyncio as redis
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict


class AsyncRedisChatMessageHistory(BaseChatMessageHistory):

    def __init__(
        self,
        session_id: str,
        url: str = "redis://localhost:6379/0",
        key_prefix: str = "message_store:",
        ttl: Optional[int] = None,
        k: int = 10,
    ):
        """
        :param k: 최근데이터로부터 k개만 가져온다.
        """
        self.redis_client = redis.from_url(url)
        self.session_id = session_id
        self.key_prefix = key_prefix
        self.ttl = ttl
        self.k = k
        self.loop = asyncio.get_event_loop()

    @property
    def key(self) -> str:
        return self.key_prefix + self.session_id

    @property
    def messages(self):
        return asyncio.run_coroutine_threadsafe(self.aget_messages(), self.loop).result()

    async def aget_messages(self) -> List[BaseMessage]:  # type: ignore
        _items = await self.redis_client.lrange(self.key, 0, self.k)  # 최근서부터 10개
        items = [json.loads(m.decode("utf-8")) for m in _items[::-1]]  # 뒤에서부터 생성
        messages = messages_from_dict(items)
        return messages

    def add_message(self, message: BaseMessage) -> None:
        asyncio.run_coroutine_threadsafe(self.aadd_message(message), self.loop)

    async def aadd_message(self, message: BaseMessage) -> None:
        await self.redis_client.lpush(self.key, json.dumps(message_to_dict(message)))
        if self.ttl:
            await self.redis_client.expire(self.key, self.ttl)

    def clear(self):
        asyncio.run_coroutine_threadsafe(self.aclear(), self.loop)

    async def aclear(self) -> None:
        await self.redis_client.delete(self.key)
