from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import Field
import pandas as pd

from api.data_structures.enums import TopItemTimeRange
from api.data_structures.models import (SpotifyProfile, TopEmotion, TopArtist, TopTrack, TopGenre, PositionChange,
                                        SpotifyTokenData, SpotifyItem)
from api.dependencies import DBServiceDependency, SpotifyDataServiceDependency
from api.services.db_service import DBService
from api.services.spotify_data_service import SpotifyDataService, ItemType

router = APIRouter(prefix="/me")


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


def add_position_changes_to_db_data(
        top_items_latest,
        top_items_previous,
        item_type: str,
        comparison_field: str = "position",
        id_key: str = "id"
) -> list[dict]:
    df_latest = pd.DataFrame([artist.model_dump() for artist in top_items_latest])
    df_previous = pd.DataFrame([artist.model_dump() for artist in top_items_previous])
    merged_df = df_latest.merge(right=df_previous, how="left", on=f"{item_type}_{id_key}", suffixes=("", "_prev"))
    merged_df["position_change"] = merged_df[f"{comparison_field}_prev"] - merged_df[comparison_field]
    merged_df["position_change"] = merged_df["position_change"].apply(format_position_change)
    top_items_with_position_changes = (
        merged_df
        .sort_values(by=comparison_field, ascending=False)
        .to_dict(orient="records")
    )
    print(f"{top_items_with_position_changes = }")
    return top_items_with_position_changes


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


async def default_get_top_artists(access_token: str, spotify_data_service: SpotifyDataService) -> list[TopArtist]:
    spotify_artists = await spotify_data_service.get_top_artists(access_token)
    top_artists = [TopArtist(**artist.model_dump()) for artist in spotify_artists]
    return top_artists


async def enrich_db_data_with_spotify_data(
        db_data: list[dict],
        item_type: ItemType,
        spotify_data_service: SpotifyDataService,
        access_token: str
) -> list[dict]:
    item_ids = [item[f"{item_type.value}_id"] for item in db_data]
    spotify_items = await spotify_data_service.get_several_items_by_ids(
        access_token=access_token,
        item_ids=item_ids,
        item_type=item_type
    )

    enriched_data = []
    item_id_to_position_map = {db_artist[f"{item_type.value}_id"]: db_artist for db_artist in db_data}

    for item in spotify_items:
        item_data = item.model_dump()
        position_data = item_id_to_position_map[item.id]
        full_data = {**item_data, **position_data}
        enriched_data.append(full_data)

    enriched_data.sort(key=lambda x: x["position"], reverse=False)
        
    return enriched_data


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
        top_artists = await default_get_top_artists(
            access_token=updated_tokens.access_token, 
            spotify_data_service=spotify_data_service
        )
        return top_artists

    db_top_artists_previous = db_service.get_top_artists(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.previous,
        limit=limit
    )

    db_artists_data = [artist.model_dump() for artist in db_top_artists_latest]

    if db_top_artists_previous:
        db_artists_data = add_position_changes_to_db_data(
            top_items_latest=db_top_artists_latest,
            top_items_previous=db_top_artists_previous,
            item_type="artist"
        )

    enriched_data = await enrich_db_data_with_spotify_data(
        db_data=db_artists_data,
        item_type=ItemType.ARTIST,
        spotify_data_service=spotify_data_service,
        access_token=updated_tokens.access_token
    )
    top_artists = [TopArtist(**entry) for entry in enriched_data]

    return top_artists


async def default_get_top_tracks(access_token: str, spotify_data_service: SpotifyDataService) -> list[TopTrack]:
    spotify_tracks = await spotify_data_service.get_top_tracks(access_token)
    top_tracks = [TopTrack(**track.model_dump()) for track in spotify_tracks]
    return top_tracks


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
        top_tracks = await default_get_top_tracks(
            access_token=updated_tokens.access_token,
            spotify_data_service=spotify_data_service
        )
        return top_tracks

    db_top_tracks_previous = db_service.get_top_tracks(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.previous,
        limit=limit
    )

    db_tracks_data = [track.model_dump() for track in db_top_tracks_latest]

    if db_top_tracks_previous:
        db_tracks_data = add_position_changes_to_db_data(
            top_items_latest=db_top_tracks_latest,
            top_items_previous=db_top_tracks_previous,
            item_type="track"
        )

    enriched_data = await enrich_db_data_with_spotify_data(
        db_data=db_tracks_data,
        item_type=ItemType.TRACK,
        spotify_data_service=spotify_data_service,
        access_token=updated_tokens.access_token
    )
    top_tracks = [TopTrack(**entry) for entry in enriched_data]

    return top_tracks


async def default_get_top_genres(access_token: str, spotify_data_service: SpotifyDataService) -> list[TopGenre]:
    spotify_genres = await spotify_data_service.get_top_genres(access_token)
    top_genres = [TopGenre(**genre.model_dump()) for genre in spotify_genres]
    return top_genres


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
        top_genres = await default_get_top_genres(
            access_token=updated_tokens.access_token,
            spotify_data_service=spotify_data_service
        )
        return top_genres

    db_top_genres_previous = db_service.get_top_genres(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.previous,
        limit=limit
    )

    db_genres_data = [genre.model_dump() for genre in db_top_genres_latest]

    if db_top_genres_previous:
        db_genres_data = add_position_changes_to_db_data(
            top_items_latest=db_top_genres_latest,
            top_items_previous=db_top_genres_previous,
            item_type="genre",
            comparison_field="count",
            id_key="name"
        )

    top_genres = [TopGenre(**genre) for genre in db_genres_data]

    return top_genres


async def default_get_top_emotions(access_token: str, spotify_data_service: SpotifyDataService) -> list[TopEmotion]:
    spotify_emotions = await spotify_data_service.get_top_emotions(access_token)
    top_emotions = [TopEmotion(**emotion.model_dump()) for emotion in spotify_emotions]
    return top_emotions


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
        top_emotions = await default_get_top_emotions(
            access_token=updated_tokens.access_token,
            spotify_data_service=spotify_data_service
        )
        return top_emotions

    db_top_emotions_previous = db_service.get_top_emotions(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.previous,
        limit=limit
    )

    db_emotions_data = [emotion.model_dump() for emotion in db_top_emotions_latest]

    if db_top_emotions_previous:
        db_emotions_data = add_position_changes_to_db_data(
            top_items_latest=db_top_emotions_latest,
            top_items_previous=db_top_emotions_previous,
            item_type="emotion",
            comparison_field="percentage",
            id_key="name"
        )

    top_emotions = [TopEmotion(**emotion) for emotion in db_emotions_data]

    return top_emotions
