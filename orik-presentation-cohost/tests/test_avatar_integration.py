"""Integration tests for OrikAvatarUI with the rest of the system."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.ui.orik_avatar_ui import OrikAvatarUI, WindowConfig
from src.models.system_status import SystemStatus
from src.models.enums import PlaybackStatus


class TestAvatarSystemIntegration:
    """Test OrikAvatarUI integration with system components."""
    
    @pytest.fixture
    def avatar_ui(self):
        """Create OrikAvatarUI instance for testing."""
        config = WindowConfig(width=300, height=400)
        ui = OrikAvatarUI(config)
        
        # Mock UI elements to avoid tkinter dependency
        ui.status_label = Mock()
        ui.error_label = Mock()
        ui.speaking_indicator = Mock()
        ui.avatar_canvas = Mock()
        
        return ui
    
    def test_system_status_integration(self, avatar_ui):
        """Test integration with SystemStatus model."""
        # Test fully operational system
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
    
    def test_error_state_integration(self, avatar_ui):
        """Test integration with error states."""
        status = SystemStatus(
            is_monitoring=False,
            presentation_connected=False,
            tts_available=True,
            audio_ready=True,
            last_activity=datetime.now(),
            error_state="Presentation software disconnected"
        )
        
        avatar_ui.update_system_status(status)
        
        avatar_ui.status_label.config.assert_called_with(text="System errors detected")
        avatar_ui.error_label.config.assert_called_with(text="ERROR: Presentation software disconnected")
    
    def test_partial_failure_integration(self, avatar_ui):
        """Test integration with partial system failures."""
        status = SystemStatus(
            is_monitoring=True,
            presentation_connected=False,
            tts_available=False,
            audio_ready=True,
            last_activity=datetime.now()
        )
        
        avatar_ui.update_system_status(status)
        
        # Should show failed components
        avatar_ui.status_label.config.assert_called_with(text="Issues: presentation, tts")
    
    def test_speaking_state_workflow(self, avatar_ui):
        """Test typical speaking state workflow."""
        # Start idle
        avatar_ui.set_speaking_state(False)
        avatar_ui.speaking_indicator.config.assert_called_with(
            text="● IDLE",
            fg='#666666'
        )
        
        # Start speaking
        avatar_ui.set_speaking_state(True)
        avatar_ui.speaking_indicator.config.assert_called_with(
            text="● SPEAKING",
            fg='#00ffff'
        )
        
        # Return to idle
        avatar_ui.set_speaking_state(False)
        avatar_ui.speaking_indicator.config.assert_called_with(
            text="● IDLE",
            fg='#666666'
        )
    
    def test_error_recovery_workflow(self, avatar_ui):
        """Test error recovery workflow."""
        # Show error
        avatar_ui.show_error("TTS service unavailable")
        avatar_ui.error_label.config.assert_called_with(text="ERROR: TTS service unavailable")
        
        # Clear error
        avatar_ui.clear_error()
        avatar_ui.error_label.config.assert_called_with(text="")
        
        assert avatar_ui.error_message is None
    
    def test_status_update_workflow(self, avatar_ui):
        """Test status update workflow."""
        status_messages = [
            "Initializing...",
            "Connecting to presentation software...",
            "Ready for presentation",
            "Processing slide change...",
            "Generating response...",
            "Playing audio..."
        ]
        
        for message in status_messages:
            avatar_ui.update_status(message)
            avatar_ui.status_label.config.assert_called_with(text=message)
            assert avatar_ui.current_status == message
    
    def test_window_lifecycle(self, avatar_ui):
        """Test window lifecycle management."""
        # Initially not visible
        assert avatar_ui.is_visible is False
        
        # Mock the initialization to avoid tkinter
        mock_root = Mock()
        with patch.object(avatar_ui, 'initialize') as mock_init:
            mock_init.side_effect = lambda: setattr(avatar_ui, 'root', mock_root)
            avatar_ui.show_avatar()
            mock_init.assert_called_once()
            assert avatar_ui.is_visible is True
            mock_root.deiconify.assert_called_once()
            mock_root.lift.assert_called_once()
        
        # Hide avatar
        avatar_ui.hide_avatar()
        assert avatar_ui.is_visible is False
        mock_root.withdraw.assert_called_once()
    
    def test_callback_integration(self, avatar_ui):
        """Test callback integration."""
        callback = Mock()
        avatar_ui.set_on_close_callback(callback)
        
        # Simulate window close
        with patch.object(avatar_ui, 'destroy') as mock_destroy:
            avatar_ui._on_window_close()
            callback.assert_called_once()
            mock_destroy.assert_called_once()
    
    def test_animation_state_management(self, avatar_ui):
        """Test animation state management."""
        # Test animation thread management
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            mock_thread_instance.is_alive.return_value = False
            
            avatar_ui._start_animation_thread()
            
            assert avatar_ui.animation_running is True
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
    
    def test_canvas_drawing_states(self, avatar_ui):
        """Test canvas drawing in different states."""
        # Test idle state drawing
        avatar_ui.is_speaking = False
        avatar_ui._draw_avatar()
        
        # Verify canvas operations
        avatar_ui.avatar_canvas.delete.assert_called_with("all")
        assert avatar_ui.avatar_canvas.create_oval.called
        
        # Test speaking state drawing
        avatar_ui.is_speaking = True
        avatar_ui._draw_avatar()
        
        # Should have additional glow effect when speaking
        assert avatar_ui.avatar_canvas.create_oval.call_count > 1


class TestAvatarConfigurationIntegration:
    """Test avatar configuration integration."""
    
    def test_custom_configuration(self):
        """Test custom window configuration."""
        config = WindowConfig(
            width=500,
            height=600,
            x_position=200,
            y_position=300,
            always_on_top=False,
            title="Custom Orik"
        )
        
        avatar = OrikAvatarUI(config)
        
        assert avatar.config.width == 500
        assert avatar.config.height == 600
        assert avatar.config.x_position == 200
        assert avatar.config.y_position == 300
        assert avatar.config.always_on_top is False
        assert avatar.config.title == "Custom Orik"
    
    def test_default_configuration(self):
        """Test default window configuration."""
        avatar = OrikAvatarUI()
        
        assert avatar.config.width == 300
        assert avatar.config.height == 400
        assert avatar.config.x_position == 100
        assert avatar.config.y_position == 100
        assert avatar.config.always_on_top is True
        assert avatar.config.title == "Orik - AI Co-host"


class TestAvatarErrorHandling:
    """Test avatar error handling scenarios."""
    
    def test_missing_tkinter_handling(self):
        """Test handling when tkinter is not available."""
        avatar = OrikAvatarUI()
        
        # Mock TKINTER_AVAILABLE to False
        with patch('src.ui.orik_avatar_ui.TKINTER_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="tkinter is not available"):
                avatar.initialize()
    
    def test_graceful_degradation(self):
        """Test graceful degradation when UI elements are missing."""
        avatar = OrikAvatarUI()
        
        # Test operations without UI elements (should not raise exceptions)
        avatar.set_speaking_state(True)
        avatar.show_error("Test error")
        avatar.clear_error()
        avatar.update_status("Test status")
        avatar.hide_avatar()
        avatar.update()
        avatar._draw_avatar()
    
    def test_animation_error_handling(self):
        """Test animation error handling."""
        avatar = OrikAvatarUI()
        avatar.animation_running = True
        avatar.root = None  # This should cause graceful handling
        
        # Should not raise exception
        avatar._animation_loop()
    
    def test_cleanup_on_destroy(self):
        """Test proper cleanup on destroy."""
        avatar = OrikAvatarUI()
        avatar.animation_running = True
        avatar.root = Mock()
        
        avatar.destroy()
        
        assert avatar.animation_running is False
        assert avatar.root is None
        assert avatar.is_visible is False


if __name__ == "__main__":
    pytest.main([__file__])