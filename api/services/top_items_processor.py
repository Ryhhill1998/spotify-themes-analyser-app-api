from dataclasses import dataclass
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

import pandas as pd

from api.data_structures.enums import TopItemType, TopItemTimeRange
from api.data_structures.models import PositionChange, create_top_items_from_data
from api.services.db_service import DBService
from api.services.spotify_data_service import SpotifyDataService


@dataclass
class CollectionDates:
    latest: str
    previous: str


def get_collection_dates(update_hour: int, update_minute: int) -> CollectionDates:
    uk_tz = ZoneInfo("Europe/London")
    latest_date = datetime.now(uk_tz)

    update_time_uk = datetime.combine(latest_date.date(), time(hour=update_hour, minute=update_minute),
                                      tzinfo=uk_tz)

    if latest_date < update_time_uk:
        latest_date -= timedelta(days=1)

    prev_date = latest_date - timedelta(days=1)

    collection_dates = CollectionDates(
        latest=latest_date.strftime(format="%Y-%m-%d"),
        previous=prev_date.strftime(format="%Y-%m-%d")
    )

    return collection_dates


class TopItemsProcessor:
    def __init__(self, db_service: DBService, spotify_data_service: SpotifyDataService):
        self.db_service = db_service
        self.spotify_data_service = spotify_data_service
    
    @staticmethod
    def _format_position_change(position_change_value: float) -> PositionChange | None:
        if position_change_value < 0:
            position_change = PositionChange.DOWN
        elif position_change_value > 0:
            position_change = PositionChange.UP
        elif position_change_value == 0:
            position_change = None
        else:
            position_change = PositionChange.NEW

        return position_change

    def _add_position_changes_to_db_data(
            self,
            top_items_latest,
            top_items_previous,
            item_type: TopItemType,
            comparison_field: str = "position",
            id_key: str = "id"
    ) -> list[dict]:
        df_latest = pd.DataFrame([artist.model_dump() for artist in top_items_latest])
        df_previous = pd.DataFrame([artist.model_dump() for artist in top_items_previous])
        merged_df = df_latest.merge(
            right=df_previous,
            how="left",
            on=f"{item_type.value}_{id_key}",
            suffixes=("", "_prev")
        )
        merged_df["position_change"] = merged_df[f"{comparison_field}_prev"] - merged_df[comparison_field]
        merged_df["position_change"] = merged_df["position_change"].apply(self._format_position_change)
        top_items_with_position_changes = (
            merged_df
            .sort_values(by=comparison_field, ascending=False)
            .to_dict(orient="records")
        )
        return top_items_with_position_changes

    async def _default_get_top_items(self, access_token: str, item_type: TopItemType):
        spotify_items = await self.spotify_data_service.get_top_items(access_token=access_token, item_type=item_type)
        top_items = create_top_items_from_data(
            data=[item.model_dump() for item in spotify_items], 
            item_type=item_type
        )
        return top_items

    async def _enrich_db_data_with_spotify_data(
            self,
            db_data: list[dict],
            item_type: TopItemType,
            access_token: str
    ) -> list[dict]:
        item_ids = [item[f"{item_type.value}_id"] for item in db_data]
        spotify_items = await self.spotify_data_service.get_several_items_by_ids(
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

    async def _get_top_items(
            self,
            user_id: str,
            access_token: str,
            time_range: TopItemTimeRange,
            limit: int,
            item_type: TopItemType,
            order_by_field: str = "position",
            order_direction: str = "ASC",
            comparison_field: str = "position",
            id_key: str = "id",
            enrich_data: bool = True
    ):
        collection_dates = get_collection_dates(update_hour=8, update_minute=30)

        db_top_items_latest = self.db_service.get_top_items(
            user_id=user_id,
            time_range=time_range,
            collected_date=collection_dates.latest,
            limit=limit,
            item_type=item_type,
            order_field=order_by_field,
            order_direction=order_direction
        )

        if not db_top_items_latest:
            top_items = await self._default_get_top_items(
                access_token=access_token,
                item_type=item_type
            )
            return top_items

        db_top_items_previous = self.db_service.get_top_items(
            user_id=user_id,
            time_range=time_range,
            collected_date=collection_dates.previous,
            limit=limit,
            item_type=item_type,
            order_field=order_by_field,
            order_direction=order_direction
        )

        db_items_data = [item.model_dump() for item in db_top_items_latest]

        if db_top_items_previous:
            db_items_data = self._add_position_changes_to_db_data(
                top_items_latest=db_top_items_latest,
                top_items_previous=db_top_items_previous,
                item_type=item_type,
                comparison_field=comparison_field,
                id_key=id_key
            )

        if enrich_data:
            db_items_data = await self._enrich_db_data_with_spotify_data(
                db_data=db_items_data,
                item_type=item_type,
                access_token=access_token
            )

        top_items = create_top_items_from_data(data=db_items_data, item_type=item_type)

        return top_items
    
    async def get_top_artists(self, user_id: str, access_token: str, time_range: TopItemTimeRange, limit: int):
        top_artists = await self._get_top_items(
            user_id=user_id,
            access_token=access_token,
            time_range=time_range,
            limit=limit,
            item_type=TopItemType.ARTIST
        )
        return top_artists
    
    async def get_top_tracks(self, user_id: str, access_token: str, time_range: TopItemTimeRange, limit: int):
        top_tracks = await self._get_top_items(
            user_id=user_id,
            access_token=access_token,
            time_range=time_range,
            limit=limit,
            item_type=TopItemType.TRACK
        )
        return top_tracks
    
    async def get_top_genres(self, user_id: str, access_token: str, time_range: TopItemTimeRange, limit: int):
        top_genres = await self._get_top_items(
            user_id=user_id,
            access_token=access_token,
            time_range=time_range,
            limit=limit,
            item_type=TopItemType.GENRE,
            order_by_field="count",
            order_direction="DESC",
            comparison_field="percentage",
            id_key="name",
            enrich_data=False
        )
        return top_genres
    
    async def get_top_emotions(self, user_id: str, access_token: str, time_range: TopItemTimeRange, limit: int):
        top_emotions = await self._get_top_items(
            user_id=user_id,
            access_token=access_token,
            time_range=time_range,
            limit=limit,
            item_type=TopItemType.EMOTION,
            order_by_field="percentage",
            order_direction="DESC",
            comparison_field="percentage",
            id_key="name",
            enrich_data=False
        )
        return top_emotions
    