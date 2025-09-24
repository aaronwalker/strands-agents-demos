#!/usr/bin/env python3
"""
Test that Orik agent properly uses slide content in responses.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.agents.orik_personality_agent import OrikPersonalityAgent
from src.models.slide_data import SlideData


async def test_slide_content_usage():
    """Test that slide content is properly used in Orik's responses."""
    print("🎭 Testing Slide Content Usage in Orik Responses")
    print("=" * 50)
    
    agent = OrikPersonalityAgent()
    
    # Test cases with different slide content
    test_cases = [
        {
            "name": "Bullet Points Slide",
            "slide_data": SlideData(
                slide_index=0,
                slide_title="Key Features",
                slide_content="• Feature 1: Amazing capability\n• Feature 2: Revolutionary approach\n• Feature 3: Groundbreaking innovation",
                speaker_notes="[Orik] This is going to be amazing",
                presentation_path="test.pptx",
                timestamp=datetime.now()
            ),
            "context": "This is going to be amazing",
            "response_type": "tagged"
        },
        {
            "name": "AWS Services Slide",
            "slide_data": SlideData(
                slide_index=1,
                slide_title="AWS Architecture",
                slide_content="Lambda functions connect to S3 buckets and EC2 instances for scalable cloud computing",
                speaker_notes="Let me explain our cloud architecture",
                presentation_path="test.pptx",
                timestamp=datetime.now()
            ),
            "context": "Let me explain our cloud architecture",
            "response_type": "tagged"
        },
        {
            "name": "AI/ML Slide",
            "slide_data": SlideData(
                slide_index=2,
                slide_title="Machine Learning Pipeline",
                slide_content="Our AI-powered machine learning model uses artificial intelligence to provide intelligent insights",
                speaker_notes="",
                presentation_path="test.pptx",
                timestamp=datetime.now()
            ),
            "context": "",
            "response_type": "random"
        },
        {
            "name": "Diagram Slide",
            "slide_data": SlideData(
                slide_index=3,
                slide_title="System Architecture",
                slide_content="[Diagram showing complex system architecture with multiple components and connections]",
                speaker_notes="",
                presentation_path="test.pptx",
                timestamp=datetime.now()
            ),
            "context": "System architecture overview",
            "response_type": "contextual"
        },
        {
            "name": "No Content Slide",
            "slide_data": SlideData(
                slide_index=4,
                slide_title="Thank You",
                slide_content="",
                speaker_notes="That's all for today",
                presentation_path="test.pptx",
                timestamp=datetime.now()
            ),
            "context": "That's all for today",
            "response_type": "tagged"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Slide Title: '{test_case['slide_data'].slide_title}'")
        print(f"   Slide Content: '{test_case['slide_data'].slide_content[:60]}{'...' if len(test_case['slide_data'].slide_content) > 60 else ''}'")
        print(f"   Context: '{test_case['context']}'")
        print(f"   Response Type: {test_case['response_type']}")
        
        try:
            result = await agent.generate_response(
                context=test_case['context'],
                slide_data=test_case['slide_data'],
                response_type=test_case['response_type']
            )
            
            if result.get('success'):
                response = result['response_text']
                model_used = result.get('model_used', 'unknown')
                
                print(f"   🎯 Orik: \"{response}\"")
                print(f"   📊 Model: {model_used}, Confidence: {result.get('confidence', 0)}")
                
                # Check if response seems to reference slide content
                slide_content_lower = test_case['slide_data'].slide_content.lower()
                response_lower = response.lower()
                
                content_referenced = False
                if slide_content_lower:
                    # Check for content-specific references
                    if 'bullet' in slide_content_lower and any(word in response_lower for word in ['bullet', 'point', 'list']):
                        content_referenced = True
                    elif any(word in slide_content_lower for word in ['aws', 'lambda', 's3', 'ec2']) and any(word in response_lower for word in ['aws', 'cloud', 'service']):
                        content_referenced = True
                    elif any(word in slide_content_lower for word in ['ai', 'machine learning', 'artificial']) and any(word in response_lower for word in ['ai', 'machine', 'artificial']):
                        content_referenced = True
                    elif 'diagram' in slide_content_lower and any(word in response_lower for word in ['diagram', 'chart', 'visual']):
                        content_referenced = True
                    elif test_case['slide_data'].slide_title.lower() in response_lower:
                        content_referenced = True
                
                if content_referenced:
                    print(f"   ✅ Response appears to reference slide content!")
                elif test_case['slide_data'].slide_content:
                    print(f"   ⚠️ Response doesn't seem to reference slide content")
                else:
                    print(f"   ℹ️ No slide content to reference")
                    
            else:
                print(f"   ❌ Failed to generate response: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")
    
    # Test the analyze_slide_content method specifically
    print(f"\n{len(test_cases) + 1}. Testing analyze_slide_content method:")
    try:
        result = await agent.analyze_slide_content(
            slide_title="AWS Lambda Functions",
            slide_content="Lambda functions are serverless compute services that run code without provisioning servers. They scale automatically and you only pay for compute time consumed.",
            speaker_notes="Let me explain how Lambda works"
        )
        
        if result.get('success'):
            print(f"   🎯 Orik: \"{result['response_text']}\"")
            print(f"   📊 Model: {result.get('model_used', 'unknown')}")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   💥 Exception: {e}")
    
    print(f"\n📈 Final Stats:")
    stats = agent.get_personality_stats()
    print(f"   Total Responses: {stats['total_responses']}")
    print(f"   Response Types: {stats['response_types']}")
    print(f"   Bedrock Available: {stats['bedrock_available']}")


if __name__ == "__main__":
    print("🧪 Slide Content Usage Test")
    print("Testing if Orik properly uses slide content in responses...")
    print()
    
    asyncio.run(test_slide_content_usage())