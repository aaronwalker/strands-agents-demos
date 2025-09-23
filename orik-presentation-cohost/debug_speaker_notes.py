#!/usr/bin/env python3
"""
Debug speaker notes extraction from PowerPoint.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.mcp_tools.speaker_notes_tool import SpeakerNotesTool


async def debug_speaker_notes():
    """Debug speaker notes extraction."""
    print("🔍 Debugging Speaker Notes Extraction")
    print("=" * 50)
    
    tool = SpeakerNotesTool()
    
    # Test 1: Get current slide notes
    print("1. Testing get_current_slide_notes()...")
    try:
        result = await tool.get_current_slide_notes()
        print(f"Result: {result}")
        
        if result.get('success'):
            slide_data = result.get('slide_data', {})
            print(f"   Slide Index: {slide_data.get('slide_index')}")
            print(f"   Slide Title: {slide_data.get('slide_title')}")
            print(f"   Speaker Notes: '{slide_data.get('speaker_notes')}'")
            print(f"   Notes Length: {len(slide_data.get('speaker_notes', ''))}")
            
            orik_content = result.get('orik_content', {})
            print(f"   Has Orik Tags: {orik_content.get('has_orik_tags')}")
            print(f"   Tag Count: {orik_content.get('tag_count')}")
            print(f"   Extracted Tags: {orik_content.get('extracted_tags')}")
        else:
            print(f"   Error: {result.get('error')}")
            
    except Exception as e:
        print(f"   Exception: {e}")
    
    print()
    
    # Test 2: Try specific slide indices
    for slide_idx in range(5):
        print(f"2.{slide_idx + 1} Testing extract_speaker_notes(slide_index={slide_idx})...")
        try:
            result = await tool.extract_speaker_notes(slide_idx, "current_presentation")
            
            if result.get('success'):
                slide_data = result.get('slide_data', {})
                notes = slide_data.get('speaker_notes', '')
                print(f"   Slide {slide_idx}: '{notes[:100]}...' ({len(notes)} chars)")
                
                orik_content = result.get('orik_content', {})
                if orik_content.get('has_orik_tags'):
                    print(f"   🎯 FOUND ORIK TAGS: {orik_content.get('extracted_tags')}")
                else:
                    print(f"   No Orik tags found")
            else:
                print(f"   Error: {result.get('error')}")
                
        except Exception as e:
            print(f"   Exception: {e}")
    
    print()
    
    # Test 3: Test the AppleScript directly
    print("3. Testing AppleScript directly...")
    try:
        import applescript
        
        # Test if PowerPoint is running
        script = '''
        tell application "System Events"
            return name of every process whose name contains "PowerPoint"
        end tell
        '''
        
        result = applescript.run(script)
        print(f"   PowerPoint processes: {result}")
        
        # Test getting presentation info
        script = '''
        tell application "Microsoft PowerPoint"
            if (count of presentations) > 0 then
                set currentPres to presentation 1
                set slideCount to count of slides of currentPres
                return "Presentation has " & slideCount & " slides"
            else
                return "No presentations open"
            end if
        end tell
        '''
        
        result = applescript.run(script)
        print(f"   Presentation info: {result}")
        
        # Test getting current slide
        script = '''
        tell application "Microsoft PowerPoint"
            if (count of presentations) > 0 then
                set currentPres to presentation 1
                set currentSlideIndex to slide index of slide show view of slide show window 1
                return currentSlideIndex
            else
                return "No presentation"
            end if
        end tell
        '''
        
        try:
            result = applescript.run(script)
            print(f"   Current slide index: {result}")
        except Exception as e:
            print(f"   Current slide error: {e}")
        
        # Test getting speaker notes for current slide
        script = '''
        tell application "Microsoft PowerPoint"
            if (count of presentations) > 0 then
                set currentPres to presentation 1
                try
                    set currentSlideIndex to slide index of slide show view of slide show window 1
                    set currentSlide to slide currentSlideIndex of currentPres
                    set notesText to content of text range of text frame of notes page of currentSlide
                    return notesText
                on error
                    return "Error getting notes"
                end try
            else
                return "No presentation"
            end if
        end tell
        '''
        
        try:
            result = applescript.run(script)
            print(f"   Speaker notes: '{result}'")
            print(f"   Notes length: {len(str(result))}")
            
            # Check for Orik tags
            if '[Orik]' in str(result) or '[orik]' in str(result).lower():
                print(f"   🎯 ORIK TAGS DETECTED in raw AppleScript result!")
            else:
                print(f"   No Orik tags in raw result")
                
        except Exception as e:
            print(f"   Speaker notes error: {e}")
            
    except ImportError:
        print("   AppleScript not available")
    except Exception as e:
        print(f"   AppleScript error: {e}")


if __name__ == "__main__":
    print("🔍 Speaker Notes Debug Tool")
    print("Make sure PowerPoint is open with your presentation!")
    print("Navigate to a slide with [Orik] tags in the speaker notes.")
    print()
    
    asyncio.run(debug_speaker_notes())