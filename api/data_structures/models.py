from enum import Enum

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey, RSAPrivateKey
from pydantic import BaseModel, ConfigDict


class EncryptionKeys(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    private_key: RSAPrivateKey
    public_key: RSAPublicKey


class DBUser(BaseModel):
    id: str
    refresh_token: str


class DBArtist(BaseModel):
    artist_id: str
    position: int


class DBTrack(BaseModel):
    track_id: str
    position: int


class DBGenre(BaseModel):
    genre_name: str
    count: int


class DBEmotion(BaseModel):
    emotion_name: str
    percentage: float
    track_id: str


class SpotifyTokenData(BaseModel):
    """
    Represents the Spotify authentication tokens for a user.

    Attributes
    ----------
    access_token : str
        The access token used for authenticated requests to the Spotify API.
    refresh_token : str
        The refresh token used to obtain a new access token.
    """

    access_token: str
    refresh_token: str | None


class SpotifyImage(BaseModel):
    """
    Represents an image associated with a Spotify item.

    Attributes
    ----------
    height : int
        The height of the image in pixels.
    width : int
        The width of the image in pixels.
    url : str
        The URL of the image.
    """

    height: int
    width: int
    url: str


class SpotifyProfile(BaseModel):
    id: str
    display_name: str
    email: str | None = None
    href: str
    images: list[SpotifyImage]
    followers: int


class SpotifyItemBase(BaseModel):
    """
    The most basic form of a Spotify item (e.g., artist or track).

    Attributes
    ----------
    id : str
        The unique identifier of the item.
    name : str
        The name of the item.
    """

    id: str
    name: str


class SpotifyTrackArtist(SpotifyItemBase):
    """
    Represents an artist associated with a track.

    This model is a simplified version of `SpotifyArtist`, containing only the basic artist details (ID and name).

    Inherits from
    -------------
    SpotifyItemBase, which provides the id and name attributes.
    """

    pass


class SpotifyItem(SpotifyItemBase):
    """
    Represents a Spotify item with additional metadata.

    Inherits from
    -------------
    SpotifyItemBase
        Provides the `id` and `name` attributes.

    Attributes
    ----------
    images : list[SpotifyImage]
        A list of images associated with the item.
    spotify_url : str
        The Spotify URL of the item.
    """

    images: list[SpotifyImage]
    spotify_url: str


class SpotifyArtist(SpotifyItem):
    """
    Represents a Spotify artist with additional metadata.

    Inherits from
    -------------
    SpotifyItem
        Provides the `id`, `name`, `images`, and `spotify_url` attributes.

    Attributes
    ----------
    genres : list[str]
        A list of genres associated with the artist.
    """

    genres: list[str]
    followers: int
    popularity: int


class SpotifyTrack(SpotifyItem):
    """
    Represents a Spotify track with associated metadata.

    Inherits from
    -------------
    SpotifyItem
        Provides the `id`, `name`, `images`, and `spotify_url` attributes.

    Attributes
    ----------
    artist : SpotifyTrackArtist
        The primary artist of the track.
    release_date : str
        The release date of the track.
    explicit : bool
        Indicates whether the track contains explicit content.
    duration_ms : int
        The duration of the track in milliseconds.
    popularity : int
        The popularity score of the track (0-100).
    """

    artist: SpotifyTrackArtist
    release_date: str
    album_name: str
    explicit: bool
    duration_ms: int
    popularity: int


class PositionChange(Enum(str)):
    UP = "up"
    DOWN = "down"
    NEW = "new"
    NONE = None


class TopArtist(SpotifyArtist):
    position: int
    position_change: PositionChange


class TopTrack(SpotifyTrack):
    position: int
    position_change: PositionChange


class TopGenre(DBGenre):
    position_change: PositionChange


class TopEmotion(DBEmotion):
    position_change: PositionChange


class AnalysisRequestBase(BaseModel):
    """
    Base class for requests related to track analysis.

    Attributes
    ----------
    track_id : str
        The unique identifier of the track.
    lyrics : str
        The lyrics of the track.
    """

    track_id: str
    lyrics: str


class Emotion(str, Enum):
    """
    Enum representing various emotions detected in track lyrics.

    Attributes
    ----------
    JOY : str
        Represents the emotion of joy.
    SADNESS : str
        Represents the emotion of sadness.
    ANGER : str
        Represents the emotion of anger.
    FEAR : str
        Represents the emotion of fear.
    LOVE : str
        Represents the emotion of love.
    HOPE : str
        Represents the emotion of hope.
    NOSTALGIA : str
        Represents the emotion of nostalgia.
    LONELINESS : str
        Represents the emotion of loneliness.
    CONFIDENCE : str
        Represents the emotion of confidence.
    DESPAIR : str
        Represents the emotion of despair.
    EXCITEMENT : str
        Represents the emotion of excitement.
    MYSTERY : str
        Represents the emotion of mystery.
    DEFIANCE : str
        Represents the emotion of defiance.
    GRATITUDE : str
        Represents the emotion of gratitude.
    SPIRITUALITY : str
        Represents the emotion of spirituality.
    """

    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    LOVE = "love"
    HOPE = "hope"
    NOSTALGIA = "nostalgia"
    LONELINESS = "loneliness"
    CONFIDENCE = "confidence"
    DESPAIR = "despair"
    EXCITEMENT = "excitement"
    MYSTERY = "mystery"
    DEFIANCE = "defiance"
    GRATITUDE = "gratitude"
    SPIRITUALITY = "spirituality"


class EmotionalTagsRequest(AnalysisRequestBase):
    """
    Represents a request for emotional tags for a track.

    Inherits from
    -------------
    AnalysisRequestBase
        Provides the `track_id` and `lyrics` attributes.

    Attributes
    ----------
    emotion : Emotion
        The emotion being analyzed.
    """

    emotion: Emotion


class EmotionalTagsResponse(EmotionalTagsRequest):
    """
    Represents a response containing emotional tags for a track.

    Inherits from
    -------------
    EmotionalTagsRequest
        Provides the `track_id`, `lyrics`, and `emotion` attributes.
    """

    pass
