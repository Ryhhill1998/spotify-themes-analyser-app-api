from fastapi import APIRouter

from api.data_structures.enums import TopItemTimeRange, TopItemType
from api.dependencies import UserIdDependency, TopItemsProcessorDependency, AccessTokenDependency
from api.services.top_items_processor import TopItemsProcessor

router = APIRouter(prefix="/compare")


def add_common_item_tag(top_items, other_top_items):
    common_ids = set(item.id for item in top_items).intersection(set(item.id for item in other_top_items))

    for item in top_items:
        if item.id in common_ids:
            item.common = True

    for item in other_top_items:
        if item.id in common_ids:
            item.common = True


async def get_top_items_for_time_range(
        user_id: str,
        access_token: str,
        item_type: TopItemType,
        time_range: TopItemTimeRange,
        top_items_processor: TopItemsProcessor,
):
    if item_type == TopItemType.ARTIST:
        method = top_items_processor.get_top_artists
    elif item_type == TopItemType.TRACK:
        method = top_items_processor.get_top_tracks
    elif item_type == TopItemType.GENRE:
        method = top_items_processor.get_top_genres
    elif item_type == TopItemType.EMOTION:
        method = top_items_processor.get_top_emotions
    else:
        raise ValueError("Invalid TopItemType")

    return await method(
        user_id=user_id,
        access_token=access_token,
        time_range=time_range,
        limit=50,
    )


async def get_top_items_with_comparisons_for_time_range(
        user_id: str,
        other_user_id: str,
        access_token: str,
        item_type: TopItemType,
        time_range: TopItemTimeRange,
        top_items_processor: TopItemsProcessor,
):
    user_top_items = await get_top_items_for_time_range(
        user_id=user_id,
        access_token=access_token,
        item_type=item_type,
        time_range=time_range,
        top_items_processor=top_items_processor,
    )

    other_user_top_items = await get_top_items_for_time_range(
        user_id=other_user_id,
        access_token=access_token,
        item_type=item_type,
        time_range=time_range,
        top_items_processor=top_items_processor,
    )

    add_common_item_tag(top_items=user_top_items, other_top_items=other_user_top_items)

    return user_top_items, other_user_top_items


async def get_top_items_for_all_time_ranges(
        user_id: str,
        other_user_id: str,
        access_token: str,
        item_type: TopItemType,
        top_items_processor: TopItemsProcessor,
):
    user_top_items_short_term, other_user_top_items_short_term = await get_top_items_with_comparisons_for_time_range(
        user_id=user_id,
        other_user_id=other_user_id,
        access_token=access_token,
        item_type=item_type,
        time_range=TopItemTimeRange.SHORT,
        top_items_processor=top_items_processor,
    )

    user_top_items_medium_term, other_user_top_items_medium_term = await get_top_items_with_comparisons_for_time_range(
        user_id=user_id,
        other_user_id=other_user_id,
        access_token=access_token,
        item_type=item_type,
        time_range=TopItemTimeRange.MEDIUM,
        top_items_processor=top_items_processor,
    )

    user_top_items_long_term, other_user_top_items_long_term = await get_top_items_with_comparisons_for_time_range(
        user_id=user_id,
        other_user_id=other_user_id,
        access_token=access_token,
        item_type=item_type,
        time_range=TopItemTimeRange.LONG,
        top_items_processor=top_items_processor,
    )

    user_top_items = {
        TopItemTimeRange.SHORT: user_top_items_short_term,
        TopItemTimeRange.MEDIUM: user_top_items_medium_term,
        TopItemTimeRange.LONG: user_top_items_long_term,
    }

    other_user_top_items = {
        TopItemTimeRange.SHORT: other_user_top_items_short_term,
        TopItemTimeRange.MEDIUM: other_user_top_items_medium_term,
        TopItemTimeRange.LONG: other_user_top_items_long_term,
    }

    return user_top_items, other_user_top_items


@router.get("/request/{other_user_id}")
async def get_music_taste_comparison(
        other_user_id: str,
        user_id: UserIdDependency,
        access_token: AccessTokenDependency,
        top_items_processor: TopItemsProcessorDependency,
):
    # artists
    user_top_artists, other_user_top_artists = await get_top_items_for_all_time_ranges(
        user_id=user_id,
        other_user_id=other_user_id,
        access_token=access_token,
        item_type=TopItemType.ARTIST,
        top_items_processor=top_items_processor,
    )

    # tracks
    user_top_tracks, other_user_top_tracks = await get_top_items_for_all_time_ranges(
        user_id=user_id,
        other_user_id=other_user_id,
        access_token=access_token,
        item_type=TopItemType.TRACK,
        top_items_processor=top_items_processor,
    )

    return {
        "artists": {"user": user_top_artists, "other_user": other_user_top_artists},
        "tracks": {"user": user_top_tracks, "other_user": other_user_top_tracks},
    }
