from fastapi import APIRouter

from api.data_structures.enums import TopItemType
from api.data_structures.models import SpotifyArtist
from api.dependencies import SpotifyDataServiceDependency, AccessTokenDependency

router = APIRouter(prefix="/artists")


@router.get("/{artist_id}", response_model=SpotifyArtist)
async def get_artist_by_id(
        access_token: AccessTokenDependency,
        artist_id: str,
        spotify_data_service: SpotifyDataServiceDependency
) -> SpotifyArtist:
    artist = await spotify_data_service.get_item_by_id(
        access_token=access_token,
        item_id=artist_id,
        item_type=TopItemType.ARTIST
    )
    return artist
