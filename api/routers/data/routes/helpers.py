from fastapi import HTTPException

from api.data_structures.models import SpotifyTokens
from api.services.db_service import DBService
from api.services.spotify_data_service import SpotifyDataService


async def retrieve_user_from_db_and_refresh_tokens(
        user_id: str,
        db_service: DBService,
        spotify_data_service: SpotifyDataService
) -> SpotifyTokens:
    user = db_service.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_tokens = await spotify_data_service.refresh_tokens(user.refresh_token)
    return updated_tokens
