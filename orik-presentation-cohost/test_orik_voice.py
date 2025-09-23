#!/usr/bin/env python3
"""
Test Orik's voice using the actual TTS tool.
"""

import sys
import asyncio
import tempfile
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

async def test_orik_voice():
    """Test Orik's voice with real AWS Polly."""
    print("🎭 Testing Orik's Voice")
    print("=" * 30)
    
    try:
        from mcp_tools.text_to_speech_tool import TextToSpeechTool
        
        # Initialize the TTS tool
        print("1. Initializing TTS tool...")
        tts_tool = TextToSpeechTool()
        print("✅ TTS tool ready")
        
        # Test phrases
        test_phrases = [
            "Hello! I'm Orik, your sarcastic AI co-host.",
            "Oh brilliant, Aaron. That's absolutely perfect.",
            "Sure, let's all pretend Aaron rehearsed this part."
        ]
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"\n{i}. Testing: '{phrase[:40]}...'")
            
            try:
                # Use the tool's synthesize_speech method
                result = await tts_tool.synthesize_speech(phrase)
                
                if result.get("success"):
                    audio_data = result.get("audio_data")
                    if audio_data:
                        print(f"   ✅ Generated {len(audio_data)} bytes of audio")
                        
                        # Convert audio data if needed
                        if isinstance(audio_data, str):
                            import base64
                            audio_bytes = base64.b64decode(audio_data)
                        else:
                            audio_bytes = audio_data
                        
                        # Save to temporary file and play
                        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                            tmp_file.write(audio_bytes)
                            tmp_file.flush()
                            
                            print(f"   🔊 Playing audio...")
                            
                            # Try different audio players
                            audio_played = False
                            
                            # Try afplay (macOS)
                            if sys.platform == "darwin":
                                try:
                                    import subprocess
                                    result = subprocess.run(['afplay', tmp_file.name], 
                                                          capture_output=True, timeout=10)
                                    if result.returncode == 0:
                                        print("   ✅ Audio played with afplay")
                                        audio_played = True
                                except Exception as e:
                                    print(f"   ⚠️ afplay failed: {e}")
                            
                            # Try pygame as fallback
                            if not audio_played:
                                try:
                                    import pygame
                                    pygame.mixer.init()
                                    pygame.mixer.music.load(tmp_file.name)
                                    pygame.mixer.music.play()
                                    
                                    # Wait for playback
                                    while pygame.mixer.music.get_busy():
                                        await asyncio.sleep(0.1)
                                    
                                    pygame.mixer.quit()
                                    print("   ✅ Audio played with pygame")
                                    audio_played = True
                                except Exception as e:
                                    print(f"   ⚠️ pygame failed: {e}")
                            
                            # Cleanup
                            try:
                                os.unlink(tmp_file.name)
                            except:
                                pass
                            
                            if not audio_played:
                                print(f"   ⚠️ Could not play audio, but file was generated")
                                print(f"   💡 Try manually playing: {tmp_file.name}")
                    else:
                        print("   ❌ No audio data received")
                else:
                    error = result.get("error", "Unknown error")
                    print(f"   ❌ TTS failed: {error}")
                    
                # Wait between phrases
                if i < len(test_phrases):
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n🎉 Voice test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Voice test failed: {e}")
        
        # Provide troubleshooting info
        print("\n🔧 Troubleshooting:")
        print("1. Check AWS credentials:")
        print("   aws configure list")
        print("2. Test AWS Polly access:")
        print("   aws polly describe-voices --region us-east-1")
        print("3. Check audio system:")
        print("   System Preferences > Sound > Output")
        
        return False


def test_aws_connection():
    """Test AWS connection."""
    print("🔗 Testing AWS Connection")
    print("=" * 30)
    
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        # Test Polly connection
        polly = boto3.client('polly')
        voices = polly.describe_voices()
        
        print(f"✅ Connected to AWS Polly")
        print(f"✅ Found {len(voices['Voices'])} voices")
        
        # Check if Matthew voice is available
        matthew_voice = None
        for voice in voices['Voices']:
            if voice['Id'] == 'Matthew':
                matthew_voice = voice
                break
        
        if matthew_voice:
            print(f"✅ Matthew voice available: {matthew_voice['LanguageName']}")
        else:
            print("⚠️ Matthew voice not found, will use default")
        
        return True
        
    except NoCredentialsError:
        print("❌ AWS credentials not configured")
        print("Run: aws configure")
        return False
    except ClientError as e:
        print(f"❌ AWS client error: {e}")
        return False
    except Exception as e:
        print(f"❌ AWS connection failed: {e}")
        return False


def main():
    """Main test function."""
    print("🎪 Orik Voice Test")
    print("=" * 20)
    
    # Test AWS connection first
    if not test_aws_connection():
        print("\n💥 Cannot test voice without AWS connection")
        return False
    
    # Test Orik's voice
    try:
        success = asyncio.run(test_orik_voice())
        
        if success:
            print("\n🎉 SUCCESS!")
            print("If you heard Orik's sarcastic voice, the audio system is working!")
            print("If not, check your system volume and audio output device.")
        else:
            print("\n💥 FAILED!")
            
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)