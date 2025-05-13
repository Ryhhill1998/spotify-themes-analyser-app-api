from fastapi import APIRouter

from api.data_structures.models import Emotion, EmotionalTagsResponse, SpotifyTrack

router = APIRouter(prefix="/tracks")


@router.get("/{track_id}", response_model=SpotifyTrack)
async def get_track_by_id(track_id: str) -> SpotifyTrack:
    pass


@router.get("/{track_id}/lyrics/emotional-tags/{emotion}", response_model=EmotionalTagsResponse)
async def get_lyrics_tagged_with_emotion(track_id: str, emotion: Emotion) -> EmotionalTagsResponse:
    pass
