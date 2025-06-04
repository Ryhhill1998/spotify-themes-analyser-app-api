from functools import lru_cache
from typing import Annotated

import mysql.connector
from fastapi import Depends, Request

from api.services.db_service import DBService
from api.services.endpoint_requester import EndpointRequester
from api.services.spotify_auth_service import SpotifyAuthService
from api.services.spotify_data_service import SpotifyDataService
from api.services.token_service import TokenService
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


def get_item_from_cookies(request: Request, item_key: str) -> str:
    cookies = request.cookies
    return cookies.get(item_key)


def get_user_id_from_cookies(request: Request) -> str:
    return get_item_from_cookies(request=request, item_key="user_id")


UserIdDependency = Annotated[str, Depends(get_user_id_from_cookies)]


def get_access_token_from_cookies(request: Request) -> str:
    return get_item_from_cookies(request=request, item_key="access_token")


AccessTokenDependency = Annotated[str, Depends(get_access_token_from_cookies)]


def get_refresh_token_from_cookies(request: Request) -> str:
    return get_item_from_cookies(request=request, item_key="refresh_token")


RefreshTokenDependency = Annotated[str, Depends(get_refresh_token_from_cookies)]


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
