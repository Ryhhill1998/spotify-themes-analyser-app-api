from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import Field
import pandas as pd

from api.data_structures.enums import TopItemTimeRange
from api.data_structures.models import SpotifyProfile, TopEmotion, TopArtist, TopTrack, TopGenre, PositionChange, \
    SpotifyTokenData
from api.dependencies import DBServiceDependency, SpotifyDataServiceDependency
from api.services.db_service import DBService
from api.services.spotify_data_service import SpotifyDataService

router = APIRouter(prefix="/me")


@dataclass
class CollectionDates:
    latest: str
    previous: str


def get_collection_dates(update_hour: int, update_minute: int) -> CollectionDates:
    uk_tz = ZoneInfo("Europe/London")
    latest_date = datetime.now(uk_tz)

    update_time_uk = datetime.combine(latest_date.date(), time(hour=update_hour, minute=update_minute), tzinfo=uk_tz)

    if latest_date < update_time_uk:
        latest_date -= timedelta(days=1)

    prev_date = latest_date - timedelta(days=1)

    collection_dates = CollectionDates(
        latest=latest_date.strftime(format="%Y-%m-%d"),
        previous=prev_date.strftime(format="%Y-%m-%d")
    )
    
    return collection_dates


@router.get("/profile", response_model=SpotifyProfile)
async def get_profile(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> SpotifyProfile:
    user = db_service.get_user(user_id)
    # get profile from spotify data service


async def retrieve_user_from_db_and_refresh_tokens(
        user_id: str,
        db_service: DBService,
        spotify_data_service: SpotifyDataService
) -> SpotifyTokenData:
    user = db_service.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_tokens = await spotify_data_service.refresh_tokens(user.refresh_token)
    return updated_tokens


def calculate_position_changes(
        top_items_latest,
        top_items_previous,
        item_type: str,
        comparison_field: str = "position",
        id_key: str = "id"
) -> list[dict]:
    df_latest = pd.DataFrame([artist.model_dump() for artist in top_items_latest])
    df_previous = pd.DataFrame([artist.model_dump() for artist in top_items_previous])
    merged_df = df_latest.merge(right=df_previous, how="outer", on=f"{item_type}_{id_key}", suffixes=("", "_prev"))
    merged_df["position_change"] = merged_df[f"{comparison_field}_prev"] - merged_df[comparison_field]
    top_items_with_position_changes = merged_df.sort_values(by=comparison_field, ascending=False).to_dict(orient="records")
    return top_items_with_position_changes


def format_position_change(position_change_value: float) -> PositionChange | None:
    if position_change_value < 0:
        position_change = PositionChange.DOWN
    elif position_change_value > 0:
        position_change = PositionChange.UP
    elif position_change_value == 0:
        position_change = None
    else:
        position_change = PositionChange.NEW

    return position_change


@router.get("/top/artists", response_model=list[TopArtist])
async def get_top_artists(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[TopArtist]:
    updated_tokens = await retrieve_user_from_db_and_refresh_tokens(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service
    )
    collection_dates = get_collection_dates(update_hour=8, update_minute=30)

    db_top_artists_latest = db_service.get_top_artists(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.latest,
        limit=limit
    )

    if not db_top_artists_latest:
        spotify_artists = await spotify_data_service.get_top_artists(access_token=updated_tokens.access_token)
        top_artists = [
            TopArtist(
                **artist.model_dump(),
                position=index + 1
            )
            for index, artist in enumerate(spotify_artists)
        ]
        return top_artists

    db_top_artists_previous = db_service.get_top_artists(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.previous,
        limit=limit
    )

    if not db_top_artists_previous:
        db_top_artists_ids = [db_artist.artist_id for db_artist in db_top_artists_latest]
        artist_id_to_position_map = {db_artist.artist_id: db_artist.position for db_artist in db_top_artists_latest}
        spotify_artists = await spotify_data_service.get_several_artists_by_ids(
            access_token=updated_tokens.access_token,
            artist_ids=db_top_artists_ids
        )
        top_artists = [
            TopArtist(
                **artist.model_dump(),
                position=artist_id_to_position_map[artist.id]
            )
            for artist in spotify_artists
        ]
        return top_artists

    # calculate position changes
    artists_with_position_changes = calculate_position_changes(
        top_items_latest=db_top_artists_latest,
        top_items_previous=db_top_artists_previous,
        item_type="artist"
    )
    artist_id_to_position_map = {db_artist["artist_id"]: db_artist for db_artist in artists_with_position_changes}

    artists_ids = [db_artist.artist_id for db_artist in db_top_artists_latest]
    spotify_artists = await spotify_data_service.get_several_artists_by_ids(
        access_token=updated_tokens.access_token,
        artist_ids=artists_ids
    )

    top_artists = []

    for artist in spotify_artists:
        artist_data = artist.model_dump()
        position_data = artist_id_to_position_map[artist.id]
        position = position_data["position"]
        position_change = format_position_change(position_data["position_change"])
        top_artist = TopArtist(**artist_data, position=position, position_change=position_change)
        top_artists.append(top_artist)

    return top_artists


@router.get("/top/tracks", response_model=list[TopTrack])
async def get_top_tracks(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[TopTrack]:
    updated_tokens = await retrieve_user_from_db_and_refresh_tokens(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service
    )
    collection_dates = get_collection_dates(update_hour=8, update_minute=30)

    db_top_tracks_latest = db_service.get_top_tracks(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.latest,
        limit=limit
    )

    if not db_top_tracks_latest:
        spotify_tracks = await spotify_data_service.get_top_tracks(access_token=updated_tokens.access_token)
        top_tracks = [
            TopTrack(
                **track.model_dump(),
                position=index + 1
            )
            for index, track in enumerate(spotify_tracks)
        ]
        return top_tracks

    db_top_tracks_previous = db_service.get_top_tracks(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.previous,
        limit=limit
    )

    if not db_top_tracks_previous:
        db_top_tracks_ids = [db_track.track_id for db_track in db_top_tracks_latest]
        track_id_to_position_map = {db_track.track_id: db_track.position for db_track in db_top_tracks_latest}
        spotify_tracks = await spotify_data_service.get_several_tracks_by_ids(
            access_token=updated_tokens.access_token,
            track_ids=db_top_tracks_ids
        )
        top_tracks = [
            TopTrack(
                **track.model_dump(),
                position=track_id_to_position_map[track.id]
            )
            for track in spotify_tracks
        ]
        return top_tracks

    # calculate position changes
    tracks_with_position_changes = calculate_position_changes(
        top_items_latest=db_top_tracks_latest,
        top_items_previous=db_top_tracks_previous,
        item_type="track"
    )
    track_id_to_position_map = {db_track["track_id"]: db_track for db_track in tracks_with_position_changes}

    tracks_ids = [db_track.track_id for db_track in db_top_tracks_latest]
    spotify_tracks = await spotify_data_service.get_several_tracks_by_ids(
        access_token=updated_tokens.access_token,
        track_ids=tracks_ids
    )

    top_tracks = []

    for track in spotify_tracks:
        track_data = track.model_dump()
        position_data = track_id_to_position_map[track.id]
        position = position_data["position"]
        position_change = format_position_change(position_data["position_change"])
        top_track = TopTrack(**track_data, position=position, position_change=position_change)
        top_tracks.append(top_track)

    return top_tracks


@router.get("/top/genres")
async def get_top_genres(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[TopGenre]:
    updated_tokens = await retrieve_user_from_db_and_refresh_tokens(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service
    )
    collection_dates = get_collection_dates(update_hour=8, update_minute=30)

    db_top_genres_latest = db_service.get_top_genres(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.latest,
        limit=limit
    )
    
    if not db_top_genres_latest:
        spotify_genres = spotify_data_service.get_top_genres(updated_tokens.access_token)
        top_genres = [TopGenre(**genre.model_dump(), position_change=None) for genre in spotify_genres]
        return top_genres

    db_top_genres_previous = db_service.get_top_genres(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.previous,
        limit=limit
    )
    
    if not db_top_genres_previous:
        top_genres = [TopGenre(**genre.model_dump(), position_change=None) for genre in db_top_genres_latest]
        return top_genres

    # calculate position changes
    genres_with_position_changes = calculate_position_changes(
        top_items_latest=db_top_genres_latest,
        top_items_previous=db_top_genres_previous,
        item_type="genre",
        comparison_field="count",
        id_key="name"
    )

    top_genres = [
        TopGenre(
            genre_name=genre["genre_name"],
            count=genre["count"],
            position_change=format_position_change(genre["position_change"])
        )
        for genre in genres_with_position_changes
    ]

    return top_genres



@router.get("/top/emotions")
async def get_top_emotions(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[TopEmotion]:
    updated_tokens = await retrieve_user_from_db_and_refresh_tokens(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service
    )
    collection_dates = get_collection_dates(update_hour=8, update_minute=30)

    db_top_emotions_latest = db_service.get_top_emotions(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.latest,
        limit=limit
    )

    if not db_top_emotions_latest:
        spotify_emotions = spotify_data_service.get_top_emotions(updated_tokens.access_token)
        top_emotions = [TopEmotion(**emotion.model_dump(), position_change=None) for emotion in spotify_emotions]
        return top_emotions

    db_top_emotions_previous = db_service.get_top_emotions(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.previous,
        limit=limit
    )

    if not db_top_emotions_previous:
        top_emotions = [TopEmotion(**emotion.model_dump(), position_change=None) for emotion in db_top_emotions_latest]
        return top_emotions

    # calculate position changes
    emotions_with_position_changes = calculate_position_changes(
        top_items_latest=db_top_emotions_latest,
        top_items_previous=db_top_emotions_previous,
        item_type="emotion",
        comparison_field="percentage",
        id_key="name"
    )

    top_emotions = [
        TopEmotion(
            emotion_name=emotion["emotion_name"],
            percentage=emotion["percentage"],
            track_id=emotion["track_id"],
            position_change=format_position_change(emotion["position_change"])
        )
        for emotion in emotions_with_position_changes
    ]

    return top_emotions
