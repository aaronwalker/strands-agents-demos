"""Unit tests for OrikAvatarUI component."""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import threading
import time

# Mock tkinter before importing the module
with patch.dict('sys.modules', {'tkinter': Mock(), 'tkinter.ttk': Mock()}):
    from src.ui.orik_avatar_ui import OrikAvatarUI, WindowConfig
    from src.models.system_status import SystemStatus


class TestWindowConfig:
    """Test WindowConfig dataclass."""
    
    def test_default_config(self):
        """Test default window configuration."""
        config = WindowConfig()
        assert config.width == 300
        assert config.height == 400
        assert config.x_position == 100
        assert config.y_position == 100
        assert config.always_on_top is True
        assert config.transparent_bg is True
        assert config.title == "Orik - AI Co-host"
    
    def test_custom_config(self):
        """Test custom window configuration."""
        config = WindowConfig(
            width=500,
            height=600,
            x_position=200,
            y_position=300,
            always_on_top=False,
            transparent_bg=False,
            title="Custom Title"
        )
        assert config.width == 500
        assert config.height == 600
        assert config.x_position == 200
        assert config.y_position == 300
        assert config.always_on_top is False
        assert config.transparent_bg is False
        assert config.title == "Custom Title"


class TestOrikAvatarUI:
    """Test OrikAvatarUI class."""
    
    @pytest.fixture
    def mock_tk_root(self):
        """Mock tkinter root window."""
        with patch('src.ui.orik_avatar_ui.tk.Tk') as mock_tk:
            mock_root = Mock()
            mock_tk.return_value = mock_root
            yield mock_root
    
    @pytest.fixture
    def avatar_ui(self):
        """Create OrikAvatarUI instance for testing."""
        config = WindowConfig(width=300, height=400)
        return OrikAvatarUI(config)
    
    def test_initialization(self, avatar_ui):
        """Test OrikAvatarUI initialization."""
        assert avatar_ui.config.width == 300
        assert avatar_ui.config.height == 400
        assert avatar_ui.root is None
        assert avatar_ui.is_visible is False
        assert avatar_ui.is_speaking is False
        assert avatar_ui.current_status == "Initializing..."
        assert avatar_ui.error_message is None
    
    def test_initialize_creates_window(self, avatar_ui, mock_tk_root):
        """Test that initialize creates tkinter window."""
        avatar_ui.initialize()
        
        assert avatar_ui.root is not None
        mock_tk_root.title.assert_called_with("Orik - AI Co-host")
        mock_tk_root.geometry.assert_called_with("300x400+100+100")
        mock_tk_root.attributes.assert_called_with('-topmost', True)
        mock_tk_root.configure.assert_called_with(bg='#1a1a1a')
    
    def test_initialize_idempotent(self, avatar_ui, mock_tk_root):
        """Test that initialize can be called multiple times safely."""
        avatar_ui.initialize()
        first_root = avatar_ui.root
        
        avatar_ui.initialize()
        assert avatar_ui.root is first_root  # Should be same instance
    
    @patch('src.ui.orik_avatar_ui.tk.Frame')
    @patch('src.ui.orik_avatar_ui.tk.Label')
    @patch('src.ui.orik_avatar_ui.tk.Canvas')
    def test_create_ui_elements(self, mock_canvas, mock_label, mock_frame, avatar_ui, mock_tk_root):
        """Test UI elements creation."""
        avatar_ui.root = mock_tk_root
        avatar_ui._create_ui_elements()
        
        # Verify UI elements were created
        assert mock_frame.called
        assert mock_label.called
        assert mock_canvas.called
        
        # Verify canvas was assigned
        assert avatar_ui.avatar_canvas is not None
        assert avatar_ui.status_label is not None
        assert avatar_ui.error_label is not None
        assert avatar_ui.speaking_indicator is not None
    
    def test_show_avatar(self, avatar_ui, mock_tk_root):
        """Test showing the avatar."""
        avatar_ui.show_avatar()
        
        assert avatar_ui.is_visible is True
        assert avatar_ui.root is not None
        mock_tk_root.deiconify.assert_called_once()
        mock_tk_root.lift.assert_called_once()
    
    def test_hide_avatar(self, avatar_ui, mock_tk_root):
        """Test hiding the avatar."""
        avatar_ui.root = mock_tk_root
        avatar_ui.hide_avatar()
        
        assert avatar_ui.is_visible is False
        mock_tk_root.withdraw.assert_called_once()
    
    def test_hide_avatar_no_root(self, avatar_ui):
        """Test hiding avatar when no root exists."""
        avatar_ui.hide_avatar()  # Should not raise exception
        assert avatar_ui.is_visible is False
    
    def test_set_speaking_state_true(self, avatar_ui):
        """Test setting speaking state to true."""
        # Mock speaking indicator
        avatar_ui.speaking_indicator = Mock()
        
        avatar_ui.set_speaking_state(True)
        
        assert avatar_ui.is_speaking is True
        avatar_ui.speaking_indicator.config.assert_called_with(
            text="● SPEAKING",
            fg='#00ffff'
        )
    
    def test_set_speaking_state_false(self, avatar_ui):
        """Test setting speaking state to false."""
        # Mock speaking indicator
        avatar_ui.speaking_indicator = Mock()
        
        avatar_ui.set_speaking_state(False)
        
        assert avatar_ui.is_speaking is False
        avatar_ui.speaking_indicator.config.assert_called_with(
            text="● IDLE",
            fg='#666666'
        )
    
    def test_set_speaking_state_no_indicator(self, avatar_ui):
        """Test setting speaking state when indicator doesn't exist."""
        avatar_ui.set_speaking_state(True)  # Should not raise exception
        assert avatar_ui.is_speaking is True
    
    def test_show_error(self, avatar_ui):
        """Test showing error message."""
        # Mock error label
        avatar_ui.error_label = Mock()
        
        avatar_ui.show_error("Test error")
        
        assert avatar_ui.error_message == "Test error"
        avatar_ui.error_label.config.assert_called_with(text="ERROR: Test error")
    
    def test_show_error_no_label(self, avatar_ui):
        """Test showing error when label doesn't exist."""
        avatar_ui.show_error("Test error")  # Should not raise exception
        assert avatar_ui.error_message == "Test error"
    
    def test_clear_error(self, avatar_ui):
        """Test clearing error message."""
        # Mock error label
        avatar_ui.error_label = Mock()
        avatar_ui.error_message = "Previous error"
        
        avatar_ui.clear_error()
        
        assert avatar_ui.error_message is None
        avatar_ui.error_label.config.assert_called_with(text="")
    
    def test_update_status(self, avatar_ui):
        """Test updating status message."""
        # Mock status label
        avatar_ui.status_label = Mock()
        
        avatar_ui.update_status("New status")
        
        assert avatar_ui.current_status == "New status"
        avatar_ui.status_label.config.assert_called_with(text="New status")
    
    def test_update_status_no_label(self, avatar_ui):
        """Test updating status when label doesn't exist."""
        avatar_ui.update_status("New status")  # Should not raise exception
        assert avatar_ui.current_status == "New status"
    
    def test_update_system_status_operational(self, avatar_ui):
        """Test updating with fully operational system status."""
        # Mock UI elements
        avatar_ui.status_label = Mock()
        avatar_ui.error_label = Mock()
        
        status = SystemStatus(
            is_monitoring=True,
            presentation_connected=True,
            tts_available=True,
            audio_ready=True,
            last_activity=datetime.now()
        )
        
        avatar_ui.update_system_status(status)
        
        avatar_ui.status_label.config.assert_called_with(text="All systems operational")
        avatar_ui.error_label.config.assert_called_with(text="")
    
    def test_update_system_status_with_errors(self, avatar_ui):
        """Test updating with system status containing errors."""
        # Mock UI elements
        avatar_ui.status_label = Mock()
        avatar_ui.error_label = Mock()
        
        status = SystemStatus(
            is_monitoring=True,
            presentation_connected=False,
            tts_available=True,
            audio_ready=True,
            last_activity=datetime.now(),
            error_state="Connection failed"
        )
        
        avatar_ui.update_system_status(status)
        
        avatar_ui.status_label.config.assert_called_with(text="System errors detected")
        avatar_ui.error_label.config.assert_called_with(text="ERROR: Connection failed")
    
    def test_update_system_status_failed_components(self, avatar_ui):
        """Test updating with failed components but no error state."""
        # Mock UI elements
        avatar_ui.status_label = Mock()
        
        status = SystemStatus(
            is_monitoring=False,
            presentation_connected=False,
            tts_available=True,
            audio_ready=True,
            last_activity=datetime.now()
        )
        
        avatar_ui.update_system_status(status)
        
        avatar_ui.status_label.config.assert_called_with(text="Issues: monitoring, presentation")
    
    def test_set_on_close_callback(self, avatar_ui):
        """Test setting close callback."""
        callback = Mock()
        avatar_ui.set_on_close_callback(callback)
        
        assert avatar_ui.on_close_callback is callback
    
    def test_on_window_close_with_callback(self, avatar_ui):
        """Test window close event with callback."""
        callback = Mock()
        avatar_ui.on_close_callback = callback
        
        with patch.object(avatar_ui, 'destroy') as mock_destroy:
            avatar_ui._on_window_close()
            
            callback.assert_called_once()
            mock_destroy.assert_called_once()
    
    def test_on_window_close_without_callback(self, avatar_ui):
        """Test window close event without callback."""
        with patch.object(avatar_ui, 'destroy') as mock_destroy:
            avatar_ui._on_window_close()
            
            mock_destroy.assert_called_once()
    
    def test_destroy_cleans_up(self, avatar_ui, mock_tk_root):
        """Test that destroy properly cleans up resources."""
        avatar_ui.root = mock_tk_root
        avatar_ui.animation_running = True
        avatar_ui.is_visible = True
        
        avatar_ui.destroy()
        
        assert avatar_ui.animation_running is False
        assert avatar_ui.root is None
        assert avatar_ui.is_visible is False
        mock_tk_root.destroy.assert_called_once()
    
    def test_destroy_no_root(self, avatar_ui):
        """Test destroy when no root exists."""
        avatar_ui.destroy()  # Should not raise exception
        assert avatar_ui.root is None
        assert avatar_ui.is_visible is False
    
    def test_update_with_root(self, avatar_ui, mock_tk_root):
        """Test update method with root."""
        avatar_ui.root = mock_tk_root
        
        avatar_ui.update()
        
        mock_tk_root.update.assert_called_once()
    
    def test_update_without_root(self, avatar_ui):
        """Test update method without root."""
        avatar_ui.update()  # Should not raise exception
    
    @patch('threading.Thread')
    def test_start_animation_thread(self, mock_thread, avatar_ui):
        """Test starting animation thread."""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        mock_thread_instance.is_alive.return_value = False
        
        avatar_ui._start_animation_thread()
        
        assert avatar_ui.animation_running is True
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
    
    @patch('threading.Thread')
    def test_start_animation_thread_already_running(self, mock_thread, avatar_ui):
        """Test starting animation thread when already running."""
        mock_thread_instance = Mock()
        mock_thread_instance.is_alive.return_value = True
        avatar_ui.animation_thread = mock_thread_instance
        
        avatar_ui._start_animation_thread()
        
        # Should not create new thread
        mock_thread.assert_not_called()
    
    def test_draw_avatar_no_canvas(self, avatar_ui):
        """Test drawing avatar when canvas doesn't exist."""
        avatar_ui._draw_avatar()  # Should not raise exception
    
    def test_draw_avatar_with_canvas(self, avatar_ui):
        """Test drawing avatar with canvas."""
        # Mock canvas
        mock_canvas = Mock()
        avatar_ui.avatar_canvas = mock_canvas
        
        avatar_ui._draw_avatar()
        
        # Verify canvas operations were called
        mock_canvas.delete.assert_called_with("all")
        assert mock_canvas.create_oval.called
        assert mock_canvas.create_line.called or mock_canvas.create_oval.call_count > 1
    
    def test_draw_avatar_speaking_state(self, avatar_ui):
        """Test drawing avatar in speaking state."""
        # Mock canvas
        mock_canvas = Mock()
        avatar_ui.avatar_canvas = mock_canvas
        avatar_ui.is_speaking = True
        
        avatar_ui._draw_avatar()
        
        # Verify canvas operations were called
        mock_canvas.delete.assert_called_with("all")
        assert mock_canvas.create_oval.called


class TestAvatarIntegration:
    """Integration tests for avatar UI."""
    
    @pytest.fixture
    def system_status(self):
        """Create test system status."""
        return SystemStatus(
            is_monitoring=True,
            presentation_connected=True,
            tts_available=True,
            audio_ready=True,
            last_activity=datetime.now()
        )
    
    def test_full_state_cycle(self, system_status):
        """Test full state cycle of avatar UI."""
        config = WindowConfig(width=200, height=300)
        avatar = OrikAvatarUI(config)
        
        # Mock UI elements to avoid actual tkinter
        avatar.status_label = Mock()
        avatar.error_label = Mock()
        avatar.speaking_indicator = Mock()
        
        # Test state changes
        avatar.update_system_status(system_status)
        avatar.set_speaking_state(True)
        avatar.show_error("Test error")
        avatar.clear_error()
        avatar.set_speaking_state(False)
        
        # Verify final state
        assert avatar.is_speaking is False
        assert avatar.error_message is None
    
    def test_error_handling_in_animation(self):
        """Test error handling in animation loop."""
        avatar = OrikAvatarUI()
        avatar.animation_running = True
        avatar.root = None  # This should cause graceful handling
        
        # This should not raise an exception
        avatar._animation_loop()


# Test the convenience function
def test_create_test_avatar():
    """Test the create_test_avatar convenience function."""
    from src.ui.orik_avatar_ui import create_test_avatar
    
    avatar = create_test_avatar()
    
    # Use string comparison since isinstance might fail with mocked modules
    assert avatar.__class__.__name__ == 'OrikAvatarUI'
    assert avatar.config.width == 300
    assert avatar.config.height == 400
    assert avatar.config.x_position == 200
    assert avatar.config.y_position == 200
    assert avatar.config.always_on_top is True


if __name__ == "__main__":
    pytest.main([__file__])