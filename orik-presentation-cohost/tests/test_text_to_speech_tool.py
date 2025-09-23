"""Unit tests for TextToSpeechTool MCP server."""

import pytest
import asyncio
import json
import base64
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

# Import the modules to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_tools.text_to_speech_tool import (
    TextToSpeechTool, 
    PollyTTSClient, 
    AudioCache, 
    SSMLProcessor
)
from models.audio_models import VoiceConfig, AudioResult
from models.enums import AudioFormat


class TestSSMLProcessor:
    """Test SSML processing functionality."""
    
    def test_add_sarcastic_emphasis(self):
        """Test adding emphasis to sarcastic words."""
        text = "Oh brilliant, Aaron. That's absolutely perfect."
        result = SSMLProcessor.add_sarcastic_emphasis(text)
        
        assert '<emphasis level="strong">brilliant</emphasis>' in result
        assert '<emphasis level="strong">absolutely</emphasis>' in result
        assert '<emphasis level="strong">perfect</emphasis>' in result
    
    def test_add_pauses_for_effect(self):
        """Test adding strategic pauses."""
        text = "Oh, that's interesting... Well, let's see."
        result = SSMLProcessor.add_pauses_for_effect(text)
        
        assert '<break time="0.5s"/>' in result
        assert '<break time="1s"/>' in result
    
    def test_wrap_in_prosody(self):
        """Test wrapping text in SSML prosody tags."""
        text = "Sure, Aaron. That's brilliant."
        voice_config = VoiceConfig()
        
        result = SSMLProcessor.wrap_in_prosody(text, voice_config)
        
        assert result.startswith('<speak>')
        assert result.endswith('</speak>')
        assert '<prosody' in result
        assert '</prosody>' in result
        assert '<emphasis level="strong">brilliant</emphasis>' in result


class TestAudioCache:
    """Test audio caching functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = AudioCache(self.temp_dir)
        
        self.voice_config = VoiceConfig()
        self.test_audio_data = b"fake_audio_data_for_testing"
        self.audio_result = AudioResult(
            audio_data=self.test_audio_data,
            format=AudioFormat.MP3,
            duration_ms=2000,
            voice_config=self.voice_config,
            text_source="test text"
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_and_retrieve_audio(self):
        """Test caching and retrieving audio."""
        text = "Test caching functionality"
        
        # Cache audio
        self.cache.cache_audio(text, self.voice_config, self.audio_result)
        
        # Retrieve cached audio
        cached_result = self.cache.get_cached_audio(text, self.voice_config)
        
        assert cached_result is not None
        assert cached_result.audio_data == self.test_audio_data
        assert cached_result.format == AudioFormat.MP3
        assert cached_result.duration_ms == 2000
    
    def test_cache_key_generation(self):
        """Test that different texts/configs generate different cache keys."""
        text1 = "First text"
        text2 = "Second text"
        
        key1 = self.cache._get_cache_key(text1, self.voice_config)
        key2 = self.cache._get_cache_key(text2, self.voice_config)
        
        assert key1 != key2
        
        # Different voice config should also generate different key
        voice_config2 = VoiceConfig(voice_id="Brian")
        key3 = self.cache._get_cache_key(text1, voice_config2)
        
        assert key1 != key3
    
    def test_cache_miss(self):
        """Test cache miss for non-existent audio."""
        text = "Non-existent text"
        result = self.cache.get_cached_audio(text, self.voice_config)
        
        assert result is None
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        text = "Test text for clearing"
        
        # Cache some audio
        self.cache.cache_audio(text, self.voice_config, self.audio_result)
        
        # Verify it's cached
        assert self.cache.get_cached_audio(text, self.voice_config) is not None
        
        # Clear cache
        self.cache.clear_cache()
        
        # Verify it's gone
        assert self.cache.get_cached_audio(text, self.voice_config) is None
    
    def test_cache_stats(self):
        """Test getting cache statistics."""
        # Cache some audio
        self.cache.cache_audio("test", self.voice_config, self.audio_result)
        
        stats = self.cache.get_cache_stats()
        
        assert 'total_cached_items' in stats
        assert 'total_files' in stats
        assert 'total_size_bytes' in stats
        assert stats['total_cached_items'] >= 1


class TestPollyTTSClient:
    """Test Polly TTS client functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.voice_config = VoiceConfig()
    
    @patch('mcp_tools.text_to_speech_tool.boto3')
    def test_client_initialization_success(self, mock_boto3):
        """Test successful client initialization."""
        mock_client = Mock()
        mock_client.describe_voices.return_value = {'Voices': []}
        mock_boto3.client.return_value = mock_client
        
        client = PollyTTSClient()
        
        assert client._client is not None
        mock_boto3.client.assert_called_once_with('polly', region_name='us-east-1')
        mock_client.describe_voices.assert_called_once()
    
    @patch('mcp_tools.text_to_speech_tool.boto3')
    def test_client_initialization_no_credentials(self, mock_boto3):
        """Test client initialization with no credentials."""
        # Mock NoCredentialsError since we can't import it without boto3
        class MockNoCredentialsError(Exception):
            pass
        
        mock_boto3.client.side_effect = MockNoCredentialsError()
        
        # Patch the exception in the module
        with patch('mcp_tools.text_to_speech_tool.NoCredentialsError', MockNoCredentialsError):
            with pytest.raises(MockNoCredentialsError):
                PollyTTSClient()
    
    @patch('mcp_tools.text_to_speech_tool.boto3')
    @pytest.mark.asyncio
    async def test_synthesize_speech_success(self, mock_boto3):
        """Test successful speech synthesis."""
        # Mock Polly client
        mock_client = Mock()
        mock_client.describe_voices.return_value = {'Voices': []}
        
        # Mock synthesis response
        mock_audio_stream = Mock()
        mock_audio_stream.read.return_value = b"fake_mp3_audio_data"
        mock_client.synthesize_speech.return_value = {
            'AudioStream': mock_audio_stream
        }
        
        mock_boto3.client.return_value = mock_client
        
        # Create client and test synthesis
        client = PollyTTSClient()
        result = await client.synthesize_speech("Test text", self.voice_config)
        
        assert isinstance(result, AudioResult)
        assert result.audio_data == b"fake_mp3_audio_data"
        assert result.format == AudioFormat.MP3
        assert result.voice_config == self.voice_config
        
        # Verify Polly was called with correct parameters
        mock_client.synthesize_speech.assert_called_once()
        call_args = mock_client.synthesize_speech.call_args[1]
        assert call_args['VoiceId'] == 'Matthew'
        assert call_args['Engine'] == 'neural'
        assert call_args['TextType'] == 'ssml'
    
    @patch('mcp_tools.text_to_speech_tool.boto3')
    @pytest.mark.asyncio
    async def test_synthesize_speech_with_plain_text(self, mock_boto3):
        """Test speech synthesis with plain text (no SSML)."""
        # Mock Polly client
        mock_client = Mock()
        mock_client.describe_voices.return_value = {'Voices': []}
        mock_audio_stream = Mock()
        mock_audio_stream.read.return_value = b"fake_audio"
        mock_client.synthesize_speech.return_value = {'AudioStream': mock_audio_stream}
        mock_boto3.client.return_value = mock_client
        
        client = PollyTTSClient()
        result = await client.synthesize_speech("Test text", self.voice_config, use_ssml=False)
        
        # Verify plain text was used
        call_args = mock_client.synthesize_speech.call_args[1]
        assert call_args['TextType'] == 'text'
        assert call_args['Text'] == 'Test text'
    
    @patch('mcp_tools.text_to_speech_tool.boto3')
    def test_get_available_voices(self, mock_boto3):
        """Test getting available voices."""
        mock_client = Mock()
        mock_client.describe_voices.return_value = {
            'Voices': [
                {'Id': 'Matthew', 'LanguageCode': 'en-US'},
                {'Id': 'Joanna', 'LanguageCode': 'en-US'}
            ]
        }
        mock_boto3.client.return_value = mock_client
        
        client = PollyTTSClient()
        voices = client.get_available_voices()
        
        assert len(voices) == 2
        assert voices[0]['Id'] == 'Matthew'
        assert voices[1]['Id'] == 'Joanna'
    
    @patch('mcp_tools.text_to_speech_tool.boto3')
    def test_connection_test_success(self, mock_boto3):
        """Test successful connection test."""
        mock_client = Mock()
        mock_client.describe_voices.return_value = {'Voices': []}
        mock_boto3.client.return_value = mock_client
        
        client = PollyTTSClient()
        result = client.test_connection()
        
        assert result is True
    
    @patch('mcp_tools.text_to_speech_tool.boto3')
    def test_connection_test_failure(self, mock_boto3):
        """Test connection test failure."""
        mock_client = Mock()
        mock_client.describe_voices.side_effect = Exception("Connection failed")
        mock_boto3.client.return_value = mock_client
        
        client = PollyTTSClient()
        result = client.test_connection()
        
        assert result is False


class TestTextToSpeechTool:
    """Test the main TextToSpeechTool class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('mcp_tools.text_to_speech_tool.PollyTTSClient')
    @pytest.mark.asyncio
    async def test_synthesize_speech_success(self, mock_polly_client_class):
        """Test successful speech synthesis through the tool."""
        # Mock the Polly client
        mock_client = Mock()
        mock_audio_result = AudioResult(
            audio_data=b"test_audio_data",
            format=AudioFormat.MP3,
            duration_ms=2000,
            voice_config=VoiceConfig(),
            text_source="test text"
        )
        mock_client.synthesize_speech = AsyncMock(return_value=mock_audio_result)
        mock_polly_client_class.return_value = mock_client
        
        # Create tool
        tool = TextToSpeechTool(cache_dir=self.temp_dir)
        
        # Test synthesis
        result = await tool.synthesize_speech("Test text for synthesis")
        
        assert result['success'] is True
        assert 'audio_data' in result
        assert result['cached'] is False
        assert result['ssml_used'] is True
        
        # Verify audio data is base64 encoded
        audio_data = base64.b64decode(result['audio_data'])
        assert audio_data == b"test_audio_data"
    
    @patch('mcp_tools.text_to_speech_tool.PollyTTSClient')
    @pytest.mark.asyncio
    async def test_synthesize_speech_with_caching(self, mock_polly_client_class):
        """Test speech synthesis with caching."""
        # Mock the Polly client
        mock_client = Mock()
        mock_audio_result = AudioResult(
            audio_data=b"cached_audio_data",
            format=AudioFormat.MP3,
            duration_ms=1500,
            voice_config=VoiceConfig(),
            text_source="cached text"
        )
        mock_client.synthesize_speech = AsyncMock(return_value=mock_audio_result)
        mock_polly_client_class.return_value = mock_client
        
        tool = TextToSpeechTool(cache_dir=self.temp_dir)
        
        # First call - should synthesize and cache
        result1 = await tool.synthesize_speech("Cached text")
        assert result1['success'] is True
        assert result1['cached'] is False
        
        # Second call - should use cache
        result2 = await tool.synthesize_speech("Cached text")
        assert result2['success'] is True
        assert result2['cached'] is True
        
        # Verify Polly was only called once
        assert mock_client.synthesize_speech.call_count == 1
    
    @patch('mcp_tools.text_to_speech_tool.PollyTTSClient')
    @pytest.mark.asyncio
    async def test_synthesize_speech_empty_text(self, mock_polly_client_class):
        """Test synthesis with empty text."""
        mock_polly_client_class.return_value = Mock()
        
        tool = TextToSpeechTool(cache_dir=self.temp_dir)
        
        result = await tool.synthesize_speech("")
        
        assert result['success'] is False
        assert 'error' in result
        assert "empty" in result['error'].lower()
    
    @patch('mcp_tools.text_to_speech_tool.PollyTTSClient')
    @pytest.mark.asyncio
    async def test_get_voice_config(self, mock_polly_client_class):
        """Test getting voice configuration."""
        mock_polly_client_class.return_value = Mock()
        
        tool = TextToSpeechTool(cache_dir=self.temp_dir)
        
        result = await tool.get_voice_config()
        
        assert result['success'] is True
        assert 'voice_config' in result
        assert result['voice_config']['voice_id'] == 'Matthew'
        assert result['voice_config']['speed'] == 1.1
        assert result['voice_config']['engine'] == 'neural'
    
    @patch('mcp_tools.text_to_speech_tool.PollyTTSClient')
    @pytest.mark.asyncio
    async def test_update_voice_config(self, mock_polly_client_class):
        """Test updating voice configuration."""
        mock_polly_client_class.return_value = Mock()
        
        tool = TextToSpeechTool(cache_dir=self.temp_dir)
        
        new_config = {
            'voice_id': 'Brian',
            'speed': 1.2,
            'pitch': '-5%',
            'volume': 0.8,
            'engine': 'neural'
        }
        
        result = await tool.update_voice_config(new_config)
        
        assert result['success'] is True
        assert result['new_config']['voice_id'] == 'Brian'
        assert result['new_config']['speed'] == 1.2
        
        # Verify the config was actually updated
        config_result = await tool.get_voice_config()
        assert config_result['voice_config']['voice_id'] == 'Brian'
    
    @patch('mcp_tools.text_to_speech_tool.PollyTTSClient')
    @pytest.mark.asyncio
    async def test_update_voice_config_invalid(self, mock_polly_client_class):
        """Test updating voice configuration with invalid values."""
        mock_polly_client_class.return_value = Mock()
        
        tool = TextToSpeechTool(cache_dir=self.temp_dir)
        
        invalid_config = {
            'voice_id': '',  # Empty voice_id should be invalid
            'speed': 5.0,    # Speed too high
            'engine': 'invalid_engine'
        }
        
        result = await tool.update_voice_config(invalid_config)
        
        assert result['success'] is False
        assert 'error' in result
    
    @patch('mcp_tools.text_to_speech_tool.PollyTTSClient')
    @pytest.mark.asyncio
    async def test_get_available_voices(self, mock_polly_client_class):
        """Test getting available voices."""
        mock_client = Mock()
        mock_client.get_available_voices.return_value = [
            {'Id': 'Matthew', 'LanguageCode': 'en-US', 'Gender': 'Male'},
            {'Id': 'Joanna', 'LanguageCode': 'en-US', 'Gender': 'Female'},
            {'Id': 'Brian', 'LanguageCode': 'en-GB', 'Gender': 'Male'},
            {'Id': 'Celine', 'LanguageCode': 'fr-FR', 'Gender': 'Female'}
        ]
        mock_polly_client_class.return_value = mock_client
        
        tool = TextToSpeechTool(cache_dir=self.temp_dir)
        
        result = await tool.get_available_voices()
        
        assert result['success'] is True
        assert result['total_voices'] == 4
        assert result['english_voices'] == 3  # Matthew, Joanna, Brian
        assert len(result['recommended_voices']) >= 1  # Should include Matthew
    
    @patch('mcp_tools.text_to_speech_tool.PollyTTSClient')
    @pytest.mark.asyncio
    async def test_test_tts_connection_success(self, mock_polly_client_class):
        """Test TTS connection test success."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        
        # Mock synthesis for the test
        mock_audio_result = AudioResult(
            audio_data=b"test_audio",
            format=AudioFormat.MP3,
            duration_ms=1000,
            voice_config=VoiceConfig()
        )
        mock_client.synthesize_speech = AsyncMock(return_value=mock_audio_result)
        mock_polly_client_class.return_value = mock_client
        
        tool = TextToSpeechTool(cache_dir=self.temp_dir)
        
        result = await tool.test_tts_connection()
        
        assert result['success'] is True
        assert result['connection_status'] == 'connected'
        assert result['synthesis_test'] == 'passed'
    
    @patch('mcp_tools.text_to_speech_tool.PollyTTSClient')
    @pytest.mark.asyncio
    async def test_test_tts_connection_failure(self, mock_polly_client_class):
        """Test TTS connection test failure."""
        mock_client = Mock()
        mock_client.test_connection.return_value = False
        mock_polly_client_class.return_value = mock_client
        
        tool = TextToSpeechTool(cache_dir=self.temp_dir)
        
        result = await tool.test_tts_connection()
        
        assert result['success'] is False
        assert result['connection_status'] == 'failed'
        assert result['synthesis_test'] == 'not_attempted'
    
    @patch('mcp_tools.text_to_speech_tool.PollyTTSClient')
    @pytest.mark.asyncio
    async def test_cache_operations(self, mock_polly_client_class):
        """Test cache statistics and clearing."""
        mock_polly_client_class.return_value = Mock()
        
        tool = TextToSpeechTool(cache_dir=self.temp_dir)
        
        # Test getting cache stats
        stats_result = await tool.get_cache_stats()
        assert stats_result['success'] is True
        assert 'cache_stats' in stats_result
        
        # Test clearing cache
        clear_result = await tool.clear_audio_cache()
        assert clear_result['success'] is True
        assert 'message' in clear_result


class TestVoiceConfig:
    """Test VoiceConfig model validation."""
    
    def test_valid_voice_config(self):
        """Test creating valid voice configuration."""
        config = VoiceConfig(
            voice_id="Matthew",
            speed=1.1,
            pitch="-10%",
            volume=0.8,
            engine="neural"
        )
        
        assert config.voice_id == "Matthew"
        assert config.speed == 1.1
        assert config.pitch == "-10%"
        assert config.volume == 0.8
        assert config.engine == "neural"
    
    def test_invalid_voice_config(self):
        """Test validation of invalid voice configuration."""
        # Empty voice_id
        with pytest.raises(ValueError, match="voice_id cannot be empty"):
            VoiceConfig(voice_id="")
        
        # Invalid speed
        with pytest.raises(ValueError, match="speed must be between"):
            VoiceConfig(speed=5.0)
        
        # Invalid volume
        with pytest.raises(ValueError, match="volume must be between"):
            VoiceConfig(volume=2.0)
        
        # Invalid engine
        with pytest.raises(ValueError, match="engine must be"):
            VoiceConfig(engine="invalid")
    
    def test_to_polly_params(self):
        """Test conversion to Polly parameters."""
        config = VoiceConfig(voice_id="Brian", engine="standard")
        params = config.to_polly_params()
        
        assert params['VoiceId'] == 'Brian'
        assert params['Engine'] == 'standard'
        assert params['OutputFormat'] == 'mp3'
    
    def test_to_ssml_prosody(self):
        """Test SSML prosody generation."""
        config = VoiceConfig(speed=1.2, pitch="-5%")
        ssml = config.to_ssml_prosody("Test text")
        
        assert 'rate="1.2"' in ssml
        assert 'pitch="-5%"' in ssml
        assert 'Test text' in ssml


if __name__ == "__main__":
    pytest.main([__file__])