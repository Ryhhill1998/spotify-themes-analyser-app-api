from fastapi import APIRouter
from api.dependencies import UserIdDependency, TopItemsProcessorDependency, AccessTokenDependency

router = APIRouter(prefix="/compare")


@router.get("/request/{other_user_id}")
async def get_music_taste_comparison(
        other_user_id: str,
        user_id: UserIdDependency,
        access_token: AccessTokenDependency,
        top_items_processor: TopItemsProcessorDependency,
):
    pass
