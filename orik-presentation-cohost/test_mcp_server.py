#!/usr/bin/env python3
"""Test script for SpeakerNotesTool MCP server functionality."""

import asyncio
import json
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from mcp_tools.speaker_notes_tool import SpeakerNotesTool


async def test_speaker_notes_tool():
    """Test the SpeakerNotesTool functionality."""
    print("Testing SpeakerNotesTool MCP server...")
    
    tool = SpeakerNotesTool()
    
    # Test 1: Get current slide notes (will likely fail without PowerPoint running)
    print("\n1. Testing get_current_slide_notes()...")
    try:
        result = await tool.get_current_slide_notes()
        print(f"Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Expected error (PowerPoint not running): {e}")
    
    # Test 2: Extract notes from specific slide (will also fail without PowerPoint)
    print("\n2. Testing extract_speaker_notes() with slide index 0...")
    try:
        result = await tool.extract_speaker_notes(0, "test.pptx")
        print(f"Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Expected error (PowerPoint not running): {e}")
    
    print("\n3. Testing Orik tag extraction with mock data...")
    
    # Create a mock slide data to test tag extraction
    from models.slide_data import SlideData
    from models.orik_content import OrikContent
    from datetime import datetime
    
    # Test various Orik tag patterns
    test_cases = [
        {
            "name": "Single Orik tag",
            "notes": "[Orik] Aaron is about to make another brilliant observation"
        },
        {
            "name": "Multiple Orik tags",
            "notes": "[Orik] First sarcastic comment [Orik] Second witty remark"
        },
        {
            "name": "Case insensitive tags",
            "notes": "[orik] lowercase [ORIK] uppercase [Orik] mixed case"
        },
        {
            "name": "Tags with newlines",
            "notes": "[Orik] This comment spans\nmultiple lines\n[Orik] Another comment"
        },
        {
            "name": "Empty tag",
            "notes": "Some notes [Orik]   "
        },
        {
            "name": "No Orik tags",
            "notes": "Regular speaker notes without any special tags"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n   Test {i+1}: {test_case['name']}")
        
        slide_data = SlideData(
            slide_index=i,
            slide_title=f"Test Slide {i+1}",
            speaker_notes=test_case['notes'],
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        orik_content = OrikContent.extract_from_notes(slide_data)
        
        print(f"   Speaker notes: {repr(test_case['notes'])}")
        print(f"   Has Orik tags: {orik_content.has_orik_tags}")
        print(f"   Tag count: {orik_content.tag_count}")
        print(f"   Extracted tags: {orik_content.extracted_tags}")
        
        if orik_content.has_orik_tags:
            print(f"   Combined content: {repr(orik_content.get_combined_content())}")
    
    print("\n✅ SpeakerNotesTool testing completed!")
    print("\nTo test with actual PowerPoint:")
    print("1. Open Microsoft PowerPoint")
    print("2. Create a presentation with speaker notes containing [Orik] tags")
    print("3. Run this script again")


if __name__ == "__main__":
    asyncio.run(test_speaker_notes_tool())