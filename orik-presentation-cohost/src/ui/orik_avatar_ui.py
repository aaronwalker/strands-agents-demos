"""OrikAvatarUI component for visual feedback and avatar display."""

try:
    import tkinter as tk
    from tkinter import ttk
    TKINTER_AVAILABLE = True
except ImportError:
    # Handle environments where tkinter is not available
    tk = None
    ttk = None
    TKINTER_AVAILABLE = False

from typing import Optional, Callable
from datetime import datetime
import threading
import time
from dataclasses import dataclass

from ..models.system_status import SystemStatus


@dataclass
class WindowConfig:
    """Configuration for the avatar window."""
    width: int = 300
    height: int = 400
    x_position: int = 100
    y_position: int = 100
    always_on_top: bool = True
    transparent_bg: bool = True
    title: str = "Orik - AI Co-host"


class OrikAvatarUI:
    """Visual avatar display for Orik with speaking animations and status indicators."""
    
    def __init__(self, window_config: WindowConfig = None):
        """Initialize the Orik Avatar UI.
        
        Args:
            window_config: Configuration for the avatar window
        """
        self.config = window_config or WindowConfig()
        self.root = None
        self.is_visible = False
        self.is_speaking = False
        self.current_status = "Initializing..."
        self.error_message = None
        
        # Animation state
        self.animation_thread = None
        self.animation_running = False
        self.blink_counter = 0
        
        # UI elements
        self.avatar_canvas = None
        self.status_label = None
        self.error_label = None
        self.speaking_indicator = None
        
        # Callbacks
        self.on_close_callback: Optional[Callable] = None
        
    def initialize(self) -> None:
        """Initialize the tkinter window and UI elements."""
        if not TKINTER_AVAILABLE:
            raise RuntimeError("tkinter is not available in this environment")
            
        if self.root is not None:
            return
            
        self.root = tk.Tk()
        self.root.title(self.config.title)
        self.root.geometry(f"{self.config.width}x{self.config.height}+{self.config.x_position}+{self.config.y_position}")
        
        if self.config.always_on_top:
            self.root.attributes('-topmost', True)
            
        # Configure window appearance
        self.root.configure(bg='#1a1a1a')  # Dark background
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        self._create_ui_elements()
        self._start_animation_thread()
        
    def _create_ui_elements(self) -> None:
        """Create and layout UI elements."""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="ORIK",
            font=('Arial', 16, 'bold'),
            fg='#00ff88',
            bg='#1a1a1a'
        )
        title_label.pack(pady=(0, 10))
        
        # Avatar canvas
        self.avatar_canvas = tk.Canvas(
            main_frame,
            width=200,
            height=200,
            bg='#1a1a1a',
            highlightthickness=0
        )
        self.avatar_canvas.pack(pady=10)
        
        # Speaking indicator
        self.speaking_indicator = tk.Label(
            main_frame,
            text="● IDLE",
            font=('Arial', 10, 'bold'),
            fg='#666666',
            bg='#1a1a1a'
        )
        self.speaking_indicator.pack(pady=5)
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text=self.current_status,
            font=('Arial', 9),
            fg='#cccccc',
            bg='#1a1a1a',
            wraplength=280
        )
        self.status_label.pack(pady=5)
        
        # Error label (initially hidden)
        self.error_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 9, 'bold'),
            fg='#ff4444',
            bg='#1a1a1a',
            wraplength=280
        )
        self.error_label.pack(pady=5)
        
        # Draw initial avatar
        self._draw_avatar()
        
    def _draw_avatar(self) -> None:
        """Draw the Orik avatar on the canvas."""
        if not self.avatar_canvas:
            return
            
        # Clear canvas
        self.avatar_canvas.delete("all")
        
        # Avatar colors
        ghost_color = '#00ff88' if not self.is_speaking else '#00ffff'
        eye_color = '#ffffff'
        
        # Draw ghostly body (oval)
        body_x1, body_y1 = 50, 80
        body_x2, body_y2 = 150, 180
        self.avatar_canvas.create_oval(
            body_x1, body_y1, body_x2, body_y2,
            fill=ghost_color,
            outline='#ffffff',
            width=2,
            stipple='gray25' if not self.is_speaking else None
        )
        
        # Draw eyes
        eye_size = 8 if not self.is_speaking else 12
        left_eye_x, left_eye_y = 75, 110
        right_eye_x, right_eye_y = 125, 110
        
        # Blinking animation
        if self.blink_counter > 0:
            # Draw closed eyes (lines)
            self.avatar_canvas.create_line(
                left_eye_x - eye_size//2, left_eye_y,
                left_eye_x + eye_size//2, left_eye_y,
                fill=eye_color, width=3
            )
            self.avatar_canvas.create_line(
                right_eye_x - eye_size//2, right_eye_y,
                right_eye_x + eye_size//2, right_eye_y,
                fill=eye_color, width=3
            )
        else:
            # Draw open eyes (circles)
            self.avatar_canvas.create_oval(
                left_eye_x - eye_size//2, left_eye_y - eye_size//2,
                left_eye_x + eye_size//2, left_eye_y + eye_size//2,
                fill=eye_color, outline='#000000'
            )
            self.avatar_canvas.create_oval(
                right_eye_x - eye_size//2, right_eye_y - eye_size//2,
                right_eye_x + eye_size//2, right_eye_y + eye_size//2,
                fill=eye_color, outline='#000000'
            )
        
        # Draw mouth (changes based on speaking state)
        mouth_x, mouth_y = 100, 140
        if self.is_speaking:
            # Open mouth (oval)
            self.avatar_canvas.create_oval(
                mouth_x - 15, mouth_y - 8,
                mouth_x + 15, mouth_y + 8,
                fill='#000000', outline=eye_color, width=2
            )
        else:
            # Closed mouth (line)
            self.avatar_canvas.create_line(
                mouth_x - 10, mouth_y,
                mouth_x + 10, mouth_y,
                fill=eye_color, width=3
            )
        
        # Add glow effect when speaking
        if self.is_speaking:
            self.avatar_canvas.create_oval(
                body_x1 - 5, body_y1 - 5, body_x2 + 5, body_y2 + 5,
                outline=ghost_color, width=1, stipple='gray12'
            )
            
    def _start_animation_thread(self) -> None:
        """Start the animation thread for avatar updates."""
        if self.animation_thread and self.animation_thread.is_alive():
            return
            
        self.animation_running = True
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()
        
    def _animation_loop(self) -> None:
        """Main animation loop running in separate thread."""
        frame_count = 0
        
        while self.animation_running and self.root:
            try:
                # Blink animation (every 3-5 seconds)
                if frame_count % 180 == 0:  # ~3 seconds at 60fps
                    self.blink_counter = 5  # Blink for 5 frames
                
                if self.blink_counter > 0:
                    self.blink_counter -= 1
                
                # Update avatar drawing
                if self.root:
                    self.root.after(0, self._draw_avatar)
                
                frame_count += 1
                time.sleep(1/60)  # 60 FPS
                
            except Exception as e:
                print(f"Animation error: {e}")
                break
                
    def show_avatar(self) -> None:
        """Show the avatar window."""
        if not self.root:
            self.initialize()
            
        self.root.deiconify()
        self.root.lift()
        self.is_visible = True
        
    def hide_avatar(self) -> None:
        """Hide the avatar window."""
        if self.root:
            self.root.withdraw()
        self.is_visible = False
        
    def set_speaking_state(self, is_speaking: bool) -> None:
        """Set the speaking state and update visual feedback.
        
        Args:
            is_speaking: True if Orik is currently speaking
        """
        self.is_speaking = is_speaking
        
        # Update speaking indicator
        if self.speaking_indicator:
            if is_speaking:
                self.speaking_indicator.config(
                    text="● SPEAKING",
                    fg='#00ffff'
                )
            else:
                self.speaking_indicator.config(
                    text="● IDLE",
                    fg='#666666'
                )
        
        # Redraw avatar with new state
        self._draw_avatar()
        
    def show_error(self, error_message: str) -> None:
        """Display an error message.
        
        Args:
            error_message: Error message to display
        """
        self.error_message = error_message
        if self.error_label:
            self.error_label.config(text=f"ERROR: {error_message}")
            
    def clear_error(self) -> None:
        """Clear the current error message."""
        self.error_message = None
        if self.error_label:
            self.error_label.config(text="")
            
    def update_status(self, status: str) -> None:
        """Update the status display.
        
        Args:
            status: Status message to display
        """
        self.current_status = status
        if self.status_label:
            self.status_label.config(text=status)
            
    def update_system_status(self, system_status: SystemStatus) -> None:
        """Update display based on system status.
        
        Args:
            system_status: Current system status
        """
        # Update status message
        if system_status.is_fully_operational:
            self.update_status("All systems operational")
            self.clear_error()
        elif system_status.has_errors:
            self.update_status("System errors detected")
            self.show_error(system_status.error_state)
        else:
            failed = system_status.failed_components
            if failed:
                self.update_status(f"Issues: {', '.join(failed)}")
            else:
                self.update_status("Starting up...")
                
    def set_on_close_callback(self, callback: Callable) -> None:
        """Set callback for when window is closed.
        
        Args:
            callback: Function to call when window is closed
        """
        self.on_close_callback = callback
        
    def _on_window_close(self) -> None:
        """Handle window close event."""
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()
        
    def destroy(self) -> None:
        """Clean up and destroy the UI."""
        self.animation_running = False
        
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)
            
        if self.root:
            self.root.destroy()
            self.root = None
            
        self.is_visible = False
        
    def run_mainloop(self) -> None:
        """Run the tkinter main loop (blocking)."""
        if not self.root:
            self.initialize()
        self.root.mainloop()
        
    def update(self) -> None:
        """Process pending tkinter events (non-blocking)."""
        if self.root:
            self.root.update()


# Convenience function for testing
def create_test_avatar() -> OrikAvatarUI:
    """Create a test avatar with default configuration."""
    config = WindowConfig(
        width=300,
        height=400,
        x_position=200,
        y_position=200,
        always_on_top=True
    )
    return OrikAvatarUI(config)


if __name__ == "__main__":
    # Test the avatar UI
    avatar = create_test_avatar()
    avatar.show_avatar()
    
    # Simulate some state changes
    import time
    
    def test_sequence():
        time.sleep(2)
        avatar.update_status("Testing speaking state...")
        avatar.set_speaking_state(True)
        
        time.sleep(3)
        avatar.set_speaking_state(False)
        avatar.update_status("Testing error state...")
        avatar.show_error("Test error message")
        
        time.sleep(2)
        avatar.clear_error()
        avatar.update_status("Test complete")
    
    # Run test in separate thread
    test_thread = threading.Thread(target=test_sequence, daemon=True)
    test_thread.start()
    
    avatar.run_mainloop()