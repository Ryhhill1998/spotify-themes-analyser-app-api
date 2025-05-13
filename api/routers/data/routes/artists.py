from fastapi import APIRouter

from api.data_structures.models import SpotifyArtist

router = APIRouter(prefix="/artists")


@router.get("/{artist_id}", response_model=SpotifyArtist)
async def get_artist_by_id(artist_id: str) -> SpotifyArtist:
    pass
