#!/usr/bin/env python3
"""Basic functionality test for Orik data models."""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import (
    SlideData, OrikContent, OrikResponse, SystemStatus,
    VoiceConfig, OrikPersonality, ResponseType
)
from utils.validation import validate_orik_tags, validate_presentation_path


def test_slide_data():
    """Test SlideData creation and validation."""
    print("Testing SlideData...")
    
    slide = SlideData(
        slide_index=1,
        slide_title="Introduction to Orik",
        speaker_notes="Welcome everyone [Orik] Oh great, another introduction slide",
        presentation_path="/path/to/presentation.pptx",
        timestamp=datetime.now()
    )
    
    assert slide.slide_index == 1
    assert slide.has_speaker_notes is True
    print("✓ SlideData creation successful")
    
    # Test to_dict conversion
    slide_dict = slide.to_dict()
    assert 'slide_index' in slide_dict
    assert 'timestamp' in slide_dict
    print("✓ SlideData to_dict conversion successful")


def test_orik_content():
    """Test OrikContent extraction."""
    print("Testing OrikContent...")
    
    slide = SlideData(
        slide_index=2,
        slide_title="Technical Details",
        speaker_notes="This covers the architecture [Orik] Wow Aaron, revolutionary stuff from 2012 [Orik] Let me guess, this will change everything?",
        presentation_path="/path/to/presentation.pptx",
        timestamp=datetime.now()
    )
    
    content = OrikContent.extract_from_notes(slide)
    
    assert content.has_orik_tags is True
    assert content.tag_count == 2
    assert "Wow Aaron, revolutionary stuff from 2012" in content.extracted_tags
    assert "Let me guess, this will change everything?" in content.extracted_tags
    print("✓ OrikContent extraction successful")
    
    # Test combined content
    combined = content.get_combined_content()
    assert len(combined) > 0
    print("✓ OrikContent combined content successful")


def test_orik_response():
    """Test OrikResponse creation."""
    print("Testing OrikResponse...")
    
    response = OrikResponse(
        response_text="Oh brilliant, Aaron. Just brilliant.",
        confidence=0.85,
        response_type=ResponseType.TAGGED,
        generation_time=datetime.now(),
        source_content="Test slide content"
    )
    
    assert response.is_high_confidence is True
    assert response.word_count == 5
    assert response.estimated_duration_seconds > 0
    print("✓ OrikResponse creation successful")


def test_system_status():
    """Test SystemStatus functionality."""
    print("Testing SystemStatus...")
    
    status = SystemStatus(
        is_monitoring=True,
        presentation_connected=True,
        tts_available=True,
        audio_ready=False,  # One component failing
        last_activity=datetime.now()
    )
    
    assert status.is_fully_operational is False  # Audio not ready
    assert status.has_errors is False  # No explicit error set
    assert "audio" in status.failed_components
    assert len(status.operational_components) == 3
    print("✓ SystemStatus functionality successful")
    
    # Test error handling
    status.set_error("Audio device not found")
    assert status.has_errors is True
    assert status.error_state == "Audio device not found"
    
    status.clear_error()
    assert status.has_errors is False
    print("✓ SystemStatus error handling successful")


def test_voice_config():
    """Test VoiceConfig functionality."""
    print("Testing VoiceConfig...")
    
    config = VoiceConfig(
        voice_id="Matthew",
        speed=1.1,
        pitch="-10%",
        volume=0.8,
        engine="neural"
    )
    
    # Test Polly parameters
    polly_params = config.to_polly_params()
    assert polly_params['VoiceId'] == "Matthew"
    assert polly_params['Engine'] == "neural"
    print("✓ VoiceConfig Polly parameters successful")
    
    # Test SSML generation
    ssml = config.to_ssml_prosody("Hello world")
    assert "<prosody" in ssml
    assert "Hello world" in ssml
    assert "</prosody>" in ssml
    print("✓ VoiceConfig SSML generation successful")


def test_orik_personality():
    """Test OrikPersonality functionality."""
    print("Testing OrikPersonality...")
    
    personality = OrikPersonality.create_default()
    
    assert personality.sarcasm_level == 0.8
    assert len(personality.response_templates) > 0
    assert len(personality.forbidden_topics) > 0
    print("✓ OrikPersonality default creation successful")
    
    # Test sarcasm modifier
    modifier = personality.get_sarcasm_modifier()
    assert isinstance(modifier, str)
    assert len(modifier) > 0
    print("✓ OrikPersonality sarcasm modifier successful")


def test_validation_functions():
    """Test validation utility functions."""
    print("Testing validation functions...")
    
    # Test Orik tag validation
    tags = validate_orik_tags("Regular text [Orik] First tag [Orik] Second tag")
    assert len(tags) == 2
    assert "First tag" in tags
    assert "Second tag" in tags
    print("✓ Orik tag validation successful")
    
    # Test presentation path validation
    assert validate_presentation_path("/path/to/file.pptx") is True
    assert validate_presentation_path("/path/to/file.pdf") is False
    assert validate_presentation_path("") is False
    print("✓ Presentation path validation successful")


def main():
    """Run all tests."""
    print("Running Orik basic functionality tests...\n")
    
    try:
        test_slide_data()
        print()
        
        test_orik_content()
        print()
        
        test_orik_response()
        print()
        
        test_system_status()
        print()
        
        test_voice_config()
        print()
        
        test_orik_personality()
        print()
        
        test_validation_functions()
        print()
        
        print("🎉 All tests passed! Core data models are working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)