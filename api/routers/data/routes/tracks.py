from fastapi import APIRouter

from api.data_structures.enums import TopItemType
from api.data_structures.models import Emotion, EmotionalTagsResponse, SpotifyTrack
from api.dependencies import DBServiceDependency, SpotifyDataServiceDependency, GetUserIdDependency

router = APIRouter(prefix="/tracks")


@router.get("/{track_id}", response_model=SpotifyTrack)
async def get_track_by_id(
        user_id: GetUserIdDependency,
        track_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> SpotifyTrack:
    user = db_service.get_user(user_id)
    updated_tokens = await spotify_data_service.refresh_tokens(user.refresh_token)
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
    user = db_service.get_user(user_id)
    updated_tokens = await spotify_data_service.refresh_tokens(user.refresh_token)
    emotional_tags = await spotify_data_service.get_lyrics_tagged_with_emotion(
        access_token=updated_tokens.access_token,
        track_id=track_id,
        emotion=emotion
    )
    return emotional_tags
