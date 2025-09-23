#!/usr/bin/env python3
"""
Complete Orik Presentation Co-host System Runner

This script demonstrates how to run all components of the Orik system together.
"""

import asyncio
import subprocess
import time
import signal
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.ui.orik_avatar_ui import OrikAvatarUI, WindowConfig
from src.models.system_status import SystemStatus
from datetime import datetime


class OrikSystemRunner:
    """Orchestrates the complete Orik system."""
    
    def __init__(self):
        self.mcp_processes = []
        self.avatar_ui = None
        self.running = False
        
    def start_mcp_servers(self):
        """Start all MCP servers in background processes."""
        print("🚀 Starting MCP Servers...")
        
        servers = [
            ("Speaker Notes Server", "src/mcp_tools/run_speaker_notes_server.py"),
            ("Text-to-Speech Server", "src/mcp_tools/run_text_to_speech_server.py"),
            ("DigAtAaron Server", "src/mcp_tools/run_dig_at_aaron_server.py")
        ]
        
        for name, script in servers:
            try:
                print(f"   Starting {name}...")
                process = subprocess.Popen([
                    sys.executable, script
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.mcp_processes.append((name, process))
                time.sleep(1)  # Give each server time to start
                print(f"   ✅ {name} started (PID: {process.pid})")
            except Exception as e:
                print(f"   ❌ Failed to start {name}: {e}")
        
        print(f"✅ Started {len(self.mcp_processes)} MCP servers")
        
    def start_avatar_ui(self):
        """Start the Orik Avatar UI."""
        print("\n🎭 Starting Orik Avatar UI...")
        
        try:
            config = WindowConfig(
                width=350,
                height=450,
                x_position=50,
                y_position=50,
                title="Orik - Presentation Co-host"
            )
            
            self.avatar_ui = OrikAvatarUI(config)
            self.avatar_ui.show_avatar()
            self.avatar_ui.update_status("System starting up...")
            
            print("✅ Orik Avatar UI started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Avatar UI: {e}")
            return False
    
    def simulate_presentation_workflow(self):
        """Simulate a presentation workflow with Orik interactions."""
        print("\n📊 Simulating Presentation Workflow...")
        
        if not self.avatar_ui:
            print("❌ Avatar UI not available")
            return
        
        # Simulation steps
        steps = [
            ("Connecting to PowerPoint...", False, None),
            ("Monitoring slide changes...", False, None),
            ("Slide 1: Introduction detected", False, None),
            ("Found [Orik] tag in speaker notes", False, None),
            ("Generating sarcastic response...", False, None),
            ("Orik is speaking!", True, None),
            ("Response complete", False, None),
            ("Slide 2: Technical content", False, None),
            ("No [Orik] tags found", False, None),
            ("Generating random dig at Aaron...", False, None),
            ("Orik interrupts with sarcasm!", True, None),
            ("Back to monitoring...", False, None),
            ("Connection lost!", False, "PowerPoint connection failed"),
            ("Reconnecting...", False, None),
            ("System restored", False, None),
            ("Ready for next slide", False, None)
        ]
        
        for i, (status, speaking, error) in enumerate(steps):
            print(f"   Step {i+1}: {status}")
            
            # Update avatar
            self.avatar_ui.update_status(status)
            self.avatar_ui.set_speaking_state(speaking)
            
            if error:
                self.avatar_ui.show_error(error)
            else:
                self.avatar_ui.clear_error()
            
            # Update system status
            system_status = SystemStatus(
                is_monitoring=True,
                presentation_connected=error is None,
                tts_available=True,
                audio_ready=True,
                last_activity=datetime.now(),
                error_state=error
            )
            self.avatar_ui.update_system_status(system_status)
            
            # Update UI
            self.avatar_ui.update()
            
            # Wait between steps
            time.sleep(2 if speaking else 1)
        
        print("✅ Presentation workflow simulation complete")
    
    def run_interactive_mode(self):
        """Run interactive mode where user can control Orik."""
        print("\n🎮 Interactive Mode - Control Orik")
        print("Commands:")
        print("  's' - Toggle speaking state")
        print("  'e' - Show error")
        print("  'c' - Clear error")
        print("  'q' - Quit")
        print("  'h' - Show help")
        
        speaking = False
        
        while self.running:
            try:
                self.avatar_ui.update()
                
                # Simple input handling (non-blocking would be better)
                print("\nEnter command (or 'h' for help): ", end='')
                cmd = input().strip().lower()
                
                if cmd == 'q':
                    break
                elif cmd == 's':
                    speaking = not speaking
                    self.avatar_ui.set_speaking_state(speaking)
                    print(f"Orik is now {'speaking' if speaking else 'idle'}")
                elif cmd == 'e':
                    self.avatar_ui.show_error("Test error message")
                    print("Error displayed")
                elif cmd == 'c':
                    self.avatar_ui.clear_error()
                    print("Error cleared")
                elif cmd == 'h':
                    print("Commands: 's'=toggle speaking, 'e'=error, 'c'=clear, 'q'=quit")
                else:
                    print("Unknown command. Type 'h' for help.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in interactive mode: {e}")
                break
    
    def stop_mcp_servers(self):
        """Stop all MCP servers."""
        print("\n🛑 Stopping MCP Servers...")
        
        for name, process in self.mcp_processes:
            try:
                print(f"   Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"   ✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"   ❌ Error stopping {name}: {e}")
        
        self.mcp_processes.clear()
        print("✅ All MCP servers stopped")
    
    def cleanup(self):
        """Clean up all resources."""
        print("\n🧹 Cleaning up...")
        
        self.running = False
        
        if self.avatar_ui:
            self.avatar_ui.destroy()
            print("✅ Avatar UI cleaned up")
        
        self.stop_mcp_servers()
        print("✅ Cleanup complete")
    
    def run(self, mode="demo"):
        """Run the complete Orik system.
        
        Args:
            mode: "demo" for automated demo, "interactive" for manual control
        """
        self.running = True
        
        try:
            print("🎪 ORIK PRESENTATION CO-HOST SYSTEM")
            print("=" * 50)
            
            # Start MCP servers
            self.start_mcp_servers()
            
            # Start Avatar UI
            if not self.start_avatar_ui():
                print("❌ Cannot continue without Avatar UI")
                return
            
            # Wait for servers to fully initialize
            print("\n⏳ Waiting for servers to initialize...")
            time.sleep(3)
            
            if mode == "demo":
                # Run automated demo
                self.simulate_presentation_workflow()
                
                # Keep running until user closes avatar
                print("\n✨ Demo complete! Close the avatar window to exit.")
                self.avatar_ui.set_on_close_callback(lambda: setattr(self, 'running', False))
                
                while self.running and self.avatar_ui.is_visible:
                    self.avatar_ui.update()
                    time.sleep(0.1)
                    
            elif mode == "interactive":
                # Run interactive mode
                self.run_interactive_mode()
            
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
        except Exception as e:
            print(f"\n❌ System error: {e}")
        finally:
            self.cleanup()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the Orik Presentation Co-host System")
    parser.add_argument(
        "--mode", 
        choices=["demo", "interactive"], 
        default="demo",
        help="Run mode: demo (automated) or interactive (manual control)"
    )
    parser.add_argument(
        "--no-servers",
        action="store_true",
        help="Skip starting MCP servers (useful if already running)"
    )
    
    args = parser.parse_args()
    
    runner = OrikSystemRunner()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n⚠️  Shutting down...")
        runner.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Skip MCP servers if requested
    if args.no_servers:
        runner.start_mcp_servers = lambda: print("⏭️  Skipping MCP server startup")
        runner.stop_mcp_servers = lambda: print("⏭️  Skipping MCP server cleanup")
    
    runner.run(args.mode)


if __name__ == "__main__":
    main()