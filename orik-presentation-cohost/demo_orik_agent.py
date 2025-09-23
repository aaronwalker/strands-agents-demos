#!/usr/bin/env python3
"""
Demo script for the Orik Agent Controller.

This script demonstrates the core functionality of the Orik Agent Controller
without requiring actual presentation software or MCP servers.
"""

import asyncio
import logging
from datetime import datetime

from src.agent.orik_agent_controller import OrikAgentController, ResponseGenerator
from src.models.slide_data import SlideData
from src.models.orik_content import OrikContent
from src.models.personality import OrikPersonality
from src.models.enums import PresentationSoftware


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_response_generation():
    """Demonstrate Orik's response generation capabilities."""
    print("\n" + "="*60)
    print("ORIK AGENT CONTROLLER DEMO")
    print("="*60)
    
    # Create Orik's personality
    personality = OrikPersonality.create_default()
    print(f"\n🎭 Orik's Personality:")
    print(f"   Sarcasm Level: {personality.sarcasm_level}")
    print(f"   Interruption Frequency: {personality.interruption_frequency}")
    print(f"   Aaron Dig Probability: {personality.aaron_dig_probability}")
    
    # Create response generator
    generator = ResponseGenerator(personality)
    
    # Test scenarios
    test_slides = [
        {
            "title": "Introduction to AWS Lambda",
            "notes": "[Orik] Aaron is about to explain serverless computing",
            "description": "Tagged content - Orik should respond sarcastically"
        },
        {
            "title": "Performance Metrics",
            "notes": "Here are our latest performance improvements and benchmarks.",
            "description": "No tags - Orik might interrupt or stay silent"
        },
        {
            "title": "Security Best Practices", 
            "notes": "[Orik] This is where Aaron pretends to be a security expert",
            "description": "Another tagged response"
        },
        {
            "title": "Demo Time",
            "notes": "[Orik] Let's see if this actually works this time",
            "description": "Demo-related sarcasm"
        }
    ]
    
    print(f"\n🎤 Testing Orik's Responses:")
    print("-" * 40)
    
    for i, slide_info in enumerate(test_slides):
        print(f"\n📊 Slide {i+1}: {slide_info['title']}")
        print(f"   Notes: {slide_info['notes']}")
        print(f"   Scenario: {slide_info['description']}")
        
        # Create slide data
        slide_data = SlideData(
            slide_index=i,
            slide_title=slide_info['title'],
            speaker_notes=slide_info['notes'],
            presentation_path="demo.pptx",
            timestamp=datetime.now()
        )
        
        # Extract Orik content
        orik_content = OrikContent.extract_from_notes(slide_data)
        print(f"   Orik Tags Found: {orik_content.tag_count}")
        
        # Generate response
        response = await generator.generate_response(orik_content)
        
        # Display response
        if response.response_text == "[SILENT]":
            print(f"   🤐 Orik: *stays silent*")
        else:
            print(f"   😏 Orik: \"{response.response_text}\"")
        
        print(f"   📈 Confidence: {response.confidence:.2f}")
        print(f"   🏷️  Type: {response.response_type.value}")
        
        # Add to history
        generator.add_to_history(response)
    
    # Show conversation history
    print(f"\n📚 Conversation History:")
    print("-" * 30)
    history = generator.get_recent_responses(10)
    for i, response in enumerate(history):
        if response.response_text != "[SILENT]":
            print(f"   {i+1}. \"{response.response_text[:50]}...\" ({response.response_type.value})")


async def demo_agent_controller():
    """Demonstrate the full Orik Agent Controller (mocked)."""
    print(f"\n🤖 Orik Agent Controller Demo:")
    print("-" * 40)
    
    # Note: This will use mocked services since we don't have real presentation software
    try:
        # Mock the dependencies to avoid AppleScript requirement
        from unittest.mock import patch, MagicMock
        
        with patch('src.agent.orik_agent_controller.PresentationMonitor') as mock_monitor, \
             patch('src.agent.orik_agent_controller.AudioPlaybackService') as mock_audio:
            
            # Set up mocks
            mock_monitor_instance = MagicMock()
            mock_monitor.return_value = mock_monitor_instance
            
            mock_audio_instance = MagicMock()
            mock_audio.return_value = mock_audio_instance
            
            # Create controller
            controller = OrikAgentController()
            
            print(f"   ✅ Controller initialized")
            print(f"   📊 System Status: {controller.get_system_status().is_fully_operational}")
            
            # Test slide processing
            test_slide = SlideData(
                slide_index=0,
                slide_title="Demo Slide",
                speaker_notes="[Orik] Aaron is demonstrating the Orik system",
                presentation_path="demo.pptx",
                timestamp=datetime.now()
            )
            
            print(f"\n   📄 Processing test slide...")
            await controller.process_slide_change(test_slide)
            
            # Check recent responses
            recent = controller.get_recent_responses(1)
            if recent:
                response = recent[0]
                if response.response_text != "[SILENT]":
                    print(f"   😏 Orik responded: \"{response.response_text}\"")
                else:
                    print(f"   🤐 Orik stayed silent")
            
            # Test force response
            print(f"\n   🎯 Testing forced response...")
            forced_response = await controller.force_response("What do you think about this demo?")
            if forced_response.response_text != "[SILENT]":
                print(f"   😏 Orik: \"{forced_response.response_text}\"")
            
            print(f"   ✅ Demo completed successfully!")
            
    except Exception as e:
        print(f"   ❌ Demo error: {e}")
        logger.error(f"Demo error: {e}")


async def main():
    """Main demo function."""
    try:
        await demo_response_generation()
        await demo_agent_controller()
        
        print(f"\n🎉 Orik Agent Controller Demo Complete!")
        print(f"\nNext steps:")
        print(f"  1. Install py-applescript for PowerPoint integration")
        print(f"  2. Set up AWS credentials for Polly TTS")
        print(f"  3. Run MCP servers for full functionality")
        print(f"  4. Start a presentation and watch Orik in action!")
        
    except KeyboardInterrupt:
        print(f"\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())