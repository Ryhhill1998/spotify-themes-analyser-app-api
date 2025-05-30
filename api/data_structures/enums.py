from enum import Enum


class TopItemType(str, Enum):
    ARTIST = "artist"
    TRACK = "track"
    GENRE = "genre"
    EMOTION = "emotion"


class TopItemTimeRange(str, Enum):
    SHORT = "short_term"
    MEDIUM = "medium_term"
    LONG = "long_term"
