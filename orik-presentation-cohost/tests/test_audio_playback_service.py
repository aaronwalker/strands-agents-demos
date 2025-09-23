"""Unit tests for AudioPlaybackService and related audio functionality."""

import pytest
from unittest.mock import Mock

from src.services.audio_playback_service import AudioDevice
from src.models.audio_models import AudioResult, VoiceConfig
from src.models.enums import AudioFormat, PlaybackStatus


class TestAudioDevice:
    """Test AudioDevice class."""
    
    def test_audio_device_creation(self):
        """Test AudioDevice creation and properties."""
        device = AudioDevice(device_id=1, name="Test Device", max_channels=2)
        
        assert device.device_id == 1
        assert device.name == "Test Device"
        assert device.max_channels == 2
    
    def test_audio_device_str(self):
        """Test AudioDevice string representation."""
        device = AudioDevice(device_id=1, name="Test Device", max_channels=2)
        expected = "AudioDevice(id=1, name='Test Device', channels=2)"
        assert str(device) == expected
    
    def test_audio_device_to_dict(self):
        """Test AudioDevice dictionary conversion."""
        device = AudioDevice(device_id=1, name="Test Device", max_channels=2)
        expected = {
            'device_id': 1,
            'name': 'Test Device',
            'max_channels': 2
        }
        assert device.to_dict() == expected


class TestAudioPlaybackServiceCore:
    """Test core AudioPlaybackService functionality."""
    
    @pytest.fixture
    def mock_audio_result(self):
        """Create a mock AudioResult for testing."""
        voice_config = VoiceConfig(voice_id="Matthew", speed=1.1)
        return AudioResult(
            audio_data=b"fake_audio_data",
            format=AudioFormat.MP3,
            duration_ms=2000,
            voice_config=voice_config,
            text_source="Test audio"
        )
    
    def test_backend_selection_logic(self):
        """Test backend selection logic."""
        from unittest.mock import patch
        from src.services.audio_playback_service import AudioPlaybackService
        
        # Create service instance without initialization
        service = AudioPlaybackService.__new__(AudioPlaybackService)
        
        # Test pygame selection when available
        with patch('src.services.audio_playback_service.PYGAME_AVAILABLE', True):
            result = service._select_backend("pygame")
            assert result == "pygame"
        
        # Test pyaudio selection when available
        with patch('src.services.audio_playback_service.PYAUDIO_AVAILABLE', True):
            result = service._select_backend("pyaudio")
            assert result == "pyaudio"
        
        # Test auto selection with pygame preference
        with patch('src.services.audio_playback_service.PYGAME_AVAILABLE', True):
            with patch('src.services.audio_playback_service.PYAUDIO_AVAILABLE', True):
                result = service._select_backend("auto")
                assert result == "pygame"
        
        # Test auto selection with pyaudio fallback
        with patch('src.services.audio_playback_service.PYGAME_AVAILABLE', False):
            with patch('src.services.audio_playback_service.PYAUDIO_AVAILABLE', True):
                result = service._select_backend("auto")
                assert result == "pyaudio"
        
        # Test no backend available
        with patch('src.services.audio_playback_service.PYGAME_AVAILABLE', False):
            with patch('src.services.audio_playback_service.PYAUDIO_AVAILABLE', False):
                with pytest.raises(RuntimeError, match="No audio backend available"):
                    service._select_backend("auto")
        
        # Test invalid backend
        with pytest.raises(ValueError, match="Backend 'invalid' not available"):
            service._select_backend("invalid")
    
    def test_no_backend_available_error(self):
        """Test error when no backend is available."""
        # This test verifies the error handling logic
        from src.services.audio_playback_service import AudioPlaybackService
        
        with pytest.raises(ValueError, match="Backend 'nonexistent' not available"):
            AudioPlaybackService(backend="nonexistent")
    
    def test_audio_result_properties(self, mock_audio_result):
        """Test AudioResult properties and methods."""
        assert mock_audio_result.duration_seconds == 2.0
        assert mock_audio_result.size_bytes == len(b"fake_audio_data")
        
        result_dict = mock_audio_result.to_dict()
        assert result_dict['format'] == 'mp3'
        assert result_dict['duration_ms'] == 2000
        assert result_dict['duration_seconds'] == 2.0
        assert result_dict['text_source'] == 'Test audio'
    
    def test_voice_config_validation(self):
        """Test VoiceConfig validation."""
        # Valid config
        config = VoiceConfig(voice_id="Matthew", speed=1.1, pitch="-10%", volume=0.8)
        assert config.voice_id == "Matthew"
        assert config.speed == 1.1
        assert config.pitch == "-10%"
        assert config.volume == 0.8
        
        # Invalid voice_id
        with pytest.raises(ValueError, match="voice_id cannot be empty"):
            VoiceConfig(voice_id="")
        
        # Invalid speed
        with pytest.raises(ValueError, match="speed must be between 0.5 and 2.0"):
            VoiceConfig(voice_id="Matthew", speed=3.0)
        
        # Invalid volume
        with pytest.raises(ValueError, match="volume must be between 0.0 and 1.0"):
            VoiceConfig(voice_id="Matthew", volume=1.5)
        
        # Invalid engine
        with pytest.raises(ValueError, match="engine must be 'standard' or 'neural'"):
            VoiceConfig(voice_id="Matthew", engine="invalid")
    
    def test_voice_config_polly_params(self):
        """Test VoiceConfig Polly parameter conversion."""
        config = VoiceConfig(voice_id="Matthew", engine="neural")
        params = config.to_polly_params()
        
        expected = {
            'VoiceId': 'Matthew',
            'Engine': 'neural',
            'OutputFormat': 'mp3'
        }
        assert params == expected
    
    def test_voice_config_ssml_prosody(self):
        """Test VoiceConfig SSML prosody generation."""
        config = VoiceConfig(voice_id="Matthew", speed=1.2, pitch="-5%")
        ssml = config.to_ssml_prosody("Hello world")
        
        expected = '<prosody rate="1.2" pitch="-5%">Hello world</prosody>'
        assert ssml == expected
    
    def test_audio_result_validation(self):
        """Test AudioResult validation."""
        voice_config = VoiceConfig(voice_id="Matthew")
        
        # Valid result
        result = AudioResult(
            audio_data=b"data",
            format=AudioFormat.MP3,
            duration_ms=1000,
            voice_config=voice_config
        )
        assert result.audio_data == b"data"
        
        # Invalid audio_data
        with pytest.raises(ValueError, match="audio_data cannot be empty"):
            AudioResult(
                audio_data=b"",
                format=AudioFormat.MP3,
                duration_ms=1000,
                voice_config=voice_config
            )
        
        # Invalid duration
        with pytest.raises(ValueError, match="duration_ms must be non-negative"):
            AudioResult(
                audio_data=b"data",
                format=AudioFormat.MP3,
                duration_ms=-1,
                voice_config=voice_config
            )
        
        # Invalid format type
        with pytest.raises(ValueError, match="format must be an AudioFormat enum"):
            AudioResult(
                audio_data=b"data",
                format="mp3",  # Should be AudioFormat.MP3
                duration_ms=1000,
                voice_config=voice_config
            )
        
        # Invalid voice_config type
        with pytest.raises(ValueError, match="voice_config must be a VoiceConfig instance"):
            AudioResult(
                audio_data=b"data",
                format=AudioFormat.MP3,
                duration_ms=1000,
                voice_config="invalid"  # Should be VoiceConfig instance
            )


class TestPlaybackStatus:
    """Test PlaybackStatus enum functionality."""
    
    def test_playback_status_values(self):
        """Test PlaybackStatus enum values."""
        assert PlaybackStatus.IDLE.value == "idle"
        assert PlaybackStatus.PLAYING.value == "playing"
        assert PlaybackStatus.PAUSED.value == "paused"
        assert PlaybackStatus.ERROR.value == "error"
    
    def test_audio_format_values(self):
        """Test AudioFormat enum values."""
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.OGG.value == "ogg"


class TestAudioPlaybackServiceMethods:
    """Test AudioPlaybackService methods that don't require backends."""
    
    def test_volume_validation_logic(self):
        """Test volume validation logic without backend initialization."""
        from src.services.audio_playback_service import AudioPlaybackService
        
        # Create a minimal service instance
        service = AudioPlaybackService.__new__(AudioPlaybackService)
        service.volume = 1.0
        service.backend = "mock"  # Set a mock backend to avoid pygame calls
        
        # Test valid volume
        service.set_volume(0.5)
        assert service.volume == 0.5
        
        # Test invalid volumes
        with pytest.raises(ValueError, match="Volume must be between 0.0 and 1.0"):
            service.set_volume(1.5)
        
        with pytest.raises(ValueError, match="Volume must be between 0.0 and 1.0"):
            service.set_volume(-0.1)
        
        # Test get_volume
        assert service.get_volume() == 0.5
    
    def test_status_tracking(self):
        """Test status tracking methods."""
        from src.services.audio_playback_service import AudioPlaybackService
        from queue import Queue
        
        service = AudioPlaybackService.__new__(AudioPlaybackService)
        service.status = PlaybackStatus.IDLE
        service.current_audio = None
        service.audio_queue = Queue()
        
        # Test initial state
        assert service.get_playback_status() == PlaybackStatus.IDLE
        assert service.is_idle() is True
        assert service.is_playing() is False
        assert service.get_current_audio() is None
        assert service.get_queue_size() == 0
        
        # Test playing state
        service.status = PlaybackStatus.PLAYING
        mock_audio = Mock()
        service.current_audio = mock_audio
        service.audio_queue.put("test_item")
        
        assert service.get_playback_status() == PlaybackStatus.PLAYING
        assert service.is_idle() is False
        assert service.is_playing() is True
        assert service.get_current_audio() == mock_audio
        assert service.get_queue_size() == 1
    
    @pytest.mark.asyncio
    async def test_play_audio_queuing_logic(self):
        """Test audio queuing logic without backend."""
        from src.services.audio_playback_service import AudioPlaybackService
        from queue import Queue
        
        service = AudioPlaybackService.__new__(AudioPlaybackService)
        service.audio_queue = Queue()
        service.is_processing = False
        service._start_processing_thread = Mock()  # Mock the threading method
        
        # Create mock audio result
        voice_config = VoiceConfig(voice_id="Matthew")
        audio_result = AudioResult(
            audio_data=b"test_data",
            format=AudioFormat.MP3,
            duration_ms=1000,
            voice_config=voice_config
        )
        
        # Test queuing
        await service.play_audio(audio_result)
        
        assert service.audio_queue.qsize() == 1
        service._start_processing_thread.assert_called_once()
    
    def test_callback_management(self):
        """Test callback assignment and management."""
        from src.services.audio_playback_service import AudioPlaybackService
        
        service = AudioPlaybackService.__new__(AudioPlaybackService)
        
        # Test callback assignment
        on_started = Mock()
        on_finished = Mock()
        on_error = Mock()
        
        service.on_playback_started = on_started
        service.on_playback_finished = on_finished
        service.on_playback_error = on_error
        
        assert service.on_playback_started == on_started
        assert service.on_playback_finished == on_finished
        assert service.on_playback_error == on_error