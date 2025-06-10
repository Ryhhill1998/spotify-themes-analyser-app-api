from api.data_structures.enums import TopItemType, TopItemTimeRange
from api.data_structures.models import SpotifyArtist, SpotifyTokens, SpotifyTrack, SpotifyGenre, SpotifyItem, \
    SpotifyProfile, Emotion, EmotionalTagsResponse
from api.services.endpoint_requester import EndpointRequester


class SpotifyDataService:
    def __init__(self, base_url: str, endpoint_requester: EndpointRequester):
        self.base_url = base_url
        self.endpoint_requester = endpoint_requester

    async def refresh_tokens(self, refresh_token: str) -> SpotifyTokens:
        url = f"{self.base_url}/auth/tokens/refresh"
        req_body = {"refresh_token": refresh_token}
        data = await self.endpoint_requester.post(url=url, json_data=req_body)
        tokens = SpotifyTokens(**data)
        return tokens

    async def get_profile(self, access_token: str) -> SpotifyProfile:
        url = f"{self.base_url}/data/me/profile"
        req_body = {"access_token": access_token}
        data = await self.endpoint_requester.post(url=url, json_data=req_body)
        profile = SpotifyProfile(**data)
        return profile

    @staticmethod
    def _create_spotify_items_from_data(data: list[dict], item_type: TopItemType):
        if item_type == TopItemType.ARTIST:
            return [SpotifyArtist(**entry) for entry in data]
        elif item_type == TopItemType.TRACK:
            return [SpotifyTrack(**entry) for entry in data]
        elif item_type == TopItemType.GENRE:
            return [SpotifyGenre(**entry) for entry in data]
        elif item_type == TopItemType.EMOTION:
            return [SpotifyGenre(**entry) for entry in data]
        else:
            raise ValueError("Invalid item type")

    async def get_top_items(self, access_token: str, item_type: TopItemType, time_range: TopItemTimeRange, limit: int):
        url = f"{self.base_url}/data/me/top/{item_type.value}s"
        params = {"time_range": time_range.value, "limit": limit}
        req_body = {"access_token": access_token}
        data = await self.endpoint_requester.post(url=url, json_data=req_body, params=params)
        top_items = self._create_spotify_items_from_data(data=data, item_type=item_type)
        return top_items

    async def get_several_items_by_ids(
            self,
            access_token: str,
            item_ids: list[str],
            item_type: TopItemType
    ) -> list[SpotifyItem]:
        url = f"{self.base_url}/data/{item_type.value}s"
        req_body = {"access_token": {"access_token": access_token}, f"requested_{item_type.value}s": {"ids": item_ids}}
        data = await self.endpoint_requester.post(url=url, json_data=req_body)

        if item_type == TopItemType.ARTIST:
            return [SpotifyArtist(**entry) for entry in data]
        elif item_type == TopItemType.TRACK:
            return [SpotifyTrack(**entry) for entry in data]
        else:
            raise ValueError("Invalid item type")

    async def get_item_by_id(
            self,
            access_token: str,
            item_id: str,
            item_type: TopItemType
    ):
        url = f"{self.base_url}/data/{item_type.value}s/{item_id}"
        req_body = {"access_token": access_token}
        data = await self.endpoint_requester.post(url=url, json_data=req_body)

        if item_type == TopItemType.ARTIST:
            return SpotifyArtist(**data)
        elif item_type == TopItemType.TRACK:
            return SpotifyTrack(**data)
        else:
            raise ValueError("Invalid item type")

    async def get_lyrics_tagged_with_emotion(
            self,
            access_token: str,
            track_id: str,
            emotion: Emotion
    ) -> EmotionalTagsResponse:
        url = f"{self.base_url}/data/tracks/{track_id}/lyrics/emotional-tags/{emotion.value}"
        req_body = {"access_token": access_token}
        data = await self.endpoint_requester.post(url=url, json_data=req_body)
        emotional_tags = EmotionalTagsResponse(**data)
        return emotional_tags
