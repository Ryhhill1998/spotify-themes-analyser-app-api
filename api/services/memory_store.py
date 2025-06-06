from datetime import timedelta

import redis.asyncio as redis


class MemoryStore:
    def __init__(self, client: redis.Redis):
        self.client = client

    @staticmethod
    def _get_access_token_key(user_id: str) -> str:
        return f"access_token-{user_id}"

    async def store_access_token(self, user_id: str, access_token: str):
        key = self._get_access_token_key(user_id)
        await self.client.set(name=key, value=access_token)
        await self.client.expire(name=key, time=timedelta(minutes=58))

    async def retrieve_access_token(self, user_id: str) -> str | None:
        key = self._get_access_token_key(user_id)
        access_token = await self.client.get(key)
        return access_token
