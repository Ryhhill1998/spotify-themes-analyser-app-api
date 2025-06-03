from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import Field
import pandas as pd

from api.data_structures.enums import TopItemTimeRange, TopItemType
from api.data_structures.models import (SpotifyProfile, TopEmotion, TopArtist, TopTrack, TopGenre, PositionChange,
                                        SpotifyTokens)
from api.dependencies import DBServiceDependency, SpotifyDataServiceDependency
from api.routers.data.routes.helpers import retrieve_user_from_db_and_refresh_tokens
from api.services.db_service import DBService
from api.services.spotify_data_service import SpotifyDataService

router = APIRouter(prefix="/me")


@router.get("/profile", response_model=SpotifyProfile)
async def get_profile(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> SpotifyProfile:
    updated_tokens = await retrieve_user_from_db_and_refresh_tokens(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service
    )
    profile = await spotify_data_service.get_profile(updated_tokens.access_token)
    return profile


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
        item_type: TopItemType,
        comparison_field: str = "position",
        id_key: str = "id"
) -> list[dict]:
    df_latest = pd.DataFrame([artist.model_dump() for artist in top_items_latest])
    df_previous = pd.DataFrame([artist.model_dump() for artist in top_items_previous])
    merged_df = df_latest.merge(right=df_previous, how="left", on=f"{item_type.value}_{id_key}", suffixes=("", "_prev"))
    merged_df["position_change"] = merged_df[f"{comparison_field}_prev"] - merged_df[comparison_field]
    merged_df["position_change"] = merged_df["position_change"].apply(format_position_change)
    top_items_with_position_changes = (
        merged_df
        .sort_values(by=comparison_field, ascending=False)
        .to_dict(orient="records")
    )
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


def create_top_items_from_data(data, item_type: TopItemType):
    if item_type == TopItemType.ARTIST:
        return [TopArtist(**entry) for entry in data]
    elif item_type == TopItemType.TRACK:
        return [TopTrack(**entry) for entry in data]
    elif item_type == TopItemType.GENRE:
        return [TopGenre(**entry) for entry in data]
    elif item_type == TopItemType.EMOTION:
        return [TopEmotion(**entry) for entry in data]
    else:
        raise ValueError("Invalid item type")


async def default_get_top_items(access_token: str, spotify_data_service: SpotifyDataService, item_type: TopItemType):
    spotify_items = await spotify_data_service.get_top_items(access_token=access_token, item_type=item_type)
    top_items = create_top_items_from_data(data=[item.model_dump() for item in spotify_items], item_type=item_type)
    return top_items


async def enrich_db_data_with_spotify_data(
        db_data: list[dict],
        item_type: TopItemType,
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
    item_id_to_position_map = {db_item[f"{item_type.value}_id"]: db_item for db_item in db_data}

    for item in spotify_items:
        item_data = item.model_dump()
        position_data = item_id_to_position_map[item.id]
        full_data = {**item_data, **position_data}
        enriched_data.append(full_data)

    enriched_data.sort(key=lambda x: x["position"], reverse=False)
        
    return enriched_data


async def get_top_items(
        user_id: str,
        db_service: DBService,
        spotify_data_service: SpotifyDataService,
        time_range: TopItemTimeRange,
        limit: int,
        item_type: TopItemType,
        comparison_field: str = "position",
        id_key: str = "id",
        enrich_data: bool = True
):
    updated_tokens = await retrieve_user_from_db_and_refresh_tokens(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service
    )
    collection_dates = get_collection_dates(update_hour=8, update_minute=30)

    db_top_items_latest = db_service.get_top_items(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.latest,
        limit=limit,
        item_type=item_type,
        order_field=comparison_field
    )

    if not db_top_items_latest:
        top_items = await default_get_top_items(
            access_token=updated_tokens.access_token,
            spotify_data_service=spotify_data_service,
            item_type=item_type
        )
        return top_items

    db_top_items_previous = db_service.get_top_items(
        user_id=user_id,
        time_range=time_range,
        collected_date=collection_dates.previous,
        limit=limit,
        item_type=item_type,
        order_field=comparison_field
    )

    db_items_data = [item.model_dump() for item in db_top_items_latest]

    if db_top_items_previous:
        db_items_data = add_position_changes_to_db_data(
            top_items_latest=db_top_items_latest,
            top_items_previous=db_top_items_previous,
            item_type=item_type,
            comparison_field=comparison_field,
            id_key=id_key
        )

    if enrich_data:
        db_items_data = await enrich_db_data_with_spotify_data(
            db_data=db_items_data,
            item_type=item_type,
            spotify_data_service=spotify_data_service,
            access_token=updated_tokens.access_token
        )

    top_items = create_top_items_from_data(data=db_items_data, item_type=item_type)

    return top_items


@router.get("/top/artists", response_model=list[TopArtist])
async def get_top_artists(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[TopArtist]:
    top_artists = await get_top_items(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service,
        time_range=time_range,
        limit=limit,
        item_type=TopItemType.ARTIST
    )
    return top_artists


@router.get("/top/tracks", response_model=list[TopTrack])
async def get_top_tracks(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[TopTrack]:
    top_tracks = await get_top_items(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service,
        time_range=time_range,
        limit=limit,
        item_type=TopItemType.TRACK
    )
    return top_tracks


@router.get("/top/genres", response_model=list[TopGenre])
async def get_top_genres(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[TopGenre]:
    top_genres = await get_top_items(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service,
        time_range=time_range,
        limit=limit,
        item_type=TopItemType.GENRE,
        comparison_field="count",
        id_key="name",
        enrich_data=False
    )
    return top_genres


@router.get("/top/emotions", response_model=list[TopEmotion])
async def get_top_emotions(
        user_id: str,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        time_range: TopItemTimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[TopEmotion]:
    top_emotions = await get_top_items(
        user_id=user_id,
        db_service=db_service,
        spotify_data_service=spotify_data_service,
        time_range=time_range,
        limit=limit,
        item_type=TopItemType.EMOTION,
        comparison_field="percentage",
        id_key="name",
        enrich_data=False
    )
    return top_emotions
