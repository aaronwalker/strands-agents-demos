"""Unit tests for validation functions."""

import pytest
from datetime import datetime

from src.utils.validation import (
    validate_slide_data, validate_orik_content, validate_system_status,
    validate_presentation_path, validate_orik_tags, validate_audio_config
)
from src.models import SlideData


class TestValidateSlideData:
    """Test cases for slide data validation."""
    
    def test_valid_slide_data_dict(self):
        """Test validating valid slide data dictionary."""
        data = {
            'slide_index': 1,
            'slide_title': 'Test Slide',
            'speaker_notes': 'Test notes',
            'presentation_path': '/path/to/file.pptx'
        }
        
        slide = validate_slide_data(data)
        
        assert isinstance(slide, SlideData)
        assert slide.slide_index == 1
        assert slide.slide_title == 'Test Slide'
    
    def test_missing_required_field(self):
        """Test validation with missing required field."""
        data = {
            'slide_index': 1,
            'slide_title': 'Test Slide'
            # Missing speaker_notes and presentation_path
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            validate_slide_data(data)
    
    def test_timestamp_conversion(self):
        """Test timestamp string conversion."""
        timestamp_str = "2024-01-01T12:00:00"
        data = {
            'slide_index': 1,
            'slide_title': 'Test Slide',
            'speaker_notes': 'Test notes',
            'presentation_path': '/path/to/file.pptx',
            'timestamp': timestamp_str
        }
        
        slide = validate_slide_data(data)
        
        assert isinstance(slide.timestamp, datetime)


class TestValidateOrikContent:
    """Test cases for Orik content validation."""
    
    def test_valid_orik_content(self):
        """Test validating valid Orik content."""
        slide = SlideData(
            slide_index=1,
            slide_title="Test",
            speaker_notes="[Orik] Test content",
            presentation_path="/path/to/file.pptx",
            timestamp=datetime.now()
        )
        
        content = validate_orik_content(slide)
        
        assert content.has_orik_tags is True
        assert "Test content" in content.extracted_tags
    
    def test_invalid_slide_data_type(self):
        """Test validation with invalid slide data type."""
        with pytest.raises(ValueError, match="slide_data must be a SlideData instance"):
            validate_orik_content("not a slide data object")


class TestValidateSystemStatus:
    """Test cases for system status validation."""
    
    def test_valid_system_status_dict(self):
        """Test validating valid system status dictionary."""
        data = {
            'is_monitoring': True,
            'presentation_connected': False,
            'tts_available': True,
            'audio_ready': True
        }
        
        status = validate_system_status(data)
        
        assert status.is_monitoring is True
        assert status.presentation_connected is False
    
    def test_missing_required_status_field(self):
        """Test validation with missing required field."""
        data = {
            'is_monitoring': True
            # Missing other required fields
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            validate_system_status(data)


class TestValidatePresentationPath:
    """Test cases for presentation path validation."""
    
    def test_valid_presentation_paths(self):
        """Test valid presentation file paths."""
        valid_paths = [
            "/path/to/presentation.pptx",
            "C:\\Users\\Documents\\slides.ppt",
            "presentation.odp",
            "/home/user/keynote.key"
        ]
        
        for path in valid_paths:
            assert validate_presentation_path(path) is True
    
    def test_invalid_presentation_paths(self):
        """Test invalid presentation file paths."""
        invalid_paths = [
            "",
            None,
            "/path/to/document.pdf",
            "image.jpg",
            123  # Not a string
        ]
        
        for path in invalid_paths:
            assert validate_presentation_path(path) is False


class TestValidateOrikTags:
    """Test cases for Orik tag validation."""
    
    def test_valid_orik_tags(self):
        """Test extracting valid Orik tags."""
        text = "Regular text [Orik] First tag [Orik] Second tag more text"
        
        tags = validate_orik_tags(text)
        
        assert len(tags) == 2
        assert "First tag" in tags
        assert "Second tag" in tags
    
    def test_no_orik_tags(self):
        """Test text with no Orik tags."""
        text = "Regular text without any tags"
        
        tags = validate_orik_tags(text)
        
        assert len(tags) == 0
    
    def test_empty_or_invalid_text(self):
        """Test empty or invalid text input."""
        assert validate_orik_tags("") == []
        assert validate_orik_tags(None) == []
        assert validate_orik_tags(123) == []
    
    def test_tag_length_limit(self):
        """Test tag length validation."""
        # Create a very long tag (over 500 characters)
        long_content = "x" * 600
        text = f"[Orik] {long_content}"
        
        tags = validate_orik_tags(text)
        
        # Should be filtered out due to length
        assert len(tags) == 0


class TestValidateAudioConfig:
    """Test cases for audio configuration validation."""
    
    def test_valid_audio_config(self):
        """Test valid audio configuration."""
        config = {
            'voice_id': 'Matthew',
            'speed': 1.1,
            'volume': 0.8
        }
        
        assert validate_audio_config(config) is True
    
    def test_invalid_speed_range(self):
        """Test audio config with invalid speed."""
        config = {
            'voice_id': 'Matthew',
            'speed': 3.0,  # Too high
            'volume': 0.8
        }
        
        assert validate_audio_config(config) is False
    
    def test_invalid_volume_range(self):
        """Test audio config with invalid volume."""
        config = {
            'voice_id': 'Matthew',
            'speed': 1.1,
            'volume': 1.5  # Too high
        }
        
        assert validate_audio_config(config) is False
    
    def test_missing_required_fields(self):
        """Test audio config with missing fields."""
        config = {
            'voice_id': 'Matthew'
            # Missing speed and volume
        }
        
        assert validate_audio_config(config) is False
    
    def test_empty_voice_id(self):
        """Test audio config with empty voice ID."""
        config = {
            'voice_id': '',
            'speed': 1.1,
            'volume': 0.8
        }
        
        assert validate_audio_config(config) is False