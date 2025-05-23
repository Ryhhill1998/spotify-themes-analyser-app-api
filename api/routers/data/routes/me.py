from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Annotated

from fastapi import APIRouter
from pydantic import Field

from api.data_structures.enums import TopItemTimeRange
from api.data_structures.models import SpotifyProfile, SpotifyTrack, TopEmotion, ResponseArtist, ResponseTrack
from api.dependencies import DBServiceDependency, SpotifyDataServiceDependency

router = APIRouter(prefix="/me")


def get_collection_date(update_hour: int, update_minute: int) -> str:
    uk_tz = ZoneInfo("Europe/London")
    now_uk = datetime.now(uk_tz)

    update_time_uk = datetime.combine(now_uk.date(), time(hour=update_hour, minute=update_minute), tzinfo=uk_tz)

    if now_uk < update_time_uk:
        now_uk = now_uk - timedelta(days=1)

    collected_date = now_uk.strftime(format="%Y-%m-%d")
    
    return collected_date


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
    collected_date = get_collection_date(update_hour=8, update_minute=30)

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


@router.get("/top/tracks", response_model=list[ResponseTrack])
async def get_top_tracks(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[ResponseTrack]:
    user = db_service.get_user(user_id)
    collected_date = get_collection_date(update_hour=8, update_minute=30)

    db_top_tracks = db_service.get_top_tracks(
        user_id=user_id,
        time_range=time_range,
        collected_date=collected_date,
        limit=limit
    )
    db_top_tracks_ids = [db_track.track_id for db_track in db_top_tracks]
    track_id_to_position_map = {db_track.track_id: db_track.position for db_track in db_top_tracks}
    updated_tokens = await spotify_data_service.refresh_tokens(user.refresh_token)
    spotify_tracks = await spotify_data_service.get_several_tracks_by_ids(
        access_token=updated_tokens.access_token,
        track_ids=db_top_tracks_ids
    )
    response_tracks = [
        ResponseTrack(
            **track.model_dump(),
            position=track_id_to_position_map[track.id]
        )
        for track in spotify_tracks
    ]
    return response_tracks


@router.get("/top/genres")
async def get_top_genres(
        user_id: str,
        db_service: DBServiceDependency,
        time_range: TopItemTimeRange
) -> list[TopEmotion]:
    pass


@router.get("/top/emotions")
async def get_top_emotions(
        user_id: str,
        db_service: DBServiceDependency,
        time_range: TopItemTimeRange
) -> list[TopEmotion]:
    pass
