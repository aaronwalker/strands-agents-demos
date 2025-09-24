#!/usr/bin/env python3
"""
Test slide content extraction.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.mcp_tools.speaker_notes_tool import SpeakerNotesTool


async def test_slide_content():
    """Test slide content extraction."""
    print("📊 Testing Slide Content Extraction")
    print("=" * 40)
    
    tool = SpeakerNotesTool()
    
    # Test current slide
    print("1. Testing current slide with content extraction...")
    try:
        result = await tool.get_current_slide_notes()
        
        if result.get('success'):
            slide_data = result.get('slide_data', {})
            print(f"   Slide Index: {slide_data.get('slide_index')}")
            print(f"   Slide Title: '{slide_data.get('slide_title')}'")
            print(f"   Slide Content: '{slide_data.get('slide_content', 'N/A')[:100]}...'")
            print(f"   Speaker Notes: '{slide_data.get('speaker_notes', 'N/A')[:100]}...'")
            
            # Check if we have content
            has_content = slide_data.get('slide_content') and slide_data.get('slide_content') != ""
            print(f"   Has Slide Content: {has_content}")
            
            if has_content:
                print("   ✅ Slide content extraction working!")
            else:
                print("   ⚠️ No slide content extracted")
                
        else:
            print(f"   Error: {result.get('error')}")
            
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n2. Testing specific slides...")
    for slide_idx in [0, 1, 2]:
        try:
            result = await tool.extract_speaker_notes(slide_idx, "current")
            
            if result.get('success'):
                slide_data = result.get('slide_data', {})
                title = slide_data.get('slide_title', 'Unknown')
                content = slide_data.get('slide_content', '')
                notes = slide_data.get('speaker_notes', '')
                
                print(f"   Slide {slide_idx}: '{title}'")
                print(f"      Content: '{content[:80]}...' ({len(content)} chars)")
                print(f"      Notes: '{notes[:50]}...' ({len(notes)} chars)")
                
                # Check for Orik tags
                orik_content = result.get('orik_content', {})
                if orik_content.get('has_orik_tags'):
                    print(f"      🎯 Orik tags: {orik_content.get('extracted_tags')}")
                
            else:
                print(f"   Slide {slide_idx}: Error - {result.get('error')}")
                
        except Exception as e:
            print(f"   Slide {slide_idx}: Exception - {e}")


if __name__ == "__main__":
    print("📊 Slide Content Extraction Test")
    print("Make sure PowerPoint is open!")
    print()
    
    asyncio.run(test_slide_content())