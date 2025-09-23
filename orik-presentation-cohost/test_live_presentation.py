#!/usr/bin/env python3
"""
Test Orik with live PowerPoint presentation.
This script will monitor your actual PowerPoint and respond to [Orik] tags.
"""

import sys
import asyncio
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.mcp_tools.speaker_notes_tool import SpeakerNotesTool
from src.mcp_tools.text_to_speech_tool import TextToSpeechTool
from src.mcp_tools.dig_at_aaron_tool import DigAtAaronTool
from src.ui.orik_avatar_ui import OrikAvatarUI, WindowConfig
from src.agents.orik_personality_agent import OrikPersonalityAgent


class LiveOrikDemo:
    """Live demonstration of Orik with real PowerPoint."""
    
    def __init__(self):
        self.speaker_notes_tool = SpeakerNotesTool()
        self.tts_tool = TextToSpeechTool()
        self.dig_tool = DigAtAaronTool()
        self.orik_agent = OrikPersonalityAgent()  # New Bedrock-powered agent
        self.avatar_ui = None
        self.running = False
        self.last_slide_index = -1
        
    def setup_avatar(self):
        """Set up the Orik avatar UI."""
        print("🎭 Setting up Orik Avatar...")
        
        config = WindowConfig(
            width=350,
            height=450,
            x_position=50,
            y_position=50,
            title="Orik - Live Demo"
        )
        
        self.avatar_ui = OrikAvatarUI(config)
        self.avatar_ui.show_avatar()
        self.avatar_ui.update_status("Ready to monitor PowerPoint...")
        print("✅ Orik avatar is ready!")
        
    async def play_audio(self, audio_data):
        """Play audio using the working method."""
        try:
            if isinstance(audio_data, str):
                import base64
                audio_bytes = base64.b64decode(audio_data)
            else:
                audio_bytes = audio_data
            
            import tempfile
            import subprocess
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_file.flush()
                
                # Play with afplay
                result = subprocess.run(['afplay', tmp_file.name], 
                                      capture_output=True, timeout=15)
                
                # Cleanup
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass
                    
                return result.returncode == 0
                
        except Exception as e:
            print(f"Audio playback error: {e}")
            return False
    
    async def process_slide_change(self, slide_data):
        """Process a slide change and generate Orik's response."""
        slide_index = slide_data.get('slide_index', 0)
        slide_title = slide_data.get('slide_title', 'Unknown')
        speaker_notes = slide_data.get('speaker_notes', '')
        
        print(f"\n📊 Slide {slide_index + 1}: {slide_title}")
        
        if self.avatar_ui:
            self.avatar_ui.update_status(f"Processing slide {slide_index + 1}: {slide_title}")
            self.avatar_ui.update()
        
        # Check for [Orik] tags
        orik_content = slide_data.get('orik_content', {})
        has_tags = orik_content.get('has_orik_tags', False)
        extracted_tags = orik_content.get('extracted_tags', [])
        
        response_text = None
        
        if has_tags and extracted_tags:
            print(f"🎯 Found {len(extracted_tags)} [Orik] tag(s)!")
            for i, tag in enumerate(extracted_tags, 1):
                print(f"   Tag {i}: {tag[:50]}...")
            
            # Use the first tag as context for AI-generated response
            context = extracted_tags[0]
            print("🤖 Generating AI response with Bedrock...")
            
            try:
                # Create slide data for context
                from src.models.slide_data import SlideData
                slide_context = SlideData(
                    slide_index=slide_index,
                    slide_title=slide_title,
                    speaker_notes=speaker_notes,
                    presentation_path="live_presentation",
                    timestamp=datetime.now()
                )
                
                # Generate dynamic response using Bedrock
                response_result = await self.orik_agent.generate_response(
                    context=context,
                    slide_data=slide_context,
                    response_type="tagged"
                )
                
                if response_result.get('success'):
                    response_text = response_result['response_text']
                    model_used = response_result.get('model_used', 'unknown')
                    confidence = response_result.get('confidence', 0.0)
                    print(f"✨ AI Response generated (model: {model_used}, confidence: {confidence:.2f})")
                else:
                    response_text = f"Oh {context}? How... groundbreaking, Aaron."
                    print("⚠️ AI generation failed, using fallback")
                    
            except Exception as e:
                print(f"❌ AI generation error: {e}")
                response_text = f"Oh {context}? How... groundbreaking, Aaron."
            
        else:
            print("🤔 No [Orik] tags found, generating random AI dig...")
            
            try:
                # Generate random sarcastic response using AI
                from src.models.slide_data import SlideData
                slide_context = SlideData(
                    slide_index=slide_index,
                    slide_title=slide_title,
                    speaker_notes=speaker_notes,
                    presentation_path="live_presentation",
                    timestamp=datetime.now()
                )
                
                response_result = await self.orik_agent.generate_response(
                    context=f"Slide about {slide_title}",
                    slide_data=slide_context,
                    response_type="random"
                )
                
                if response_result.get('success'):
                    response_text = response_result['response_text']
                    model_used = response_result.get('model_used', 'unknown')
                    print(f"✨ AI Random dig generated (model: {model_used})")
                else:
                    # Fallback to old dig tool
                    dig_result = await self.dig_tool.get_aaron_dig()
                    if dig_result.get('success'):
                        response_text = dig_result.get('dig', "Sure, Aaron. That's brilliant.")
                    else:
                        response_text = "Oh brilliant, Aaron. Just brilliant."
                    print("⚠️ Using fallback dig tool")
                    
            except Exception as e:
                print(f"❌ AI dig generation error: {e}")
                response_text = "Wow Aaron, groundbreaking insight."
        
        if response_text:
            print(f"😏 Orik says: \"{response_text}\"")
            
            if self.avatar_ui:
                self.avatar_ui.set_speaking_state(True)
                self.avatar_ui.update_status("Orik is speaking...")
                self.avatar_ui.update()
            
            # Generate and play speech
            try:
                print("🔄 Generating speech...")
                tts_result = await self.tts_tool.synthesize_speech(response_text)
                
                if tts_result.get('success'):
                    audio_data = tts_result.get('audio_data')
                    if audio_data:
                        print("🔊 Playing Orik's response...")
                        success = await self.play_audio(audio_data)
                        if success:
                            print("✅ Orik spoke successfully!")
                        else:
                            print("⚠️ Audio playback may have failed")
                    else:
                        print("❌ No audio data generated")
                else:
                    print(f"❌ TTS failed: {tts_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Speech generation failed: {e}")
            
            finally:
                if self.avatar_ui:
                    self.avatar_ui.set_speaking_state(False)
                    self.avatar_ui.update_status("Monitoring for next slide...")
                    self.avatar_ui.update()
    
    async def monitor_presentation(self):
        """Monitor PowerPoint for slide changes."""
        print("👀 Starting PowerPoint monitoring...")
        print("📝 Instructions:")
        print("   1. Make sure PowerPoint is open with your presentation")
        print("   2. Add [Orik] tags to speaker notes like:")
        print("      [Orik] Aaron is about to explain this concept")
        print("      [Orik] Let's see if this demo actually works")
        print("   3. Navigate through your slides")
        print("   4. Press Ctrl+C to stop monitoring")
        print()
        
        if self.avatar_ui:
            self.avatar_ui.update_status("Monitoring PowerPoint slides...")
            self.avatar_ui.update()
        
        self.running = True
        
        while self.running:
            try:
                # Get current slide notes
                result = await self.speaker_notes_tool.get_current_slide_notes()
                
                if result.get('success'):
                    slide_data = result.get('slide_data', {})
                    current_slide = slide_data.get('slide_index', 0)
                    
                    # Check if slide changed
                    if current_slide != self.last_slide_index:
                        print(f"\n🔄 Slide change detected: {self.last_slide_index + 1} → {current_slide + 1}")
                        self.last_slide_index = current_slide
                        
                        # Process the new slide
                        await self.process_slide_change(result)
                        
                        # Wait a bit before checking again
                        await asyncio.sleep(2)
                    else:
                        # No change, check again soon
                        await asyncio.sleep(1)
                        
                else:
                    error = result.get('error', 'Unknown error')
                    if 'PowerPoint not found' in error or 'No presentation' in error:
                        print("⚠️ PowerPoint not detected. Please open PowerPoint with a presentation.")
                        if self.avatar_ui:
                            self.avatar_ui.update_status("Waiting for PowerPoint...")
                            self.avatar_ui.update()
                    else:
                        print(f"⚠️ Monitoring error: {error}")
                    
                    await asyncio.sleep(3)
                    
            except KeyboardInterrupt:
                print("\n⚠️ Monitoring stopped by user")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                await asyncio.sleep(2)
    
    async def run_demo(self):
        """Run the live demo."""
        print("🎪 ORIK LIVE POWERPOINT DEMO")
        print("=" * 40)
        
        try:
            # Set up avatar
            self.setup_avatar()
            
            # Start monitoring
            await self.monitor_presentation()
            
        except KeyboardInterrupt:
            print("\n⚠️ Demo interrupted")
        except Exception as e:
            print(f"❌ Demo failed: {e}")
        finally:
            if self.avatar_ui:
                self.avatar_ui.destroy()
            print("✅ Demo cleanup completed")


async def main():
    """Main function."""
    demo = LiveOrikDemo()
    await demo.run_demo()


if __name__ == "__main__":
    print("🎭 Starting Orik Live PowerPoint Demo...")
    print("Make sure PowerPoint is open with your presentation!")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    print("🎪 Thanks for trying Orik!")