from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Annotated

from fastapi import APIRouter
from pydantic import Field

from api.data_structures.enums import TopItemTimeRange
from api.data_structures.models import SpotifyProfile, SpotifyArtist, SpotifyTrack, TopEmotion, ResponseArtist
from api.dependencies import DBServiceDependency, SpotifyDataServiceDependency

router = APIRouter(prefix="/me")


@router.get("/profile", response_model=SpotifyProfile)
async def get_profile(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> SpotifyProfile:
    user = db_service.get_user(user_id)
    # get profile from spotify data service


@router.get("/top/artists", response_model=list[ResponseArtist])
async def get_top_artists(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[ResponseArtist]:
    user = db_service.get_user(user_id)
    uk_tz = ZoneInfo("Europe/London")

    # Get current time in UK
    now_uk = datetime.now(uk_tz)

    # Create a datetime for 8:30 AM today in UK
    update_time_uk = datetime.combine(now_uk.date(), time(8, 30), tzinfo=uk_tz)

    if now_uk < update_time_uk:
        now_uk = now_uk - timedelta(days=1)

    collected_date = now_uk.strftime(format="%Y-%m-%d")

    db_top_artists = db_service.get_top_artists(
        user_id=user_id,
        time_range=time_range,
        collected_date=collected_date,
        limit=limit
    )
    db_top_artists_ids = [db_artist.artist_id for db_artist in db_top_artists]
    artist_id_to_position_map = {db_artist.artist_id: db_artist.position for db_artist in db_top_artists}
    updated_tokens = await spotify_data_service.refresh_tokens(user.refresh_token)
    spotify_artists = await spotify_data_service.get_several_artists_by_ids(
        access_token=updated_tokens.access_token,
        artist_ids=db_top_artists_ids
    )
    response_artists = [
        ResponseArtist(
            **artist.model_dump(),
            position=artist_id_to_position_map[artist.id]
        )
        for artist in spotify_artists
    ]
    return response_artists


@router.get("/top/tracks")
async def get_top_tracks(
        user_id: str,
        db_service: DBServiceDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[SpotifyTrack]:
    pass


@router.get("/top/emotions")
async def get_top_emotions(
        user_id: str,
        db_service: DBServiceDependency,
        time_range: TopItemTimeRange
) -> list[TopEmotion]:
    pass
