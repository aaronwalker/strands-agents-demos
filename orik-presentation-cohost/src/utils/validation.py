"""Validation functions for core data models."""

from datetime import datetime
from typing import Any, Dict, List

from models import SlideData, OrikContent, SystemStatus


def validate_slide_data(data: Dict[str, Any]) -> SlideData:
    """Validate and create SlideData from dictionary."""
    required_fields = ['slide_index', 'slide_title', 'speaker_notes', 'presentation_path']
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Convert timestamp if it's a string
    timestamp = data.get('timestamp')
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    elif timestamp is None:
        timestamp = datetime.now()
    
    return SlideData(
        slide_index=int(data['slide_index']),
        slide_title=str(data['slide_title']),
        speaker_notes=str(data['speaker_notes']),
        presentation_path=str(data['presentation_path']),
        timestamp=timestamp
    )


def validate_orik_content(slide_data: SlideData) -> OrikContent:
    """Validate and extract OrikContent from SlideData."""
    if not isinstance(slide_data, SlideData):
        raise ValueError("slide_data must be a SlideData instance")
    
    return OrikContent.extract_from_notes(slide_data)


def validate_system_status(data: Dict[str, Any]) -> SystemStatus:
    """Validate and create SystemStatus from dictionary."""
    required_fields = ['is_monitoring', 'presentation_connected', 'tts_available', 'audio_ready']
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Convert timestamp if it's a string
    last_activity = data.get('last_activity')
    if isinstance(last_activity, str):
        last_activity = datetime.fromisoformat(last_activity)
    elif last_activity is None:
        last_activity = datetime.now()
    
    return SystemStatus(
        is_monitoring=bool(data['is_monitoring']),
        presentation_connected=bool(data['presentation_connected']),
        tts_available=bool(data['tts_available']),
        audio_ready=bool(data['audio_ready']),
        last_activity=last_activity,
        error_state=data.get('error_state')
    )


def validate_presentation_path(path: str) -> bool:
    """Validate presentation file path."""
    if not path or not isinstance(path, str):
        return False
    
    valid_extensions = ['.pptx', '.ppt', '.odp', '.key']
    return any(path.lower().endswith(ext) for ext in valid_extensions)


def validate_orik_tags(text: str) -> List[str]:
    """Validate and extract Orik tags from text."""
    import re
    
    if not text or not isinstance(text, str):
        return []
    
    # Pattern to match [Orik] tags
    pattern = r'\[Orik\]\s*([^[\n]*?)(?=\[|$)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    # Clean and validate extracted content
    valid_tags = []
    for match in matches:
        cleaned = match.strip()
        if cleaned and len(cleaned) <= 500:  # Reasonable length limit
            valid_tags.append(cleaned)
    
    return valid_tags


def validate_audio_config(config: Dict[str, Any]) -> bool:
    """Validate audio configuration parameters."""
    required_fields = ['voice_id', 'speed', 'volume']
    
    for field in required_fields:
        if field not in config:
            return False
    
    # Validate ranges
    if not 0.5 <= config['speed'] <= 2.0:
        return False
    
    if not 0.0 <= config['volume'] <= 1.0:
        return False
    
    if not config['voice_id'] or not isinstance(config['voice_id'], str):
        return False
    
    return True