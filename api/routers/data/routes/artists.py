import json

from fastapi import APIRouter

from api.data_structures.enums import TopItemType
from api.data_structures.models import SpotifyArtist
from api.dependencies import SpotifyDataServiceDependency, DBServiceDependency, GetUserIdDependency, \
    MemoryStoreDependency

router = APIRouter(prefix="/artists")


@router.get("/{artist_id}", response_model=SpotifyArtist)
async def get_artist_by_id(
        user_id: GetUserIdDependency,
        artist_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        memory_store: MemoryStoreDependency
) -> SpotifyArtist:
    access_token = await memory_store.retrieve_access_token(user_id)

    if not access_token:
        user = db_service.get_user(user_id)
        updated_tokens = await spotify_data_service.refresh_tokens(user.refresh_token)
        access_token = updated_tokens.access_token
        await memory_store.store_access_token(user_id=user_id, access_token=access_token)

    artist = await spotify_data_service.get_item_by_id(
        access_token=access_token,
        item_id=artist_id,
        item_type=TopItemType.ARTIST
    )
    return artist
