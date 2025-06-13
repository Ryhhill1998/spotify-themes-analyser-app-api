from functools import lru_cache
from typing import Annotated

import mysql.connector
from fastapi import Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
import redis.asyncio as redis

from api.services.db_service import DBService
from api.services.endpoint_requester import EndpointRequester
from api.services.memory_store import MemoryStore
from api.services.spotify_auth_service import SpotifyAuthService
from api.services.spotify_data_service import SpotifyDataService
from api.services.token_service import TokenService, TokenServiceException
from api.services.top_items_processor import TopItemsProcessor
from api.settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


SettingsDependency = Annotated[Settings, Depends(get_settings)]


def get_token_service(settings: SettingsDependency) -> TokenService:
    return TokenService(
        secret_key=settings.encryption_secret_key,
        encryption_algorithm=settings.encryption_algorithm
    )


TokenServiceDependency = Annotated[TokenService, Depends(get_token_service)]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/spotify/token")


def get_user_id_from_token(token: Annotated[str, Depends(oauth2_scheme)], token_service: TokenServiceDependency) -> str:
    try:
        user_id = token_service.decode_token(token)["user_id"]
        return user_id
    except TokenServiceException:
        raise HTTPException(status_code=401, detail="Token expired.")


UserIdDependency = Annotated[str, Depends(get_user_id_from_token)]


def get_endpoint_requester(request: Request) -> EndpointRequester:
    return request.app.state.endpoint_requester


EndpointRequesterDependency = Annotated[EndpointRequester, Depends(get_endpoint_requester)]


def get_db_service(settings: SettingsDependency):
    conn = mysql.connector.connect(
        host=settings.db_host,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_pass
    )

    try:
        yield DBService(conn)
    finally:
        conn.close()


DBServiceDependency = Annotated[DBService, Depends(get_db_service)]


def get_spotify_auth_service(
        settings: SettingsDependency,
        endpoint_requester: EndpointRequesterDependency
) -> SpotifyAuthService:
    return SpotifyAuthService(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        base_url=settings.spotify_auth_base_url,
        redirect_uri=settings.spotify_auth_redirect_uri,
        auth_scope=settings.spotify_auth_user_scope,
        endpoint_requester=endpoint_requester
    )


SpotifyAuthServiceDependency = Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)]


def get_spotify_data_service(
        settings: SettingsDependency,
        endpoint_requester: EndpointRequesterDependency
) -> SpotifyDataService:
    return SpotifyDataService(base_url=settings.spotify_data_base_url, endpoint_requester=endpoint_requester)


SpotifyDataServiceDependency = Annotated[SpotifyDataService, Depends(get_spotify_data_service)]


def get_top_items_processor(
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> TopItemsProcessor:
    return TopItemsProcessor(db_service=db_service, spotify_data_service=spotify_data_service)


TopItemsProcessorDependency = Annotated[TopItemsProcessor, Depends(get_top_items_processor)]


async def get_memory_store(settings: SettingsDependency):
    redis_client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
        username=settings.redis_username,
        password=settings.redis_password,
    )

    try:
        yield MemoryStore(redis_client)
    finally:
        await redis_client.aclose()


MemoryStoreDependency = Annotated[MemoryStore, Depends(get_memory_store)]


async def get_access_token(
        user_id: UserIdDependency,
        memory_store: MemoryStoreDependency,
        db_service: DBServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency
):
    access_token = await memory_store.retrieve_access_token(user_id)

    if not access_token:
        user = db_service.get_user(user_id)
        updated_tokens = await spotify_data_service.refresh_tokens(user.refresh_token)
        access_token = updated_tokens.access_token
        await memory_store.store_access_token(user_id=user_id, access_token=access_token)

    return access_token


AccessTokenDependency = Annotated[str, Depends(get_access_token)]
