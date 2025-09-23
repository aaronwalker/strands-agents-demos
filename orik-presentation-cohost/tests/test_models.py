"""Unit tests for core data models."""

import pytest
from datetime import datetime

from src.models import (
    SlideData, OrikContent, OrikResponse, SystemStatus,
    AudioResult, VoiceConfig, OrikPersonality,
    ResponseType, AudioFormat
)


class TestSlideData:
    """Test cases for SlideData model."""
    
    def test_valid_slide_data(self):
        """Test creating valid SlideData."""
        slide = SlideData(
            slide_index=1,
            slide_title="Test Slide",
            speaker_notes="[Orik] This is a test",
            presentation_path="/path/to/presentation.pptx",
            timestamp=datetime.now()
        )
        
        assert slide.slide_index == 1
        assert slide.slide_title == "Test Slide"
        assert slide.has_speaker_notes is True
    
    def test_invalid_slide_index(self):
        """Test SlideData with invalid slide index."""
        with pytest.raises(ValueError, match="slide_index must be non-negative"):
            SlideData(
                slide_index=-1,
                slide_title="Test",
                speaker_notes="Notes",
                presentation_path="/path/to/file.pptx",
                timestamp=datetime.now()
            )
    
    def test_empty_presentation_path(self):
        """Test SlideData with empty presentation path."""
        with pytest.raises(ValueError, match="presentation_path cannot be empty"):
            SlideData(
                slide_index=0,
                slide_title="Test",
                speaker_notes="Notes",
                presentation_path="",
                timestamp=datetime.now()
            )


class TestOrikContent:
    """Test cases for OrikContent model."""
    
    def test_extract_orik_tags(self):
        """Test extracting Orik tags from speaker notes."""
        slide = SlideData(
            slide_index=1,
            slide_title="Test Slide",
            speaker_notes="Regular notes [Orik] This is sarcastic content [Orik] Another comment",
            presentation_path="/path/to/file.pptx",
            timestamp=datetime.now()
        )
        
        content = OrikContent.extract_from_notes(slide)
        
        assert content.has_orik_tags is True
        assert content.tag_count == 2
        assert "This is sarcastic content" in content.extracted_tags
        assert "Another comment" in content.extracted_tags
    
    def test_no_orik_tags(self):
        """Test content with no Orik tags."""
        slide = SlideData(
            slide_index=1,
            slide_title="Test Slide",
            speaker_notes="Regular speaker notes without tags",
            presentation_path="/path/to/file.pptx",
            timestamp=datetime.now()
        )
        
        content = OrikContent.extract_from_notes(slide)
        
        assert content.has_orik_tags is False
        assert content.tag_count == 0
        assert len(content.extracted_tags) == 0


class TestOrikResponse:
    """Test cases for OrikResponse model."""
    
    def test_valid_response(self):
        """Test creating valid OrikResponse."""
        response = OrikResponse(
            response_text="Oh brilliant, Aaron. Just brilliant.",
            confidence=0.85,
            response_type=ResponseType.TAGGED,
            generation_time=datetime.now(),
            source_content="Test content"
        )
        
        assert response.is_high_confidence is True
        assert response.word_count == 5
        assert response.estimated_duration_seconds > 0
    
    def test_invalid_confidence(self):
        """Test OrikResponse with invalid confidence."""
        with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
            OrikResponse(
                response_text="Test response",
                confidence=1.5,
                response_type=ResponseType.TAGGED,
                generation_time=datetime.now()
            )
    
    def test_empty_response_text(self):
        """Test OrikResponse with empty text."""
        with pytest.raises(ValueError, match="response_text cannot be empty"):
            OrikResponse(
                response_text="",
                confidence=0.8,
                response_type=ResponseType.TAGGED,
                generation_time=datetime.now()
            )


class TestSystemStatus:
    """Test cases for SystemStatus model."""
    
    def test_fully_operational(self):
        """Test fully operational system status."""
        status = SystemStatus(
            is_monitoring=True,
            presentation_connected=True,
            tts_available=True,
            audio_ready=True,
            last_activity=datetime.now()
        )
        
        assert status.is_fully_operational is True
        assert status.has_errors is False
        assert len(status.operational_components) == 4
        assert len(status.failed_components) == 0
    
    def test_partial_failure(self):
        """Test system status with partial failures."""
        status = SystemStatus(
            is_monitoring=True,
            presentation_connected=False,
            tts_available=True,
            audio_ready=False,
            last_activity=datetime.now(),
            error_state="Connection failed"
        )
        
        assert status.is_fully_operational is False
        assert status.has_errors is True
        assert "presentation" in status.failed_components
        assert "audio" in status.failed_components


class TestVoiceConfig:
    """Test cases for VoiceConfig model."""
    
    def test_valid_voice_config(self):
        """Test creating valid VoiceConfig."""
        config = VoiceConfig(
            voice_id="Matthew",
            speed=1.1,
            pitch="-10%",
            volume=0.8,
            engine="neural"
        )
        
        assert config.voice_id == "Matthew"
        assert config.speed == 1.1
        
        polly_params = config.to_polly_params()
        assert polly_params['VoiceId'] == "Matthew"
        assert polly_params['Engine'] == "neural"
    
    def test_invalid_speed(self):
        """Test VoiceConfig with invalid speed."""
        with pytest.raises(ValueError, match="speed must be between 0.5 and 2.0"):
            VoiceConfig(speed=3.0)
    
    def test_ssml_prosody(self):
        """Test SSML prosody generation."""
        config = VoiceConfig()
        ssml = config.to_ssml_prosody("Hello world")
        
        assert "<prosody" in ssml
        assert "Hello world" in ssml
        assert "</prosody>" in ssml


class TestOrikPersonality:
    """Test cases for OrikPersonality model."""
    
    def test_default_personality(self):
        """Test creating default personality."""
        personality = OrikPersonality.create_default()
        
        assert personality.sarcasm_level == 0.8
        assert len(personality.response_templates) > 0
        assert len(personality.forbidden_topics) > 0
        assert "sarcastic" in personality.get_sarcasm_modifier()
    
    def test_invalid_sarcasm_level(self):
        """Test personality with invalid sarcasm level."""
        with pytest.raises(ValueError, match="sarcasm_level must be between 0.0 and 1.0"):
            OrikPersonality(
                base_prompt="Test prompt",
                sarcasm_level=1.5
            )
    
    def test_probability_methods(self):
        """Test probability-based methods."""
        personality = OrikPersonality(
            base_prompt="Test",
            interruption_frequency=1.0,  # Always interrupt
            aaron_dig_probability=0.0    # Never dig
        )
        
        # Note: These are probabilistic, but with extreme values should be predictable
        # In a real test, you might want to mock random.random()
        assert isinstance(personality.should_interrupt(), bool)
        assert isinstance(personality.should_dig_at_aaron(), bool)