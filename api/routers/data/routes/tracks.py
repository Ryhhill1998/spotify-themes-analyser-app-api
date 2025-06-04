from fastapi import APIRouter

from api.data_structures.enums import TopItemType
from api.data_structures.models import Emotion, EmotionalTagsResponse, SpotifyTrack
from api.dependencies import DBServiceDependency, SpotifyDataServiceDependency, GetUserIdDependency
from api.routers.data.routes.helpers import retrieve_user_from_db_and_refresh_tokens

router = APIRouter(prefix="/tracks")


@router.get("/{track_id}", response_model=SpotifyTrack)
async def get_track_by_id(
        user_id: GetUserIdDependency,
        track_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> SpotifyTrack:
    updated_tokens = await retrieve_user_from_db_and_refresh_tokens(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service
    )
    track = await spotify_data_service.get_item_by_id(
        access_token=updated_tokens.access_token,
        item_id=track_id,
        item_type=TopItemType.TRACK
    )
    return track


@router.get("/{track_id}/lyrics/emotional-tags/{emotion}", response_model=EmotionalTagsResponse)
async def get_lyrics_tagged_with_emotion(
        user_id: GetUserIdDependency,
        track_id: str,
        emotion: Emotion,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> EmotionalTagsResponse:
    updated_tokens = await retrieve_user_from_db_and_refresh_tokens(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service
    )
    emotional_tags = await spotify_data_service.get_lyrics_tagged_with_emotion(
        access_token=updated_tokens.access_token,
        track_id=track_id,
        emotion=emotion
    )
    return emotional_tags
