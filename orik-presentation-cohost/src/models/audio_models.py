"""Audio-related data models."""

from dataclasses import dataclass
from typing import Optional

from .enums import AudioFormat


@dataclass
class VoiceConfig:
    """Configuration for text-to-speech voice parameters."""
    
    voice_id: str = "Matthew"  # Amazon Polly voice ID
    speed: float = 1.1         # Speech rate multiplier
    pitch: str = "-10%"        # Pitch adjustment
    volume: float = 1.0        # Volume level (0.0 to 1.0)
    engine: str = "standard"   # Polly engine type
    
    def __post_init__(self):
        """Validate voice configuration."""
        if not self.voice_id:
            raise ValueError("voice_id cannot be empty")
        
        if not 0.5 <= self.speed <= 2.0:
            raise ValueError("speed must be between 0.5 and 2.0")
        
        if not 0.0 <= self.volume <= 1.0:
            raise ValueError("volume must be between 0.0 and 1.0")
        
        if self.engine not in ["standard", "neural"]:
            raise ValueError("engine must be 'standard' or 'neural'")
    
    def to_polly_params(self) -> dict:
        """Convert to Amazon Polly API parameters."""
        return {
            'VoiceId': self.voice_id,
            'Engine': self.engine,
            'OutputFormat': 'mp3'
        }
    
    def to_ssml_prosody(self, text: str) -> str:
        """Wrap text in SSML prosody tags."""
        return f'<prosody rate="{self.speed}" pitch="{self.pitch}">{text}</prosody>'


@dataclass
class AudioResult:
    """Result from text-to-speech synthesis."""
    
    audio_data: bytes
    format: AudioFormat
    duration_ms: int
    voice_config: VoiceConfig
    text_source: Optional[str] = None
    
    def __post_init__(self):
        """Validate audio result."""
        if not self.audio_data:
            raise ValueError("audio_data cannot be empty")
        
        if not isinstance(self.format, AudioFormat):
            raise ValueError("format must be an AudioFormat enum")
        
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        
        if not isinstance(self.voice_config, VoiceConfig):
            raise ValueError("voice_config must be a VoiceConfig instance")
    
    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration_ms / 1000.0
    
    @property
    def size_bytes(self) -> int:
        """Get audio data size in bytes."""
        return len(self.audio_data)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'format': self.format.value,
            'duration_ms': self.duration_ms,
            'duration_seconds': self.duration_seconds,
            'size_bytes': self.size_bytes,
            'voice_config': {
                'voice_id': self.voice_config.voice_id,
                'speed': self.voice_config.speed,
                'pitch': self.voice_config.pitch,
                'volume': self.voice_config.volume,
                'engine': self.voice_config.engine
            },
            'text_source': self.text_source
        }