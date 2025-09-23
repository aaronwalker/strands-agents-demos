#!/usr/bin/env python3
"""
Simple audio test using the MCP tool directly.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_tts_mcp_tool():
    """Test the TTS MCP tool directly."""
    print("🎤 Testing TTS MCP Tool")
    print("=" * 30)
    
    try:
        from mcp_tools.text_to_speech_tool import synthesize_speech
        
        # Test with simple parameters
        test_text = "Hello! I'm Orik, your sarcastic AI co-host."
        
        print(f"Testing: '{test_text}'")
        print("🔄 Generating speech...")
        
        # Call the MCP tool function directly
        result = synthesize_speech(
            text=test_text,
            voice_id="Matthew",
            engine="neural",
            speed=1.1,
            pitch=-10
        )
        
        print(f"Result: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            audio_data = result.get("audio_data")
            if audio_data:
                print(f"✅ Generated {len(audio_data)} bytes of audio")
                
                # Try to play with pygame
                try:
                    import pygame
                    import io
                    
                    pygame.mixer.init()
                    
                    # Convert bytes to pygame sound
                    audio_buffer = io.BytesIO(audio_data)
                    sound = pygame.mixer.Sound(audio_buffer)
                    
                    print("🔊 Playing audio...")
                    sound.play()
                    
                    # Wait for playback to complete
                    import time
                    while pygame.mixer.get_busy():
                        time.sleep(0.1)
                    
                    print("✅ Audio playback completed!")
                    pygame.mixer.quit()
                    return True
                    
                except Exception as e:
                    print(f"❌ Audio playback failed: {e}")
                    return False
            else:
                print("❌ No audio data received")
                return False
        else:
            print(f"❌ TTS failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False


def test_basic_pygame_audio():
    """Test basic pygame audio functionality."""
    print("\n🔊 Testing Basic Audio")
    print("=" * 30)
    
    try:
        import pygame
        import numpy as np
        
        # Initialize pygame mixer
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Generate a simple test tone
        duration = 1.0  # seconds
        sample_rate = 22050
        frequency = 440  # A4 note
        
        # Generate sine wave
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2))
        
        for i in range(frames):
            wave = np.sin(2 * np.pi * frequency * i / sample_rate)
            arr[i][0] = wave * 0.1  # Left channel
            arr[i][1] = wave * 0.1  # Right channel
        
        # Convert to pygame sound
        sound = pygame.sndarray.make_sound((arr * 32767).astype(np.int16))
        
        print("🔊 Playing test tone...")
        sound.play()
        
        # Wait for playback
        import time
        while pygame.mixer.get_busy():
            time.sleep(0.1)
        
        pygame.mixer.quit()
        print("✅ Basic audio test completed!")
        return True
        
    except ImportError:
        print("❌ numpy not available for audio test")
        return False
    except Exception as e:
        print(f"❌ Basic audio test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🎪 Simple Orik Audio Test")
    print("=" * 40)
    
    # Test basic audio first
    print("Step 1: Testing basic audio system...")
    if not test_basic_pygame_audio():
        print("⚠️ Basic audio test failed, but continuing...")
    
    # Test TTS
    print("\nStep 2: Testing Text-to-Speech...")
    if test_tts_mcp_tool():
        print("\n🎉 SUCCESS: You should have heard Orik's voice!")
        print("If you didn't hear anything, check your system volume.")
        return True
    else:
        print("\n💥 FAILED: TTS audio test failed")
        print("\nTroubleshooting:")
        print("1. Check AWS credentials: aws configure list")
        print("2. Check system volume")
        print("3. Try: python3 -c \"import pygame; pygame.mixer.init(); print('Audio OK')\"")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)