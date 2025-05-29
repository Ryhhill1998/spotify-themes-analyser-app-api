from enum import Enum

from api.data_structures.models import SpotifyArtist, SpotifyTokenData, SpotifyTrack, SpotifyGenre, SpotifyEmotion, \
    SpotifyItem
from api.services.endpoint_requester import EndpointRequester


class ItemType(str, Enum):
    ARTIST = "artist"
    TRACK = "track"
    GENRE = "genre"
    EMOTION = "emotion"


class SpotifyDataService:
    def __init__(self, base_url: str, endpoint_requester: EndpointRequester):
        self.base_url = base_url
        self.endpoint_requester = endpoint_requester
        
    async def refresh_tokens(self, refresh_token: str) -> SpotifyTokenData:
        url = f"{self.base_url}/auth/tokens/refresh"
        req_body = {"refresh_token": refresh_token}
        data = await self.endpoint_requester.post(url=url, json_data=req_body)
        token_data = SpotifyTokenData(**data)
        return token_data

    async def _get_top_items_data(self, access_token: str, item_type: ItemType) -> list[dict]:
        url = f"{self.base_url}/data/me/top/{item_type.value}s"
        req_body = {"access_token": access_token}
        data = await self.endpoint_requester.post(url=url, json_data=req_body)
        return data
    
    async def get_top_artists(self, access_token: str) -> list[SpotifyArtist]:
        data = await self._get_top_items_data(access_token, item_type=ItemType.ARTIST)
        return [SpotifyArtist(**entry) for entry in data]
    
    async def get_top_tracks(self, access_token: str) -> list[SpotifyTrack]:
        data = await self._get_top_items_data(access_token, item_type=ItemType.TRACK)
        return [SpotifyTrack(**entry) for entry in data]
    
    async def get_top_genres(self, access_token: str) -> list[SpotifyGenre]:
        data = await self._get_top_items_data(access_token, item_type=ItemType.GENRE)
        return [SpotifyGenre(**entry) for entry in data]
    
    async def get_top_emotions(self, access_token: str) -> list[SpotifyEmotion]:
        data = await self._get_top_items_data(access_token, item_type=ItemType.EMOTION)
        return [SpotifyEmotion(**entry) for entry in data]

    async def get_several_items_by_ids(
            self, 
            access_token: str, 
            item_ids: list[str], 
            item_type: ItemType
    ) -> list[SpotifyItem]:
        url = f"{self.base_url}/data/{item_type.value}s"
        req_body = {"access_token": {"access_token": access_token}, f"requested_{item_type.value}s": {"ids": item_ids}}
        data = await self.endpoint_requester.post(url=url, json_data=req_body)

        if item_type == ItemType.ARTIST:
            return [SpotifyArtist(**entry) for entry in data]
        elif item_type == ItemType.TRACK:
            return [SpotifyTrack(**entry) for entry in data]
        else:
            raise ValueError("Invalid item type")
