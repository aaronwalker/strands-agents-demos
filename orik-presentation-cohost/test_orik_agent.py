#!/usr/bin/env python3
"""
Test the Orik Personality Agent with Bedrock.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.agents.orik_personality_agent import OrikPersonalityAgent
from src.models.slide_data import SlideData
from datetime import datetime


async def test_orik_agent():
    """Test the Orik personality agent with various scenarios."""
    print("🎭 Testing Orik Personality Agent with Bedrock")
    print("=" * 50)
    
    agent = OrikPersonalityAgent()
    
    # Test scenarios
    test_cases = [
        {
            "context": "Aaron is about to explain this complex concept",
            "type": "tagged",
            "description": "Custom [Orik] tag response"
        },
        {
            "context": "Let's see if this demo actually works",
            "type": "tagged", 
            "description": "Demo-related sarcasm"
        },
        {
            "context": "This is where Aaron usually loses everyone",
            "type": "tagged",
            "description": "Presentation skills dig"
        },
        {
            "context": "Technical Architecture Overview",
            "type": "random",
            "description": "Random dig at slide topic"
        },
        {
            "context": "AWS Lambda Functions",
            "type": "contextual",
            "description": "Contextual technical response"
        }
    ]
    
    # Create sample slide data
    slide_data = SlideData(
        slide_index=2,
        slide_title="Building Cloud-Native AI Agents",
        speaker_notes="[Orik] Aaron is about to explain this complex concept",
        presentation_path="test_presentation.pptx",
        timestamp=datetime.now()
    )
    
    print("🤖 Testing AI-generated responses...")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Context: '{test_case['context']}'")
        print(f"Type: {test_case['type']}")
        
        try:
            # Generate response
            result = await agent.generate_response(
                context=test_case['context'],
                slide_data=slide_data,
                response_type=test_case['type']
            )
            
            if result.get('success'):
                response = result['response_text']
                model = result.get('model_used', 'unknown')
                confidence = result.get('confidence', 0.0)
                
                print(f"😏 Orik: \"{response}\"")
                print(f"📊 Model: {model}, Confidence: {confidence:.2f}")
                
                # Check if it's a dynamic response (not templated)
                if model == "bedrock":
                    print("✨ Dynamic AI response!")
                else:
                    print("⚠️ Fallback response")
                    
            else:
                print("❌ Failed to generate response")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)
        
        # Wait between tests
        await asyncio.sleep(1)
    
    # Show conversation history
    print("\n📚 Conversation History:")
    history = agent.get_conversation_history()
    for entry in history[-3:]:  # Show last 3
        print(f"  Context: {entry['context'][:40]}...")
        print(f"  Response: {entry['response']}")
        print(f"  Type: {entry['type']}")
        print()
    
    # Show personality stats
    print("📊 Personality Statistics:")
    stats = agent.get_personality_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n🎉 Orik Agent testing complete!")


if __name__ == "__main__":
    print("🎭 Orik Personality Agent Test")
    print("This will test Orik's AI-powered responses using AWS Bedrock")
    print("Make sure you have AWS credentials configured!")
    print()
    
    try:
        asyncio.run(test_orik_agent())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check AWS credentials: aws configure list")
        print("2. Verify Bedrock access in your AWS region")
        print("3. Ensure boto3 is installed: pip install boto3")