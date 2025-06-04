import base64
import urllib.parse
from functools import cached_property
from loguru import logger

import pydantic

from api.data_structures.models import SpotifyTokens
from api.services.endpoint_requester import EndpointRequester, EndpointRequesterException


class SpotifyAuthServiceException(Exception):
    """
    Exception raised when the SpotifyAuthService encounters an error.

    Parameters
    ----------
    message : str
        The error message describing the failure.
    """

    def __init__(self, message):
        super().__init__(message)


class SpotifyAuthService:
    """
    Service responsible for handling authentication and token management for Spotify's API.

    This class provides methods for generating authorization URLs, obtaining access tokens, and refreshing expired
    tokens.

    Inherits from
    -------------
    MusicService, which provides core attributes such as client_id, client_secret, base_url, and endpoint_requester.

    Attributes
    ----------
    redirect_uri : str
        The URI to which Spotify will redirect after authentication.
    auth_scope : str
        The scope of permissions requested from the Spotify API.

    Methods
    -------
    generate_auth_url(state: str) -> str
        Generates the Spotify authorization URL for user authentication.

    create_tokens(auth_code: str) -> TokenData
        Exchanges an authorization code for access and refresh tokens.

    refresh_tokens(refresh_token: str) -> TokenData
        Refreshes an expired access token using the refresh token.
    """


    def __init__(
            self,
            client_id: str,
            client_secret: str,
            base_url: str,
            redirect_uri: str,
            auth_scope: str,
            endpoint_requester: EndpointRequester
    ):
        """
        Parameters
        ----------
        client_id : str
            The Spotify API client ID.
        client_secret : str
            The Spotify API client secret.
        base_url : str
            The base URL of the Spotify Web API.
        redirect_uri : str
            The URI to which Spotify will redirect after authentication.
        auth_scope : str
            The scope of permissions requested from the Spotify API.
        endpoint_requester : EndpointRequester
            The service responsible for making API requests.
        """

        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.redirect_uri = redirect_uri
        self.auth_scope = auth_scope
        self.endpoint_requester = endpoint_requester

    @cached_property
    def _auth_header(self) -> str:
        """
        Generates the base64-encoded authorization header required for authentication requests and caches it so it is
        only computed once.

        Returns
        -------
        str
            The base64-encoded client ID and secret.
        """

        return base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

    def generate_auth_url(self, state: str) -> str:
        """
        Generates the Spotify authorization URL for user authentication.

        Parameters
        ----------
        state : str
            A unique state parameter used for security and to prevent request forgery.

        Returns
        -------
        str
            The generated Spotify authorization URL.
        """

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": self.auth_scope,
            "state": state
        }

        return f"{self.base_url}/authorize?" + urllib.parse.urlencode(params)

    async def _get_tokens(self, data: dict[str, str], refresh_token: str | None = None) -> SpotifyTokens:
        """
        Retrieves access and refresh tokens from the Spotify API.

        Parameters
        ----------
        data : dict[str, str]
            The request payload containing necessary authentication parameters.
        refresh_token : str, optional
            The refresh token to use when refreshing access, default is None.

        Returns
        -------
        SpotifyTokens
            A validated TokenData object containing access and refresh tokens.

        Raises
        ------
        SpotifyAuthServiceException
            If the request or token validation fails.
        """

        try:
            url = f"{self.base_url}/api/token"
            headers = {"Authorization": f"Basic {self._auth_header}", "Content-Type": "application/x-www-form-urlencoded"}

            token_data = await self.endpoint_requester.post(url=url, headers=headers, data=data)
            logger.info(f"{token_data = }")

            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token", refresh_token)

            return SpotifyTokens(access_token=access_token, refresh_token=refresh_token)
        except EndpointRequesterException as e:
            error_message = f"Spotify API token request failed - {e}"
            logger.error(error_message)
            raise SpotifyAuthServiceException(error_message)
        except pydantic.ValidationError as e:
            error_message = f"Failed to validate tokens - {e}"
            logger.error(error_message)
            raise SpotifyAuthServiceException(error_message)

    async def create_tokens(self, auth_code: str) -> SpotifyTokens:
        """
        Exchanges an authorization code for access and refresh tokens.

        Parameters
        ----------
        auth_code : str
            The authorization code received from Spotify after user login.

        Returns
        -------
        SpotifyTokens
            A validated TokenData object containing access and refresh tokens.

        Raises
        ------
        SpotifyAuthServiceException
            If token retrieval fails.
        """

        data = {"code": auth_code, "redirect_uri": self.redirect_uri, "grant_type": "authorization_code"}

        tokens = await self._get_tokens(data=data)

        return tokens

    async def refresh_tokens(self, refresh_token: str) -> SpotifyTokens:
        """
        Refreshes an expired access token using the refresh token.

        Parameters
        ----------
        refresh_token : str
            The refresh token to use for obtaining a new access token.

        Returns
        -------
        SpotifyTokens
            A validated TokenData object containing new access and refresh tokens.

        Raises
        ------
        SpotifyAuthServiceException
            If token retrieval fails.
        """

        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        tokens = await self._get_tokens(data=data, refresh_token=refresh_token)

        return tokens
