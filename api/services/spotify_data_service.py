from api.data_structures.models import SpotifyArtist, SpotifyTokenData, SpotifyTrack
from api.services.endpoint_requester import EndpointRequester


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

    async def get_several_artists_by_ids(self, access_token: str, artist_ids: list[str]) -> list[SpotifyArtist]:
        url = f"{self.base_url}/data/artists"
        req_body = {"access_token": {"access_token": access_token}, "requested_artists": {"ids": artist_ids}}
        data = await self.endpoint_requester.post(url=url, json_data=req_body)
        spotify_artists = [SpotifyArtist(**entry) for entry in data]
        return spotify_artists
    
    async def get_several_tracks_by_ids(self, access_token: str, track_ids: list[str]) -> list[SpotifyTrack]:
        url = f"{self.base_url}/data/tracks"
        req_body = {"access_token": {"access_token": access_token}, "requested_tracks": {"ids": track_ids}}
        data = await self.endpoint_requester.post(url=url, json_data=req_body)
        spotify_tracks = [SpotifyTrack(**entry) for entry in data]
        return spotify_tracks
