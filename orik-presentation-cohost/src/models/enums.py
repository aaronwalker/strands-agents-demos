"""Enumerations used throughout the Orik system."""

from enum import Enum


class ResponseType(Enum):
    """Types of responses Orik can generate."""
    TAGGED = "tagged"           # Response to [Orik] tagged content
    RANDOM_DIG = "random_dig"   # Random sarcastic one-liner
    CONTEXTUAL = "contextual"   # Context-aware response


class PresentationSoftware(Enum):
    """Supported presentation software types."""
    POWERPOINT = "powerpoint"
    GOOGLE_SLIDES = "google_slides"
    KEYNOTE = "keynote"
    GENERIC = "generic"


class PlaybackStatus(Enum):
    """Audio playback status states."""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    ERROR = "error"


class AudioFormat(Enum):
    """Supported audio formats."""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"