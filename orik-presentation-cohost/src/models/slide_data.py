"""SlideData model for presentation slide information."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SlideData:
    """Represents data from a presentation slide."""
    
    slide_index: int
    slide_title: str
    speaker_notes: str
    presentation_path: str
    timestamp: datetime
    
    def __post_init__(self):
        """Validate slide data after initialization."""
        if self.slide_index < 0:
            raise ValueError("slide_index must be non-negative")
        
        if not self.presentation_path:
            raise ValueError("presentation_path cannot be empty")
        
        if not isinstance(self.timestamp, datetime):
            raise ValueError("timestamp must be a datetime object")
    
    @property
    def has_speaker_notes(self) -> bool:
        """Check if slide has speaker notes."""
        return bool(self.speaker_notes and self.speaker_notes.strip())
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'slide_index': self.slide_index,
            'slide_title': self.slide_title,
            'speaker_notes': self.speaker_notes,
            'presentation_path': self.presentation_path,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class SlideInfo:
    """Basic slide information without full SlideData."""
    slide_index: int
    slide_title: str
    total_slides: int
    is_slideshow_mode: bool = False
    
    def __post_init__(self):
        """Validate slide info after initialization."""
        if self.slide_index < 0:
            raise ValueError("slide_index must be non-negative")
        
        if self.total_slides < 0:
            raise ValueError("total_slides must be non-negative")
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'slide_index': self.slide_index,
            'slide_title': self.slide_title,
            'total_slides': self.total_slides,
            'is_slideshow_mode': self.is_slideshow_mode
        }


@dataclass
class SlideEvent:
    """Represents a slide change event."""
    event_type: str  # "slide_changed", "presentation_started", "presentation_ended"
    slide_data: Optional['SlideData'] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()