import json
import secrets

import boto3
from fastapi import Response, APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from api.dependencies import SpotifyAuthServiceDependency, SpotifyDataServiceDependency, DBServiceDependency, \
    TokenServiceDependency, SettingsDependency
from api.services.spotify_auth_service import SpotifyAuthServiceException

router = APIRouter(prefix="/spotify")


@router.get("/login")
async def login(spotify_auth_service: SpotifyAuthServiceDependency):
    """
    Initiates the Spotify login process.

    This route generates a login URL for Spotify's OAuth authentication flow, sets a state cookie for CSRF protection
    and redirects the user to Spotify's authorization page.

    Parameters
    ----------
    spotify_auth_service : SpotifyAuthServiceDependency
        The Spotify authentication service used to generate the authorization URL.

    Returns
    -------
    Response
        A redirect response to Spotify's OAuth authorization page with a state cookie.
    """

    state = secrets.token_hex(16)
    url = spotify_auth_service.generate_auth_url(state)

    return {"login_url": url, "oauth_state": state}


class TokenRequest(BaseModel):
    code: str


@router.post("/token", response_model=dict[str, str | int])
async def get_token(
        token_request: TokenRequest,
        spotify_auth_service: SpotifyAuthServiceDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        db_service: DBServiceDependency,
        settings: SettingsDependency,
        token_service: TokenServiceDependency
) -> dict[str, str | int]:
    try:
        tokens = await spotify_auth_service.create_tokens(token_request.code)

        # use access_token to get user_id from Spotify
        spotify_data_service.access_token = tokens.access_token
        profile_data = await spotify_data_service.get_profile(tokens.access_token)
        user_id = profile_data.id

        # create new user in db
        new_user_created = db_service.create_user(user_id=user_id, refresh_token=tokens.refresh_token)

        if new_user_created:
            # add user data to SQS for processing
            sqs = boto3.client(
                "sqs",
                aws_access_key_id=settings.aws_access_key,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            message = json.dumps({"user_id": user_id, "refresh_token": tokens.refresh_token})
            logger.info(f"Sending user data to SQS queue: {message}")
            res = sqs.send_message(QueueUrl=settings.queue_url, MessageBody=message)
            logger.info(f"User data sent to SQS queue. Response: {res}")

        # create JWT
        jwt, expiry_seconds = token_service.create_token(user_id)

        return {"access_token": jwt, "token_type": "bearer", "max_age": expiry_seconds}
    except SpotifyAuthServiceException as e:
        logger.error(f"Failed to create tokens from code: {token_request.code} - {e}")
        raise HTTPException(status_code=401, detail="Invalid authorisation code.")
