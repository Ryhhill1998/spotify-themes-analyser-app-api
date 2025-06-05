from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import Field

from api.data_structures.enums import TopItemTimeRange
from api.data_structures.models import SpotifyProfile, TopEmotion, TopArtist, TopTrack, TopGenre
from api.dependencies import DBServiceDependency, SpotifyDataServiceDependency, GetUserIdDependency, \
    TopItemsProcessorDependency

router = APIRouter(prefix="/me")


@router.get("/profile", response_model=SpotifyProfile)
async def get_profile(
        user_id: GetUserIdDependency,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> SpotifyProfile:
    user = db_service.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_tokens = await spotify_data_service.refresh_tokens(user.refresh_token)
    profile = await spotify_data_service.get_profile(updated_tokens.access_token)
    return profile


@router.get("/top/artists", response_model=list[TopArtist])
async def get_top_artists(
        user_id: GetUserIdDependency,
        top_items_processor: TopItemsProcessorDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[TopArtist]:
    top_artists = await top_items_processor.get_top_artists(user_id=user_id, time_range=time_range, limit=limit)
    return top_artists


@router.get("/top/tracks", response_model=list[TopTrack])
async def get_top_tracks(
        user_id: GetUserIdDependency,
        top_items_processor: TopItemsProcessorDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[TopTrack]:
    top_tracks = await top_items_processor.get_top_tracks(user_id=user_id, time_range=time_range, limit=limit)
    return top_tracks


@router.get("/top/genres", response_model=list[TopGenre])
async def get_top_genres(
        user_id: GetUserIdDependency,
        top_items_processor: TopItemsProcessorDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=1)] = 5
) -> list[TopGenre]:
    top_genres = await top_items_processor.get_top_genres(user_id=user_id, time_range=time_range, limit=limit)
    return top_genres


@router.get("/top/emotions", response_model=list[TopEmotion])
async def get_top_emotions(
        user_id: GetUserIdDependency,
        top_items_processor: TopItemsProcessorDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=1, le=15)] = 5
) -> list[TopEmotion]:
    top_emotions = await top_items_processor.get_top_emotions(user_id=user_id, time_range=time_range, limit=limit)
    return top_emotions
