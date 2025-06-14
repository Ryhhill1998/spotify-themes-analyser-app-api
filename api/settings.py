from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Represents the application configuration settings.

    Attributes
    ----------
    spotify_client_id : str
        The client ID for Spotify API authentication.
    spotify_client_secret : str
        The client secret for Spotify API authentication.
    spotify_auth_user_scope : str
        The scope of user permissions required for Spotify authentication.
    spotify_auth_redirect_uri : str
        The redirect URI used in the Spotify authentication flow.
    spotify_auth_base_url : str
        The base URL for authenticating with the Spotify API.
    spotify_data_base_url : str
        The base URL for retrieving data from the Spotify API.
    frontend_url : str
        The URL of the frontend application.

    allowed_origins : list[str]
        A list of allowed origins for CORS configuration.

    model_config : SettingsConfigDict
        Configuration for loading environment variables from a `.env` file.
    """

    spotify_client_id: str
    spotify_client_secret: str
    spotify_auth_user_scope: str
    spotify_auth_redirect_uri: str
    spotify_auth_base_url: str
    spotify_data_base_url: str
    frontend_url: str

    allowed_origins: list[str]

    db_host: str
    db_name: str
    db_user: str
    db_pass: str

    queue_url: str
    aws_access_key: str
    aws_secret_access_key: str
    aws_region: str

    encryption_secret_key: str
    encryption_algorithm: str

    redis_host: str
    redis_port: int
    redis_username: str
    redis_password: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
