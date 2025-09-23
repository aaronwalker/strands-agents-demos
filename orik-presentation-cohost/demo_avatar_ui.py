#!/usr/bin/env python3
"""Demo script for OrikAvatarUI component."""

import time
import threading
from datetime import datetime

from src.ui.orik_avatar_ui import OrikAvatarUI, WindowConfig
from src.models.system_status import SystemStatus


def demo_avatar_states():
    """Demonstrate different avatar states and animations."""
    
    # Create avatar with custom configuration
    config = WindowConfig(
        width=350,
        height=450,
        x_position=100,
        y_position=100,
        title="Orik Avatar Demo"
    )
    
    avatar = OrikAvatarUI(config)
    
    try:
        print("Starting Orik Avatar Demo...")
        print("Note: This demo requires a GUI environment with tkinter support.")
        
        # Show the avatar
        avatar.show_avatar()
        print("Avatar window should now be visible.")
        
        # Demo sequence
        demo_sequence = [
            ("Initializing system...", False, None),
            ("Connecting to presentation software...", False, None),
            ("System ready - waiting for presentation", False, None),
            ("Orik is now speaking!", True, None),
            ("Back to idle state", False, None),
            ("Testing error state", False, "Connection lost"),
            ("Error cleared - all systems operational", False, None),
            ("Demo complete", False, None)
        ]
        
        for i, (status_msg, is_speaking, error_msg) in enumerate(demo_sequence):
            print(f"Step {i+1}: {status_msg}")
            
            # Update avatar state
            avatar.update_status(status_msg)
            avatar.set_speaking_state(is_speaking)
            
            if error_msg:
                avatar.show_error(error_msg)
            else:
                avatar.clear_error()
            
            # Wait between states
            time.sleep(2)
            
            # Update UI
            avatar.update()
        
        # Demo system status integration
        print("\nDemonstrating SystemStatus integration...")
        
        # Fully operational status
        operational_status = SystemStatus(
            is_monitoring=True,
            presentation_connected=True,
            tts_available=True,
            audio_ready=True,
            last_activity=datetime.now()
        )
        avatar.update_system_status(operational_status)
        time.sleep(2)
        avatar.update()
        
        # Partial failure status
        partial_failure_status = SystemStatus(
            is_monitoring=True,
            presentation_connected=False,
            tts_available=True,
            audio_ready=False,
            last_activity=datetime.now()
        )
        avatar.update_system_status(partial_failure_status)
        time.sleep(2)
        avatar.update()
        
        # Error status
        error_status = SystemStatus(
            is_monitoring=False,
            presentation_connected=False,
            tts_available=False,
            audio_ready=False,
            last_activity=datetime.now(),
            error_state="Critical system failure"
        )
        avatar.update_system_status(error_status)
        time.sleep(3)
        avatar.update()
        
        print("Demo completed. Close the avatar window to exit.")
        
        # Keep the demo running until user closes window
        def on_close():
            print("Avatar window closed. Exiting demo.")
        
        avatar.set_on_close_callback(on_close)
        
        # Run main loop (this will block until window is closed)
        avatar.run_mainloop()
        
    except Exception as e:
        print(f"Demo error: {e}")
        print("This is expected if tkinter is not available in your environment.")
        
    finally:
        avatar.destroy()
        print("Demo cleanup completed.")


def demo_non_blocking():
    """Demonstrate non-blocking avatar usage."""
    
    print("\nDemonstrating non-blocking avatar usage...")
    
    avatar = OrikAvatarUI()
    
    try:
        avatar.show_avatar()
        
        # Simulate background processing
        for i in range(10):
            avatar.update_status(f"Processing step {i+1}/10...")
            
            # Simulate speaking every few steps
            if i % 3 == 0:
                avatar.set_speaking_state(True)
                time.sleep(0.5)
                avatar.set_speaking_state(False)
            
            # Update UI without blocking
            avatar.update()
            time.sleep(0.5)
        
        avatar.update_status("Processing complete!")
        avatar.update()
        time.sleep(2)
        
    except Exception as e:
        print(f"Non-blocking demo error: {e}")
        
    finally:
        avatar.destroy()


if __name__ == "__main__":
    print("Orik Avatar UI Demo")
    print("==================")
    
    try:
        # Run the main demo
        demo_avatar_states()
        
        # Run non-blocking demo
        demo_non_blocking()
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Demo failed: {e}")
        print("\nThis is expected if running in an environment without GUI support.")
        print("The OrikAvatarUI component is designed to work in GUI environments with tkinter.")