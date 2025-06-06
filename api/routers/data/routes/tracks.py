from fastapi import APIRouter

from api.data_structures.enums import TopItemType
from api.data_structures.models import Emotion, EmotionalTagsResponse, SpotifyTrack
from api.dependencies import SpotifyDataServiceDependency, AccessTokenDependency

router = APIRouter(prefix="/tracks")


@router.get("/{track_id}", response_model=SpotifyTrack)
async def get_track_by_id(
        access_token: AccessTokenDependency,
        track_id: str,
        spotify_data_service: SpotifyDataServiceDependency
) -> SpotifyTrack:
    track = await spotify_data_service.get_item_by_id(
        access_token=access_token,
        item_id=track_id,
        item_type=TopItemType.TRACK
    )
    return track


@router.get("/{track_id}/lyrics/emotional-tags/{emotion}", response_model=EmotionalTagsResponse)
async def get_lyrics_tagged_with_emotion(
        access_token: AccessTokenDependency,
        track_id: str,
        emotion: Emotion,
        spotify_data_service: SpotifyDataServiceDependency
) -> EmotionalTagsResponse:
    emotional_tags = await spotify_data_service.get_lyrics_tagged_with_emotion(
        access_token=access_token,
        track_id=track_id,
        emotion=emotion
    )
    return emotional_tags
