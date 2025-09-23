#!/usr/bin/env python3
"""
Simple test of AI-powered Orik responses.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.agents.orik_personality_agent import OrikPersonalityAgent


async def test_ai_responses():
    """Test AI-powered responses with rate limiting."""
    print("🤖 Testing AI-Powered Orik Responses")
    print("=" * 40)
    
    orik = OrikPersonalityAgent(region_name="eu-central-1")
    
    # Test with your actual [Orik] tags
    test_cases = [
        ("Introduce yourself", "tagged"),
        ("Aaron is about to explain this complex concept", "tagged"),
        ("Let's see if this demo actually works", "tagged"),
        ("AWS Lambda presentation", "random")
    ]
    
    for i, (context, resp_type) in enumerate(test_cases, 1):
        print(f"\nTest {i}: {resp_type.title()} Response")
        print(f"Context: '{context}'")
        
        try:
            result = await orik.generate_response(context, response_type=resp_type)
            
            if result.get('success'):
                response = result['response_text']
                model = result.get('model_used', 'unknown')
                confidence = result.get('confidence', 0.0)
                
                print(f"🎭 Orik: \"{response}\"")
                print(f"📊 Model: {model}, Confidence: {confidence:.2f}")
                
                if model == "bedrock":
                    print("✨ Real AI response!")
                else:
                    print("⚡ Smart fallback response")
            else:
                print("❌ Failed to generate response")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Wait between requests to avoid throttling
        if i < len(test_cases):
            print("⏳ Waiting to avoid rate limits...")
            await asyncio.sleep(3)
    
    # Show final stats
    print(f"\n📈 Session Summary:")
    stats = orik.get_personality_stats()
    mood = orik.get_current_mood()
    
    print(f"Total responses: {stats['total_responses']}")
    print(f"Bedrock available: {stats['bedrock_available']}")
    print(f"Current mood: {mood['mood']} - {mood['description']}")


if __name__ == "__main__":
    print("🎭 AI-Powered Orik Test")
    print("Testing with eu-central-1 region")
    print()
    
    try:
        asyncio.run(test_ai_responses())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
    except Exception as e:
        print(f"❌ Test failed: {e}")