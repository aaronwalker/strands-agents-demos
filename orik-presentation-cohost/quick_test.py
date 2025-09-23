#!/usr/bin/env python3
"""
Quick Test Script for Orik Components

Run individual components quickly for testing and development.
"""

import sys
import subprocess
from pathlib import Path

def run_component(component):
    """Run a specific component."""
    
    components = {
        "avatar": {
            "script": "demo_avatar_ui.py",
            "description": "Orik Avatar UI with visual feedback"
        },
        "agent": {
            "script": "demo_orik_agent.py", 
            "description": "Orik AI Agent with personality"
        },
        "tts": {
            "script": "test_tts_basic_functionality.py",
            "description": "Text-to-Speech functionality"
        },
        "dig": {
            "script": "test_dig_at_aaron_mcp.py",
            "description": "DigAtAaron sarcastic one-liners"
        },
        "mcp": {
            "script": "test_mcp_server.py",
            "description": "MCP server functionality"
        },
        "basic": {
            "script": "test_basic_functionality.py",
            "description": "Basic system functionality"
        },
        "system": {
            "script": "run_orik_system.py",
            "description": "Complete Orik system (all components)"
        }
    }
    
    if component not in components:
        print(f"❌ Unknown component: {component}")
        print("\nAvailable components:")
        for name, info in components.items():
            print(f"  {name:8} - {info['description']}")
        return False
    
    info = components[component]
    script = info["script"]
    
    print(f"🚀 Running: {info['description']}")
    print(f"📄 Script: {script}")
    print("-" * 50)
    
    try:
        # Run from current directory (should already be in orik-presentation-cohost)
        result = subprocess.run([sys.executable, script], check=True)
        print(f"\n✅ {component} completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {component} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Script not found: {script}")
        return False
    except Exception as e:
        print(f"\n❌ Error running {component}: {e}")
        return False


def run_tests():
    """Run all unit tests."""
    print("🧪 Running All Unit Tests")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", "-v", "--tb=short"
        ], check=True)
        
        print("\n✅ All tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("🎪 Orik Component Quick Test")
        print("=" * 30)
        print("\nUsage:")
        print("  python3 quick_test.py <component>")
        print("  python3 quick_test.py tests")
        print("\nComponents:")
        print("  avatar   - Visual avatar UI")
        print("  agent    - AI agent core")
        print("  tts      - Text-to-speech")
        print("  dig      - Sarcastic one-liners")
        print("  mcp      - MCP server test")
        print("  basic    - Basic functionality")
        print("  system   - Complete system")
        print("  tests    - Run all unit tests")
        print("\nExamples:")
        print("  python3 quick_test.py avatar")
        print("  python3 quick_test.py system")
        print("  python3 quick_test.py tests")
        return
    
    component = sys.argv[1].lower()
    
    if component == "tests":
        success = run_tests()
    else:
        success = run_component(component)
    
    if success:
        print(f"\n🎉 {component} completed successfully!")
    else:
        print(f"\n💥 {component} failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()