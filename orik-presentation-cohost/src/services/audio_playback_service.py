"""Audio playback service for the Orik Presentation Co-host system."""

import asyncio
import io
import logging
import threading
from queue import Queue, Empty
from typing import Optional, List, Callable, Dict, Any
import time

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

from ..models.audio_models import AudioResult, VoiceConfig
from ..models.enums import PlaybackStatus, AudioFormat


logger = logging.getLogger(__name__)


class AudioDevice:
    """Represents an audio output device."""
    
    def __init__(self, device_id: int, name: str, max_channels: int = 2):
        self.device_id = device_id
        self.name = name
        self.max_channels = max_channels
    
    def __str__(self) -> str:
        return f"AudioDevice(id={self.device_id}, name='{self.name}', channels={self.max_channels})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'device_id': self.device_id,
            'name': self.name,
            'max_channels': self.max_channels
        }


class AudioPlaybackService:
    """Cross-platform audio playback service with queue management."""
    
    def __init__(self, device_id: Optional[int] = None, backend: str = "auto"):
        """
        Initialize the audio playback service.
        
        Args:
            device_id: Specific audio device ID to use (None for default)
            backend: Audio backend to use ("pygame", "pyaudio", or "auto")
        """
        self.device_id = device_id
        self.backend = self._select_backend(backend)
        self.volume = 1.0
        self.status = PlaybackStatus.IDLE
        
        # Audio queue for sequential playback
        self.audio_queue: Queue[AudioResult] = Queue()
        self.is_processing = False
        self.current_audio: Optional[AudioResult] = None
        
        # Threading for async playback
        self.playback_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Callbacks
        self.on_playback_started: Optional[Callable[[AudioResult], None]] = None
        self.on_playback_finished: Optional[Callable[[AudioResult], None]] = None
        self.on_playback_error: Optional[Callable[[Exception], None]] = None
        
        # Initialize backend
        self._initialize_backend()
        
        logger.info(f"AudioPlaybackService initialized with backend: {self.backend}")
    
    def _select_backend(self, backend: str) -> str:
        """Select the best available audio backend."""
        if backend == "pygame" and PYGAME_AVAILABLE:
            return "pygame"
        elif backend == "pyaudio" and PYAUDIO_AVAILABLE:
            return "pyaudio"
        elif backend == "auto":
            if PYGAME_AVAILABLE:
                return "pygame"
            elif PYAUDIO_AVAILABLE:
                return "pyaudio"
            else:
                raise RuntimeError("No audio backend available. Install pygame or pyaudio.")
        else:
            raise ValueError(f"Backend '{backend}' not available or not supported")
    
    def _initialize_backend(self) -> None:
        """Initialize the selected audio backend."""
        try:
            if self.backend == "pygame":
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                logger.info("Pygame audio backend initialized")
            elif self.backend == "pyaudio":
                self.pyaudio_instance = pyaudio.PyAudio()
                logger.info("PyAudio backend initialized")
        except Exception as e:
            logger.error(f"Failed to initialize {self.backend} backend: {e}")
            raise
    
    def get_available_devices(self) -> List[AudioDevice]:
        """Get list of available audio output devices."""
        devices = []
        
        if self.backend == "pyaudio" and hasattr(self, 'pyaudio_instance'):
            try:
                for i in range(self.pyaudio_instance.get_device_count()):
                    device_info = self.pyaudio_instance.get_device_info_by_index(i)
                    if device_info['maxOutputChannels'] > 0:
                        devices.append(AudioDevice(
                            device_id=i,
                            name=device_info['name'],
                            max_channels=device_info['maxOutputChannels']
                        ))
            except Exception as e:
                logger.warning(f"Failed to enumerate audio devices: {e}")
        else:
            # For pygame, we can't enumerate devices easily, so return default
            devices.append(AudioDevice(device_id=0, name="Default Audio Device"))
        
        return devices
    
    def set_device(self, device_id: int) -> bool:
        """
        Set the audio output device.
        
        Args:
            device_id: ID of the device to use
            
        Returns:
            True if device was set successfully, False otherwise
        """
        try:
            # Stop current playback
            self.stop_playback()
            
            # Update device ID
            old_device_id = self.device_id
            self.device_id = device_id
            
            # For pygame, we need to reinitialize
            if self.backend == "pygame":
                pygame.mixer.quit()
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
            
            logger.info(f"Audio device changed from {old_device_id} to {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set audio device {device_id}: {e}")
            self.device_id = old_device_id  # Restore previous device
            return False
    
    def set_volume(self, volume: float) -> None:
        """
        Set the playback volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        if not 0.0 <= volume <= 1.0:
            raise ValueError("Volume must be between 0.0 and 1.0")
        
        self.volume = volume
        
        # Apply volume to current playback if active
        if self.backend == "pygame" and pygame.mixer.get_init():
            pygame.mixer.music.set_volume(volume)
        
        logger.debug(f"Volume set to {volume}")
    
    def get_volume(self) -> float:
        """Get current volume level."""
        return self.volume
    
    async def play_audio(self, audio_result: AudioResult) -> None:
        """
        Queue audio for playback.
        
        Args:
            audio_result: Audio data to play
        """
        logger.debug(f"Queuing audio: {audio_result.format.value}, {audio_result.duration_ms}ms")
        self.audio_queue.put(audio_result)
        
        # Start processing thread if not already running
        if not self.is_processing:
            self._start_processing_thread()
    
    def _start_processing_thread(self) -> None:
        """Start the audio processing thread."""
        if self.playback_thread and self.playback_thread.is_alive():
            return
        
        self.is_processing = True
        self.stop_event.clear()
        self.playback_thread = threading.Thread(target=self._process_audio_queue, daemon=True)
        self.playback_thread.start()
        logger.debug("Audio processing thread started")
    
    def _process_audio_queue(self) -> None:
        """Process audio queue in background thread."""
        while self.is_processing and not self.stop_event.is_set():
            try:
                # Get next audio with timeout
                audio_result = self.audio_queue.get(timeout=1.0)
                
                # Play the audio
                self._play_audio_sync(audio_result)
                
                # Mark task as done
                self.audio_queue.task_done()
                
            except Empty:
                # No audio in queue, continue checking
                continue
            except Exception as e:
                logger.error(f"Error processing audio queue: {e}")
                if self.on_playback_error:
                    self.on_playback_error(e)
        
        logger.debug("Audio processing thread stopped")
    
    def _play_audio_sync(self, audio_result: AudioResult) -> None:
        """
        Play audio synchronously in the background thread.
        
        Args:
            audio_result: Audio data to play
        """
        try:
            self.current_audio = audio_result
            self.status = PlaybackStatus.PLAYING
            
            # Notify playback started
            if self.on_playback_started:
                self.on_playback_started(audio_result)
            
            logger.debug(f"Starting playback: {audio_result.format.value}")
            
            if self.backend == "pygame":
                self._play_with_pygame(audio_result)
            elif self.backend == "pyaudio":
                self._play_with_pyaudio(audio_result)
            
            # Wait for playback to complete
            self._wait_for_completion(audio_result)
            
            self.status = PlaybackStatus.IDLE
            self.current_audio = None
            
            # Notify playback finished
            if self.on_playback_finished:
                self.on_playback_finished(audio_result)
            
            logger.debug("Playback completed")
            
        except Exception as e:
            self.status = PlaybackStatus.ERROR
            self.current_audio = None
            logger.error(f"Playback error: {e}")
            if self.on_playback_error:
                self.on_playback_error(e)
    
    def _play_with_pygame(self, audio_result: AudioResult) -> None:
        """Play audio using pygame backend."""
        # Create a BytesIO object from audio data
        audio_file = io.BytesIO(audio_result.audio_data)
        
        # Load and play the audio
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.play()
    
    def _play_with_pyaudio(self, audio_result: AudioResult) -> None:
        """Play audio using pyaudio backend."""
        # For pyaudio, we need to decode the audio first
        # This is a simplified implementation - in practice, you'd want
        # to use a library like pydub to handle different formats
        
        if audio_result.format != AudioFormat.WAV:
            logger.warning(f"PyAudio backend may not support {audio_result.format.value} format directly")
        
        # Basic WAV playback (simplified)
        chunk_size = 1024
        
        try:
            # Open audio stream
            stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=2,
                rate=22050,
                output=True,
                output_device_index=self.device_id
            )
            
            # Play audio data in chunks
            audio_io = io.BytesIO(audio_result.audio_data)
            
            # Skip WAV header if present (simplified detection)
            if audio_result.audio_data.startswith(b'RIFF'):
                audio_io.seek(44)  # Skip standard WAV header
            
            while True:
                chunk = audio_io.read(chunk_size)
                if not chunk:
                    break
                stream.write(chunk)
            
            # Clean up
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            logger.error(f"PyAudio playback error: {e}")
            raise
    
    def _wait_for_completion(self, audio_result: AudioResult) -> None:
        """Wait for audio playback to complete."""
        if self.backend == "pygame":
            # Wait for pygame to finish playing
            while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
                time.sleep(0.1)
        else:
            # For other backends, wait based on duration
            duration_seconds = audio_result.duration_ms / 1000.0
            self.stop_event.wait(duration_seconds)
    
    def stop_playback(self) -> None:
        """Stop current playback and clear queue."""
        logger.debug("Stopping audio playback")
        
        # Signal stop
        self.stop_event.set()
        
        # Stop backend-specific playback
        if self.backend == "pygame" and pygame.mixer.get_init():
            pygame.mixer.music.stop()
        
        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except Empty:
                break
        
        self.status = PlaybackStatus.IDLE
        self.current_audio = None
    
    def pause_playback(self) -> bool:
        """
        Pause current playback.
        
        Returns:
            True if paused successfully, False if not supported or no audio playing
        """
        if self.status != PlaybackStatus.PLAYING:
            return False
        
        try:
            if self.backend == "pygame" and pygame.mixer.get_init():
                pygame.mixer.music.pause()
                self.status = PlaybackStatus.PAUSED
                logger.debug("Playback paused")
                return True
        except Exception as e:
            logger.error(f"Failed to pause playback: {e}")
        
        return False
    
    def resume_playback(self) -> bool:
        """
        Resume paused playback.
        
        Returns:
            True if resumed successfully, False if not paused or error
        """
        if self.status != PlaybackStatus.PAUSED:
            return False
        
        try:
            if self.backend == "pygame" and pygame.mixer.get_init():
                pygame.mixer.music.unpause()
                self.status = PlaybackStatus.PLAYING
                logger.debug("Playback resumed")
                return True
        except Exception as e:
            logger.error(f"Failed to resume playback: {e}")
        
        return False
    
    def get_playback_status(self) -> PlaybackStatus:
        """Get current playback status."""
        return self.status
    
    def get_current_audio(self) -> Optional[AudioResult]:
        """Get currently playing audio result."""
        return self.current_audio
    
    def get_queue_size(self) -> int:
        """Get number of items in the audio queue."""
        return self.audio_queue.qsize()
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self.status == PlaybackStatus.PLAYING
    
    def is_idle(self) -> bool:
        """Check if service is idle (not playing or queued)."""
        return self.status == PlaybackStatus.IDLE and self.audio_queue.empty()
    
    def shutdown(self) -> None:
        """Shutdown the audio service and clean up resources."""
        logger.info("Shutting down AudioPlaybackService")
        
        # Stop playback
        self.stop_playback()
        
        # Stop processing thread
        self.is_processing = False
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=2.0)
        
        # Clean up backend resources
        try:
            if self.backend == "pygame" and pygame.mixer.get_init():
                pygame.mixer.quit()
            elif self.backend == "pyaudio" and hasattr(self, 'pyaudio_instance'):
                self.pyaudio_instance.terminate()
        except Exception as e:
            logger.error(f"Error during audio backend cleanup: {e}")
        
        logger.info("AudioPlaybackService shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()