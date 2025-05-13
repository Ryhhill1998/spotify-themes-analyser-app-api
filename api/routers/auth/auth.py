from fastapi import APIRouter

from api.routers.auth.routes import spotify

router = APIRouter(prefix="/auth")

router.include_router(spotify.router)
