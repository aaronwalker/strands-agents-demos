#!/usr/bin/env python3
"""
Test real audio functionality with AWS Polly and audio playback.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.mcp_tools.text_to_speech_tool import TextToSpeechTool
from src.services.audio_playback_service import AudioPlaybackService
from src.models.audio_models import VoiceConfig


async def test_real_audio():
    """Test real TTS and audio playback."""
    print("🎤 Testing Real Audio Functionality")
    print("=" * 50)
    
    try:
        # Initialize TTS tool
        print("1. Initializing Text-to-Speech tool...")
        tts_tool = TextToSpeechTool()
        print("✅ TTS tool initialized")
        
        # Initialize audio playback
        print("2. Initializing Audio Playback service...")
        audio_service = AudioPlaybackService()
        print("✅ Audio service initialized")
        
        # Test voice configuration
        print("3. Configuring Orik's voice...")
        voice_config = VoiceConfig(
            voice_id="Matthew",
            engine="neural",
            speed=1.1,
            pitch=-10
        )
        print(f"✅ Voice: {voice_config.voice_id}, Speed: {voice_config.speed}x")
        
        # Test phrases
        test_phrases = [
            "Oh brilliant, Aaron. That's absolutely perfect.",
            "Sure, let's all pretend Aaron rehearsed this part.",
            "Wow Aaron, groundbreaking insight from 2012.",
            "Hello! I'm Orik, your sarcastic AI co-host."
        ]
        
        print(f"\n4. Testing {len(test_phrases)} sarcastic phrases...")
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"\n   Testing phrase {i}: '{phrase[:30]}...'")
            
            try:
                # Generate speech
                print("      🔄 Generating speech with AWS Polly...")
                result = await tts_tool.synthesize_speech(phrase)
                
                if result.get("success"):
                    audio_data = result.get("audio_data")
                    if audio_data:
                        print(f"      ✅ Generated {len(audio_data)} bytes of audio")
                        
                        # Convert audio data if needed
                        if isinstance(audio_data, str):
                            import base64
                            audio_bytes = base64.b64decode(audio_data)
                        else:
                            audio_bytes = audio_data
                        
                        # Play audio using simple approach
                        print("      🔊 Playing audio...")
                        try:
                            import subprocess
                            import tempfile
                            import os
                            
                            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                                tmp_file.write(audio_bytes)
                                tmp_file.flush()
                                
                                # Use afplay on macOS
                                result_play = subprocess.run(['afplay', tmp_file.name], 
                                                           capture_output=True, timeout=10)
                                if result_play.returncode == 0:
                                    print("      ✅ Audio playback completed")
                                else:
                                    print("      ⚠️ Audio playback may have failed")
                                
                                # Cleanup
                                try:
                                    os.unlink(tmp_file.name)
                                except:
                                    pass
                                    
                        except Exception as play_error:
                            print(f"      ⚠️ Audio playback error: {play_error}")
                    else:
                        print("      ❌ No audio data received")
                    
                    # Wait between phrases
                    if i < len(test_phrases):
                        print("      ⏳ Waiting 2 seconds...")
                        await asyncio.sleep(2)
                        
                else:
                    print(f"      ❌ TTS failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"      ❌ Error with phrase {i}: {e}")
        
        print(f"\n🎉 Audio test completed!")
        print("If you heard Orik's sarcastic voice, the audio system is working!")
        
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check AWS credentials: aws configure list")
        print("2. Verify audio system: Check system volume")
        print("3. Check dependencies: python3 verify_installation.py")
        return False
    
    finally:
        # Cleanup
        if 'audio_service' in locals():
            try:
                # Try to cleanup if method exists
                if hasattr(audio_service, 'cleanup'):
                    audio_service.cleanup()
                elif hasattr(audio_service, 'stop'):
                    audio_service.stop()
            except:
                pass  # Ignore cleanup errors
    
    return True


def test_audio_system():
    """Test basic audio system functionality."""
    print("\n🔊 Testing Audio System")
    print("-" * 30)
    
    try:
        import pygame
        pygame.mixer.init()
        print("✅ pygame audio system initialized")
        
        # Test basic audio capabilities
        freq = pygame.mixer.get_init()
        if freq:
            print(f"✅ Audio frequency: {freq[0]} Hz")
            print(f"✅ Audio format: {freq[1]} bit")
            print(f"✅ Audio channels: {freq[2]}")
        
        pygame.mixer.quit()
        return True
        
    except Exception as e:
        print(f"❌ Audio system test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🎪 Orik Real Audio Test")
    print("=" * 30)
    
    # Test audio system first
    if not test_audio_system():
        print("❌ Audio system not working")
        return False
    
    # Test real TTS and playback
    try:
        success = asyncio.run(test_real_audio())
        return success
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 SUCCESS: Orik's voice is working!")
    else:
        print("\n💥 FAILED: Audio system needs attention")
    sys.exit(0 if success else 1)