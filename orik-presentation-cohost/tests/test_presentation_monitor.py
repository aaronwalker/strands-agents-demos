"""Unit tests for PresentationMonitor service."""

import asyncio
import pytest
import threading
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.services.presentation_monitor import (
    PresentationMonitor,
    PowerPointMacMonitor
)
from src.models.slide_data import SlideData, SlideInfo, SlideEvent
from src.models.enums import PresentationSoftware


class TestSlideEvent:
    """Test SlideEvent data class."""
    
    def test_slide_event_creation(self):
        """Test creating a slide event."""
        slide_data = SlideData(
            slide_index=0,
            slide_title="Test Slide",
            speaker_notes="Test notes",
            presentation_path="/test/path.pptx",
            timestamp=datetime.now()
        )
        
        event = SlideEvent(
            event_type="slide_changed",
            slide_data=slide_data
        )
        
        assert event.event_type == "slide_changed"
        assert event.slide_data == slide_data
        assert isinstance(event.timestamp, datetime)
    
    def test_slide_event_auto_timestamp(self):
        """Test that timestamp is automatically set."""
        event = SlideEvent(event_type="presentation_started")
        
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)


class TestSlideInfo:
    """Test SlideInfo data class."""
    
    def test_slide_info_creation(self):
        """Test creating slide info."""
        info = SlideInfo(
            slide_index=2,
            slide_title="Test Slide",
            total_slides=10,
            is_slideshow_mode=True
        )
        
        assert info.slide_index == 2
        assert info.slide_title == "Test Slide"
        assert info.total_slides == 10
        assert info.is_slideshow_mode is True
    
    def test_slide_info_validation(self):
        """Test slide info validation."""
        # Test negative slide index
        with pytest.raises(ValueError, match="slide_index must be non-negative"):
            SlideInfo(
                slide_index=-1,
                slide_title="Test",
                total_slides=10
            )
        
        # Test negative total slides
        with pytest.raises(ValueError, match="total_slides must be non-negative"):
            SlideInfo(
                slide_index=0,
                slide_title="Test",
                total_slides=-1
            )
    
    def test_slide_info_to_dict(self):
        """Test converting slide info to dictionary."""
        info = SlideInfo(
            slide_index=1,
            slide_title="Test Slide",
            total_slides=5,
            is_slideshow_mode=False
        )
        
        result = info.to_dict()
        
        expected = {
            'slide_index': 1,
            'slide_title': "Test Slide",
            'total_slides': 5,
            'is_slideshow_mode': False
        }
        
        assert result == expected


@pytest.fixture
def mock_applescript():
    """Mock applescript module."""
    with patch('src.services.presentation_monitor.applescript', create=True) as mock:
        # Mock successful result
        mock_result = Mock()
        mock_result.code = 0
        mock_result.out = True
        mock.run.return_value = mock_result
        yield mock


class TestPowerPointMacMonitor:
    """Test PowerPointMacMonitor class."""
    
    def test_init_without_applescript(self):
        """Test initialization without applescript available."""
        with patch('src.services.presentation_monitor.APPLESCRIPT_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="AppleScript not available"):
                PowerPointMacMonitor()
    
    def test_init_with_applescript(self, mock_applescript):
        """Test successful initialization."""
        with patch('src.services.presentation_monitor.APPLESCRIPT_AVAILABLE', True):
            monitor = PowerPointMacMonitor()
            
            assert monitor.is_monitoring is False
            assert monitor.current_slide_index == -1
            assert monitor.presentation_path == ""
            assert monitor.total_slides == 0
    
    def test_is_powerpoint_running_true(self, mock_applescript):
        """Test checking if PowerPoint is running (true case)."""
        with patch('src.services.presentation_monitor.APPLESCRIPT_AVAILABLE', True):
            monitor = PowerPointMacMonitor()
            
            # Mock PowerPoint running
            mock_applescript.run.return_value.out = True
            
            result = monitor.is_powerpoint_running()
            assert result is True
    
    def test_is_powerpoint_running_false(self, mock_applescript):
        """Test checking if PowerPoint is running (false case)."""
        with patch('src.services.presentation_monitor.APPLESCRIPT_AVAILABLE', True):
            monitor = PowerPointMacMonitor()
            
            # Mock PowerPoint not running
            mock_applescript.run.return_value.out = False
            
            result = monitor.is_powerpoint_running()
            assert result is False
    
    def test_is_powerpoint_running_error(self, mock_applescript):
        """Test error handling when checking PowerPoint status."""
        with patch('src.services.presentation_monitor.APPLESCRIPT_AVAILABLE', True):
            monitor = PowerPointMacMonitor()
            
            # Mock error
            mock_applescript.run.side_effect = Exception("AppleScript error")
            
            result = monitor.is_powerpoint_running()
            assert result is False
    
    def test_get_current_slide_info_success(self, mock_applescript):
        """Test getting current slide info successfully."""
        with patch('src.services.presentation_monitor.APPLESCRIPT_AVAILABLE', True):
            monitor = PowerPointMacMonitor()
            
            # Mock PowerPoint running
            monitor.is_powerpoint_running = Mock(return_value=True)
            
            # Mock slide info response: [slide_index, total_slides, title, is_slideshow]
            mock_applescript.run.return_value.out = [3, 10, "Test Slide", True]
            
            result = monitor.get_current_slide_info()
            
            assert result is not None
            assert result.slide_index == 2  # Converted to 0-based
            assert result.slide_title == "Test Slide"
            assert result.total_slides == 10
            assert result.is_slideshow_mode is True
    
    def test_get_current_slide_info_no_powerpoint(self, mock_applescript):
        """Test getting slide info when PowerPoint is not running."""
        with patch('src.services.presentation_monitor.APPLESCRIPT_AVAILABLE', True):
            monitor = PowerPointMacMonitor()
            
            # Mock PowerPoint not running
            monitor.is_powerpoint_running = Mock(return_value=False)
            
            result = monitor.get_current_slide_info()
            assert result is None
    
    def test_get_presentation_path_success(self, mock_applescript):
        """Test getting presentation path successfully."""
        with patch('src.services.presentation_monitor.APPLESCRIPT_AVAILABLE', True):
            monitor = PowerPointMacMonitor()
            
            # Mock PowerPoint running
            monitor.is_powerpoint_running = Mock(return_value=True)
            
            # Mock path response
            mock_applescript.run.return_value.out = "/Users/test/presentation.pptx"
            
            result = monitor.get_presentation_path()
            assert result == "/Users/test/presentation.pptx"
    
    def test_get_speaker_notes_success(self, mock_applescript):
        """Test getting speaker notes successfully."""
        with patch('src.services.presentation_monitor.APPLESCRIPT_AVAILABLE', True):
            monitor = PowerPointMacMonitor()
            
            # Mock PowerPoint running
            monitor.is_powerpoint_running = Mock(return_value=True)
            
            # Mock notes response
            mock_applescript.run.return_value.out = "[Orik] This is a test note"
            
            result = monitor.get_speaker_notes(0)
            assert result == "[Orik] This is a test note"
    
    def test_get_speaker_notes_no_powerpoint(self, mock_applescript):
        """Test getting speaker notes when PowerPoint is not running."""
        with patch('src.services.presentation_monitor.APPLESCRIPT_AVAILABLE', True):
            monitor = PowerPointMacMonitor()
            
            # Mock PowerPoint not running
            monitor.is_powerpoint_running = Mock(return_value=False)
            
            result = monitor.get_speaker_notes(0)
            assert result == ""


class TestPresentationMonitor:
    """Test PresentationMonitor class."""
    
    @pytest.fixture
    def mock_powerpoint_monitor(self):
        """Mock PowerPointMacMonitor."""
        with patch('src.services.presentation_monitor.PowerPointMacMonitor') as mock:
            mock_instance = Mock()
            mock.return_value = mock_instance
            yield mock_instance
    
    def test_init_powerpoint(self, mock_powerpoint_monitor):
        """Test initialization with PowerPoint."""
        monitor = PresentationMonitor(PresentationSoftware.POWERPOINT)
        
        assert monitor.software_type == PresentationSoftware.POWERPOINT
        assert monitor.is_monitoring is False
        assert monitor.poll_interval == 1.0
    
    def test_init_unsupported_software(self):
        """Test initialization with unsupported software."""
        with pytest.raises(NotImplementedError):
            PresentationMonitor(PresentationSoftware.KEYNOTE)
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self, mock_powerpoint_monitor):
        """Test starting monitoring."""
        monitor = PresentationMonitor(PresentationSoftware.POWERPOINT)
        callback = Mock()
        
        await monitor.start_monitoring(callback)
        
        assert monitor.is_monitoring is True
        assert monitor.slide_change_callback == callback
        assert monitor.monitor_thread is not None
        assert monitor.monitor_thread.is_alive()
        
        # Clean up
        await monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_stop_monitoring(self, mock_powerpoint_monitor):
        """Test stopping monitoring."""
        monitor = PresentationMonitor(PresentationSoftware.POWERPOINT)
        callback = Mock()
        
        # Start monitoring first
        await monitor.start_monitoring(callback)
        assert monitor.is_monitoring is True
        
        # Stop monitoring
        await monitor.stop_monitoring()
        
        assert monitor.is_monitoring is False
        assert monitor.stop_event.is_set()
    
    def test_set_poll_interval(self, mock_powerpoint_monitor):
        """Test setting poll interval."""
        monitor = PresentationMonitor(PresentationSoftware.POWERPOINT)
        
        monitor.set_poll_interval(0.5)
        assert monitor.get_poll_interval() == 0.5
        
        # Test invalid interval
        with pytest.raises(ValueError, match="Poll interval must be at least 0.1 seconds"):
            monitor.set_poll_interval(0.05)
    
    def test_is_presentation_active(self, mock_powerpoint_monitor):
        """Test checking if presentation is active."""
        monitor = PresentationMonitor(PresentationSoftware.POWERPOINT)
        
        # Mock PowerPoint running
        mock_powerpoint_monitor.is_powerpoint_running.return_value = True
        
        result = monitor.is_presentation_active()
        assert result is True
        
        # Mock PowerPoint not running
        mock_powerpoint_monitor.is_powerpoint_running.return_value = False
        
        result = monitor.is_presentation_active()
        assert result is False
    
    def test_create_slide_data(self, mock_powerpoint_monitor):
        """Test creating SlideData from SlideInfo."""
        monitor = PresentationMonitor(PresentationSoftware.POWERPOINT)
        
        # Mock speaker notes and presentation path
        mock_powerpoint_monitor.get_speaker_notes.return_value = "[Orik] Test notes"
        mock_powerpoint_monitor.get_presentation_path.return_value = "/test/path.pptx"
        
        slide_info = SlideInfo(
            slide_index=1,
            slide_title="Test Slide",
            total_slides=5,
            is_slideshow_mode=True
        )
        
        result = monitor._create_slide_data(slide_info)
        
        assert isinstance(result, SlideData)
        assert result.slide_index == 1
        assert result.slide_title == "Test Slide"
        assert result.speaker_notes == "[Orik] Test notes"
        assert result.presentation_path == "/test/path.pptx"
        assert isinstance(result.timestamp, datetime)
    
    def test_get_monitoring_status(self, mock_powerpoint_monitor):
        """Test getting monitoring status."""
        monitor = PresentationMonitor(PresentationSoftware.POWERPOINT)
        
        # Mock presentation active
        mock_powerpoint_monitor.is_powerpoint_running.return_value = True
        
        status = monitor.get_monitoring_status()
        
        assert isinstance(status, dict)
        assert 'is_monitoring' in status
        assert 'software_type' in status
        assert 'presentation_active' in status
        assert 'current_slide' in status
        assert 'last_check_time' in status
        assert 'poll_interval' in status
        
        assert status['software_type'] == 'powerpoint'
        assert status['presentation_active'] is True
    
    def test_set_callbacks(self, mock_powerpoint_monitor):
        """Test setting presentation lifecycle callbacks."""
        monitor = PresentationMonitor(PresentationSoftware.POWERPOINT)
        
        start_callback = Mock()
        end_callback = Mock()
        
        monitor.set_presentation_start_callback(start_callback)
        monitor.set_presentation_end_callback(end_callback)
        
        assert monitor.presentation_start_callback == start_callback
        assert monitor.presentation_end_callback == end_callback
    
    @pytest.mark.asyncio
    async def test_slide_change_detection(self, mock_powerpoint_monitor):
        """Test slide change detection in monitoring loop."""
        monitor = PresentationMonitor(PresentationSoftware.POWERPOINT)
        
        # Mock initial state - no presentation
        mock_powerpoint_monitor.is_powerpoint_running.return_value = False
        mock_powerpoint_monitor.get_current_slide_info.return_value = None
        
        # Set very short poll interval for testing
        monitor.set_poll_interval(0.1)
        
        callback_calls = []
        
        def test_callback(event):
            callback_calls.append(event)
        
        # Start monitoring
        await monitor.start_monitoring(test_callback)
        
        # Wait a bit for initial state
        await asyncio.sleep(0.2)
        
        # Simulate PowerPoint starting and slide change
        mock_powerpoint_monitor.is_powerpoint_running.return_value = True
        mock_powerpoint_monitor.get_current_slide_info.return_value = SlideInfo(
            slide_index=0,
            slide_title="First Slide",
            total_slides=3,
            is_slideshow_mode=True
        )
        mock_powerpoint_monitor.get_speaker_notes.return_value = "Test notes"
        mock_powerpoint_monitor.get_presentation_path.return_value = "/test.pptx"
        
        # Wait for monitoring to detect changes
        await asyncio.sleep(0.3)
        
        # Simulate slide change
        mock_powerpoint_monitor.get_current_slide_info.return_value = SlideInfo(
            slide_index=1,
            slide_title="Second Slide",
            total_slides=3,
            is_slideshow_mode=True
        )
        
        # Wait for slide change detection
        await asyncio.sleep(0.3)
        
        # Stop monitoring
        await monitor.stop_monitoring()
        
        # Check that callbacks were called
        assert len(callback_calls) >= 1
        
        # Find slide change events
        slide_events = [event for event in callback_calls if event.event_type == "slide_changed"]
        assert len(slide_events) >= 1
        
        # Check first slide event
        first_event = slide_events[0]
        assert first_event.slide_data.slide_index == 0
        assert first_event.slide_data.slide_title == "First Slide"
    
    def test_context_manager(self, mock_powerpoint_monitor):
        """Test using PresentationMonitor as context manager."""
        with PresentationMonitor(PresentationSoftware.POWERPOINT) as monitor:
            assert isinstance(monitor, PresentationMonitor)
        
        # Should not raise any exceptions


@pytest.mark.integration
class TestPresentationMonitorIntegration:
    """Integration tests for PresentationMonitor."""
    
    @pytest.mark.skipif(
        not hasattr(pytest, 'applescript_available') or not pytest.applescript_available,
        reason="AppleScript not available for integration testing"
    )
    def test_real_powerpoint_detection(self):
        """Test real PowerPoint detection (requires PowerPoint to be installed)."""
        try:
            from src.services.presentation_monitor import PowerPointMacMonitor
            monitor = PowerPointMacMonitor()
            
            # This should not raise an exception
            is_running = monitor.is_powerpoint_running()
            assert isinstance(is_running, bool)
            
        except RuntimeError:
            pytest.skip("PowerPoint monitoring not available on this system")


if __name__ == "__main__":
    pytest.main([__file__])