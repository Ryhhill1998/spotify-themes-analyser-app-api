import json
from datetime import timedelta

import redis.asyncio as redis

from api.data_structures.enums import TopItemType
from api.data_structures.models import create_top_items_from_data


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

    @staticmethod
    def _get_user_top_items_key(user_id: str) -> str:
        return f"top_items-{user_id}"

    async def _retrieve_all_top_items_data(self, user_id: str) -> dict | None:
        all_top_items_data = None

        top_items_key = self._get_user_top_items_key(user_id)
        all_top_items_raw = await self.client.get(top_items_key)

        if all_top_items_raw:
            all_top_items_data = json.loads(all_top_items_raw)

        return all_top_items_data

    async def store_top_items(self, user_id: str, top_items_to_store: list, item_type: TopItemType):
        all_top_items_data = await self._retrieve_all_top_items_data(user_id)
        all_top_items_data[f"top_{item_type.value}s"] = top_items_to_store
        all_top_items_raw = json.dumps(all_top_items_data)
        top_items_key = self._get_user_top_items_key(user_id)
        await self.client.set(name=top_items_key, value=all_top_items_raw)

    async def retrieve_top_items(self, user_id: str, item_type: TopItemType) -> list | None:
        top_items = None

        all_top_items = await self._retrieve_all_top_items_data(user_id)

        if all_top_items:
            top_items_data = all_top_items.get(f"top_{item_type.value}s")
            top_items = create_top_items_from_data(data=top_items_data, item_type=item_type)

        return top_items
