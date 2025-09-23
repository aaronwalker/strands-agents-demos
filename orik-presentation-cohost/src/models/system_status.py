"""SystemStatus model for tracking system state."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SystemStatus:
    """Represents the current status of the Orik system."""
    
    is_monitoring: bool
    presentation_connected: bool
    tts_available: bool
    audio_ready: bool
    last_activity: datetime
    error_state: Optional[str] = None
    
    def __post_init__(self):
        """Validate system status after initialization."""
        if not isinstance(self.last_activity, datetime):
            raise ValueError("last_activity must be a datetime object")
    
    @property
    def is_fully_operational(self) -> bool:
        """Check if all systems are operational."""
        return (
            self.is_monitoring and
            self.presentation_connected and
            self.tts_available and
            self.audio_ready and
            self.error_state is None
        )
    
    @property
    def has_errors(self) -> bool:
        """Check if system has any errors."""
        return self.error_state is not None
    
    @property
    def operational_components(self) -> list:
        """Get list of operational components."""
        components = []
        if self.is_monitoring:
            components.append("monitoring")
        if self.presentation_connected:
            components.append("presentation")
        if self.tts_available:
            components.append("tts")
        if self.audio_ready:
            components.append("audio")
        return components
    
    @property
    def failed_components(self) -> list:
        """Get list of failed components."""
        components = []
        if not self.is_monitoring:
            components.append("monitoring")
        if not self.presentation_connected:
            components.append("presentation")
        if not self.tts_available:
            components.append("tts")
        if not self.audio_ready:
            components.append("audio")
        return components
    
    def update_activity(self) -> None:
        """Update last activity timestamp to now."""
        self.last_activity = datetime.now()
    
    def set_error(self, error_message: str) -> None:
        """Set error state with message."""
        self.error_state = error_message
        self.update_activity()
    
    def clear_error(self) -> None:
        """Clear error state."""
        self.error_state = None
        self.update_activity()
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'is_monitoring': self.is_monitoring,
            'presentation_connected': self.presentation_connected,
            'tts_available': self.tts_available,
            'audio_ready': self.audio_ready,
            'last_activity': self.last_activity.isoformat(),
            'error_state': self.error_state,
            'is_fully_operational': self.is_fully_operational,
            'has_errors': self.has_errors,
            'operational_components': self.operational_components,
            'failed_components': self.failed_components
        }