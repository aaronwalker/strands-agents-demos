#!/usr/bin/env python3
"""
Test AppleScript directly to debug speaker notes.
"""

import subprocess
import sys


def test_applescript(script, description):
    """Test an AppleScript and show results."""
    print(f"\n🔍 Testing: {description}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Output: '{result.stdout.strip()}'")
        if result.stderr:
            print(f"Error: '{result.stderr.strip()}'")
            
        return result.stdout.strip()
        
    except Exception as e:
        print(f"Exception: {e}")
        return None


def main():
    """Test various AppleScript approaches."""
    print("🍎 AppleScript Direct Testing")
    print("=" * 40)
    
    # Test 1: Check if PowerPoint is running
    script1 = '''
    tell application "System Events"
        return (name of processes) contains "Microsoft PowerPoint"
    end tell
    '''
    test_applescript(script1, "PowerPoint running check")
    
    # Test 2: Get presentation count
    script2 = '''
    tell application "Microsoft PowerPoint"
        return count of presentations
    end tell
    '''
    test_applescript(script2, "Presentation count")
    
    # Test 3: Get slide count
    script3 = '''
    tell application "Microsoft PowerPoint"
        if (count of presentations) > 0 then
            return count of slides of presentation 1
        else
            return "No presentations"
        end if
    end tell
    '''
    test_applescript(script3, "Slide count")
    
    # Test 4: Get current slide (different approaches)
    script4a = '''
    tell application "Microsoft PowerPoint"
        if (count of presentations) > 0 then
            try
                return slide index of slide show view of slide show window 1
            on error
                return "Not in slideshow mode"
            end try
        else
            return "No presentations"
        end if
    end tell
    '''
    test_applescript(script4a, "Current slide (slideshow mode)")
    
    script4b = '''
    tell application "Microsoft PowerPoint"
        if (count of presentations) > 0 then
            try
                return slide index of slide range of selection of document window 1 of presentation 1
            on error
                return "No slide selected"
            end try
        else
            return "No presentations"
        end if
    end tell
    '''
    test_applescript(script4b, "Current slide (edit mode)")
    
    # Test 5: Get slide title (slide 1)
    script5 = '''
    tell application "Microsoft PowerPoint"
        if (count of presentations) > 0 then
            set pres to presentation 1
            if (count of slides of pres) > 0 then
                set currentSlide to slide 1 of pres
                try
                    return content of text range of text frame of shape 1 of currentSlide
                on error
                    return "No title found"
                end try
            else
                return "No slides"
            end if
        else
            return "No presentations"
        end if
    end tell
    '''
    test_applescript(script5, "Slide 1 title")
    
    # Test 6: Get speaker notes (slide 1) - original approach
    script6 = '''
    tell application "Microsoft PowerPoint"
        if (count of presentations) > 0 then
            set pres to presentation 1
            if (count of slides of pres) > 0 then
                set currentSlide to slide 1 of pres
                try
                    return content of text range of text frame of notes page of currentSlide
                on error errMsg
                    return "Notes error: " & errMsg
                end try
            else
                return "No slides"
            end if
        else
            return "No presentations"
        end if
    end tell
    '''
    test_applescript(script6, "Speaker notes (slide 1) - original")
    
    # Test 7: Get speaker notes (slide 1) - alternative approach
    script7 = '''
    tell application "Microsoft PowerPoint"
        if (count of presentations) > 0 then
            set pres to presentation 1
            if (count of slides of pres) > 0 then
                set currentSlide to slide 1 of pres
                try
                    set notesPage to notes page of currentSlide
                    if (count of shapes of notesPage) > 0 then
                        return content of text range of text frame of shape 1 of notesPage
                    else
                        return "No notes shapes"
                    end if
                on error errMsg
                    return "Notes error: " & errMsg
                end try
            else
                return "No slides"
            end if
        else
            return "No presentations"
        end if
    end tell
    '''
    test_applescript(script7, "Speaker notes (slide 1) - alternative")
    
    # Test 8: List all shapes on notes page
    script8 = '''
    tell application "Microsoft PowerPoint"
        if (count of presentations) > 0 then
            set pres to presentation 1
            if (count of slides of pres) > 0 then
                set currentSlide to slide 1 of pres
                try
                    set notesPage to notes page of currentSlide
                    set shapeCount to count of shapes of notesPage
                    return "Notes page has " & shapeCount & " shapes"
                on error errMsg
                    return "Shape count error: " & errMsg
                end try
            else
                return "No slides"
            end if
        else
            return "No presentations"
        end if
    end tell
    '''
    test_applescript(script8, "Notes page shape count")
    
    # Test 9: Try to get notes from shape 2 (sometimes notes are in shape 2)
    script9 = '''
    tell application "Microsoft PowerPoint"
        if (count of presentations) > 0 then
            set pres to presentation 1
            if (count of slides of pres) > 0 then
                set currentSlide to slide 1 of pres
                try
                    set notesPage to notes page of currentSlide
                    if (count of shapes of notesPage) > 1 then
                        return content of text range of text frame of shape 2 of notesPage
                    else
                        return "Less than 2 shapes on notes page"
                    end if
                on error errMsg
                    return "Shape 2 error: " & errMsg
                end try
            else
                return "No slides"
            end if
        else
            return "No presentations"
        end if
    end tell
    '''
    test_applescript(script9, "Speaker notes from shape 2")


if __name__ == "__main__":
    print("Make sure PowerPoint is open with your presentation!")
    print("Navigate to slide 1 which should have [Orik] tags in speaker notes.")
    input("Press Enter to continue...")
    
    main()