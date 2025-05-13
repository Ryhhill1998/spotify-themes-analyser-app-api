from typing import Annotated

from fastapi import APIRouter
from pydantic import Field

from api.data_structures.enums import TopItemTimeRange
from api.data_structures.models import SpotifyProfile, SpotifyArtist, SpotifyTrack, TopEmotion

router = APIRouter(prefix="/me")


@router.get("/profile", response_model=SpotifyProfile)
async def get_profile() -> SpotifyProfile:
    pass


@router.get("/top/artists", response_model=list[SpotifyArtist])
async def get_top_artists(
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[SpotifyArtist]:
    pass


@router.get("/top/tracks")
async def get_top_tracks(
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[SpotifyTrack]:
    pass


@router.get("/top/emotions")
async def get_top_emotions(
        time_range: TopItemTimeRange
) -> list[TopEmotion]:
    pass
