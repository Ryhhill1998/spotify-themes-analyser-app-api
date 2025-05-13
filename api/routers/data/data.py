from fastapi import APIRouter

from api.routers.data.routes import artists, tracks, me

router = APIRouter(prefix="/data")

router.include_router(artists.router)
router.include_router(tracks.router)
router.include_router(me.router)
