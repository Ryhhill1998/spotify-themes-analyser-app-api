from fastapi import APIRouter

from api.data_structures.enums import TopItemType
from api.data_structures.models import SpotifyArtist
from api.dependencies import SpotifyDataServiceDependency, DBServiceDependency
from api.routers.data.routes.helpers import retrieve_user_from_db_and_refresh_tokens

router = APIRouter(prefix="/artists")


@router.get("/{artist_id}", response_model=SpotifyArtist)
async def get_artist_by_id(
        user_id: str,
        artist_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> SpotifyArtist:
    updated_tokens = await retrieve_user_from_db_and_refresh_tokens(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service
    )
    artist = await spotify_data_service.get_item_by_id(
        access_token=updated_tokens.access_token,
        item_id=artist_id,
        item_type=TopItemType.ARTIST
    )
    return artist
