#!/usr/bin/env python3
"""
Verify Orik Installation Script

Checks that all required dependencies and components are properly installed.
"""

import sys
import importlib
from pathlib import Path

def check_import(module_name, description=""):
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - {description} - Error: {e}")
        return False

def check_file_exists(file_path, description=""):
    """Check if a file exists."""
    if Path(file_path).exists():
        print(f"✅ {file_path} - {description}")
        return True
    else:
        print(f"❌ {file_path} - {description} - File not found")
        return False

def main():
    """Run installation verification."""
    print("🔍 Orik Installation Verification")
    print("=" * 50)
    
    all_good = True
    
    # Core Python modules
    print("\n📦 Core Dependencies:")
    all_good &= check_import("tkinter", "GUI framework")
    all_good &= check_import("pygame", "Audio playback")
    all_good &= check_import("boto3", "AWS SDK")
    all_good &= check_import("mcp", "Model Context Protocol")
    all_good &= check_import("pydantic", "Data validation")
    all_good &= check_import("structlog", "Logging")
    all_good &= check_import("pytest", "Testing framework")
    
    # Platform-specific dependencies
    print("\n🖥️  Platform-specific Dependencies:")
    if sys.platform == "darwin":  # macOS
        all_good &= check_import("applescript", "PowerPoint integration (macOS)")
    elif sys.platform == "win32":  # Windows
        all_good &= check_import("win32com.client", "PowerPoint integration (Windows)")
    
    # Orik components
    print("\n🎪 Orik Components:")
    sys.path.append("src")
    
    all_good &= check_import("src.models.slide_data", "Core data models")
    all_good &= check_import("src.ui.orik_avatar_ui", "Avatar UI component")
    all_good &= check_import("src.agent.orik_agent_controller", "Agent controller")
    all_good &= check_import("src.mcp_tools.speaker_notes_tool", "Speaker notes tool")
    all_good &= check_import("src.mcp_tools.text_to_speech_tool", "Text-to-speech tool")
    all_good &= check_import("src.mcp_tools.dig_at_aaron_tool", "DigAtAaron tool")
    all_good &= check_import("src.services.audio_playback_service", "Audio playback service")
    all_good &= check_import("src.services.presentation_monitor", "Presentation monitor")
    
    # Key files
    print("\n📄 Key Files:")
    all_good &= check_file_exists("demo_avatar_ui.py", "Avatar demo script")
    all_good &= check_file_exists("demo_orik_agent.py", "Agent demo script")
    all_good &= check_file_exists("run_orik_system.py", "Complete system runner")
    all_good &= check_file_exists("requirements.txt", "Dependencies list")
    all_good &= check_file_exists("RUN_GUIDE.md", "Usage guide")
    
    # Test basic functionality
    print("\n🧪 Basic Functionality Tests:")
    try:
        from src.ui.orik_avatar_ui import OrikAvatarUI, WindowConfig
        config = WindowConfig()
        avatar = OrikAvatarUI(config)
        print("✅ Avatar UI can be instantiated")
        all_good &= True
    except Exception as e:
        print(f"❌ Avatar UI instantiation failed: {e}")
        all_good = False
    
    try:
        from src.agent.orik_agent_controller import ResponseGenerator
        from src.models.personality import OrikPersonality
        personality = OrikPersonality.create_default()
        generator = ResponseGenerator(personality)
        print("✅ Agent controller can be instantiated")
        all_good &= True
    except Exception as e:
        print(f"❌ Agent controller instantiation failed: {e}")
        all_good = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 Installation Verification: SUCCESS!")
        print("\n✅ All components are properly installed and working")
        print("✅ Ready to run Orik Presentation Co-host")
        print("\nNext steps:")
        print("  1. Run: python3 demo_avatar_ui.py")
        print("  2. Run: python3 demo_orik_agent.py")
        print("  3. Run: python3 run_orik_system.py")
    else:
        print("❌ Installation Verification: FAILED!")
        print("\n⚠️  Some components are missing or not working properly")
        print("📖 Check the RUN_GUIDE.md for installation instructions")
        print("\nTo install missing dependencies:")
        print("  pip3 install --break-system-packages -r requirements.txt")
        if sys.platform == "darwin":
            print("  brew install python-tk")
            print("  pip3 install --break-system-packages py-applescript")
    
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)