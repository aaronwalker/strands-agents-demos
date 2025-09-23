#!/usr/bin/env python3
"""
Test the refactored Orik Personality Agent as a proper Strands agent.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.agents.orik_personality_agent import OrikPersonalityAgent
from src.models.slide_data import SlideData
from datetime import datetime


async def test_strands_orik_agent():
    """Test the Orik agent using its Strands agent tools."""
    print("🎭 Testing Orik as a Proper Strands Agent")
    print("=" * 50)
    
    # Initialize the Strands agent
    orik = OrikPersonalityAgent()
    
    print(f"Agent Name: {orik.name}")
    print(f"Agent Description: {orik.description}")
    print()
    
    # Test 1: Check initial mood
    print("1. Testing get_current_mood tool...")
    mood = orik.get_current_mood()
    print(f"   Mood: {mood['mood']}")
    print(f"   Description: {mood['description']}")
    print(f"   Activity: {mood['recent_activity']} recent responses")
    print()
    
    # Test 2: Generate responses using different tools
    print("2. Testing respond_to_tag tool...")
    tag_response = await orik.respond_to_tag(
        tag_content="Aaron is about to explain this complex concept",
        slide_context="Building Cloud-Native AI Agents"
    )
    if tag_response.get('success'):
        print(f"   Orik: \"{tag_response['response_text']}\"")
        print(f"   Model: {tag_response.get('model_used', 'unknown')}")
    print()
    
    # Test 3: Generate random dig
    print("3. Testing generate_random_dig tool...")
    dig_response = await orik.generate_random_dig(
        slide_title="Technical Architecture Overview",
        slide_index=2
    )
    if dig_response.get('success'):
        print(f"   Orik: \"{dig_response['response_text']}\"")
        print(f"   Type: {dig_response.get('response_type', 'unknown')}")
    print()
    
    # Test 4: Analyze slide content
    print("4. Testing analyze_slide_content tool...")
    analysis_response = await orik.analyze_slide_content(
        slide_title="AWS Lambda Functions",
        slide_content="Serverless computing with automatic scaling",
        speaker_notes="This slide covers the basics of Lambda functions"
    )
    if analysis_response.get('success'):
        print(f"   Orik: \"{analysis_response['response_text']}\"")
        print(f"   Analysis type: {analysis_response.get('response_type', 'unknown')}")
    print()
    
    # Test 5: Check conversation history
    print("5. Testing get_conversation_history tool...")
    history = orik.get_conversation_history()
    print(f"   Conversation entries: {len(history)}")
    for i, entry in enumerate(history[-2:], 1):  # Show last 2
        print(f"   Entry {i}: {entry['context'][:40]}...")
        print(f"            Response: {entry['response'][:50]}...")
    print()
    
    # Test 6: Check personality stats
    print("6. Testing get_personality_stats tool...")
    stats = orik.get_personality_stats()
    print(f"   Total responses: {stats['total_responses']}")
    print(f"   Response types: {stats.get('response_types', {})}")
    print(f"   Bedrock available: {stats.get('bedrock_available', False)}")
    print(f"   Strands agent: {stats.get('strands_agent', False)}")
    print(f"   Sarcasm level: {stats['personality_traits']['sarcasm_level']}")
    print()
    
    # Test 7: Adjust personality
    print("7. Testing adjust_personality tool...")
    adjustment = orik.adjust_personality(
        sarcasm_level=0.9,
        aaron_dig_probability=0.6
    )
    print(f"   Changes made: {adjustment['changes_made']}")
    print(f"   New sarcasm level: {adjustment['current_personality']['sarcasm_level']}")
    print()
    
    # Test 8: Check mood after interactions
    print("8. Testing mood after interactions...")
    final_mood = orik.get_current_mood()
    print(f"   Final mood: {final_mood['mood']}")
    print(f"   Description: {final_mood['description']}")
    print(f"   Total responses: {final_mood['total_responses']}")
    print()
    
    # Test 9: Generate one more response with adjusted personality
    print("9. Testing response with adjusted personality...")
    final_response = await orik.respond_to_tag(
        tag_content="Let's see if this demo actually works",
        slide_context="Live Demo Section"
    )
    if final_response.get('success'):
        print(f"   Orik (adjusted): \"{final_response['response_text']}\"")
        print(f"   Confidence: {final_response.get('confidence', 0.0):.2f}")
    print()
    
    # Test 10: Clear history
    print("10. Testing clear_conversation_history tool...")
    clear_result = orik.clear_conversation_history()
    print(f"    Result: {clear_result}")
    
    final_history = orik.get_conversation_history()
    print(f"    History after clear: {len(final_history)} entries")
    
    print("\n🎉 Strands Agent Testing Complete!")
    print("\n📊 Agent Capabilities Demonstrated:")
    print("   ✅ Tool-based architecture")
    print("   ✅ Personality management")
    print("   ✅ Conversation tracking")
    print("   ✅ Dynamic response generation")
    print("   ✅ Mood and state management")
    print("   ✅ Configurable behavior")


async def test_agent_integration():
    """Test how the agent integrates with presentation workflow."""
    print("\n" + "="*50)
    print("🎪 Testing Presentation Integration")
    print("="*50)
    
    orik = OrikPersonalityAgent()
    
    # Simulate a presentation workflow
    presentation_slides = [
        {
            "title": "Introduction",
            "notes": "[Orik] Welcome everyone to this presentation",
            "has_tags": True
        },
        {
            "title": "Technical Overview", 
            "notes": "This slide covers our architecture",
            "has_tags": False
        },
        {
            "title": "Demo Time",
            "notes": "[Orik] Let's see if this actually works",
            "has_tags": True
        },
        {
            "title": "Conclusion",
            "notes": "Thank you for your attention",
            "has_tags": False
        }
    ]
    
    print("Simulating presentation workflow...")
    
    for i, slide in enumerate(presentation_slides):
        print(f"\nSlide {i+1}: {slide['title']}")
        
        if slide['has_tags']:
            # Extract the tag content (simplified)
            tag_content = slide['notes'].replace('[Orik]', '').strip()
            response = await orik.respond_to_tag(tag_content, slide['title'])
        else:
            # Generate random dig
            response = await orik.generate_random_dig(slide['title'], i)
        
        if response.get('success'):
            print(f"   🎭 Orik: \"{response['response_text']}\"")
        
        # Brief pause between slides
        await asyncio.sleep(0.5)
    
    # Show final stats
    print(f"\n📈 Presentation Summary:")
    stats = orik.get_personality_stats()
    mood = orik.get_current_mood()
    
    print(f"   Total responses: {stats['total_responses']}")
    print(f"   Final mood: {mood['mood']} - {mood['description']}")
    print(f"   Response types: {stats.get('response_types', {})}")


if __name__ == "__main__":
    print("🎭 Strands Agent Orik Test")
    print("Testing Orik as a proper Strands agent with tools")
    print()
    
    try:
        asyncio.run(test_strands_orik_agent())
        asyncio.run(test_agent_integration())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()