"""SpeakerNotesTool MCP server for extracting presentation speaker notes."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

try:
    import mcp
    from mcp.server import Server
    from mcp.types import Tool, TextContent
except ImportError:
    # Fallback for development/testing
    mcp = None
    Server = object
    Tool = dict
    TextContent = str

# Import our models
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.slide_data import SlideData
from models.orik_content import OrikContent


logger = logging.getLogger(__name__)


class SpeakerNotesExtractor:
    """Handles extraction of speaker notes from different presentation software."""
    
    def __init__(self):
        self.current_presentation_path: Optional[str] = None
        self._powerpoint_app = None
        
    async def extract_notes_from_powerpoint(self, presentation_path: str, slide_index: int) -> SlideData:
        """Extract speaker notes from PowerPoint presentation on macOS."""
        try:
            # For macOS, we'll use AppleScript to interact with PowerPoint
            import subprocess
            
            # Enhanced AppleScript to get slide information including content
            applescript = f'''
            tell application "Microsoft PowerPoint"
                if (count of presentations) > 0 then
                    set pres to presentation 1
                    if {slide_index + 1} <= (count of slides of pres) then
                        set currentSlide to slide {slide_index + 1} of pres
                        set slideTitle to ""
                        set slideContent to ""
                        set speakerNotes to ""
                        
                        -- Try to get slide title from first text shape
                        try
                            set slideTitle to content of text range of text frame of shape 1 of currentSlide
                        end try
                        
                        -- Get slide content from all text shapes
                        try
                            set shapeCount to count of shapes of currentSlide
                            repeat with i from 1 to shapeCount
                                try
                                    set shapeText to content of text range of text frame of shape i of currentSlide
                                    if shapeText is not "" and shapeText is not slideTitle then
                                        if slideContent is "" then
                                            set slideContent to shapeText
                                        else
                                            set slideContent to slideContent & " " & shapeText
                                        end if
                                    end if
                                end try
                            end repeat
                        end try
                        
                        -- Get speaker notes (usually in shape 2 of notes page)
                        try
                            set notesPage to notes page of currentSlide
                            if (count of shapes of notesPage) > 1 then
                                set speakerNotes to content of text range of text frame of shape 2 of notesPage
                            else
                                set speakerNotes to ""
                            end if
                        on error
                            set speakerNotes to ""
                        end try
                        
                        return slideTitle & "|||" & slideContent & "|||" & speakerNotes
                    else
                        return "ERROR: Slide index out of range"
                    end if
                else
                    return "ERROR: No presentation open"
                end if
            end tell
            '''
            
            # Execute AppleScript
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"AppleScript error: {result.stderr}")
                raise Exception(f"Failed to extract notes: {result.stderr}")
            
            # Parse result
            output = result.stdout.strip()
            if output.startswith("ERROR:"):
                raise Exception(output)
            
            parts = output.split("|||")
            slide_title = parts[0] if len(parts) > 0 else ""
            slide_content = parts[1] if len(parts) > 1 else ""
            speaker_notes = parts[2] if len(parts) > 2 else ""
            
            # Clean up "missing value" responses
            if slide_title == "missing value":
                slide_title = f"Slide {slide_index + 1}"
            if slide_content == "missing value":
                slide_content = ""
            if speaker_notes == "missing value":
                speaker_notes = ""
            
            # Create SlideData with enhanced content
            return SlideData(
                slide_index=slide_index,
                slide_title=slide_title,
                speaker_notes=speaker_notes,
                slide_content=slide_content,
                presentation_path=presentation_path,
                timestamp=datetime.now()
            )
            
        except subprocess.TimeoutExpired:
            logger.error("AppleScript execution timed out")
            raise Exception("PowerPoint interaction timed out")
        except Exception as e:
            logger.error(f"Error extracting PowerPoint notes: {e}")
            raise
    
    async def extract_notes_from_file(self, presentation_path: str, slide_index: int) -> SlideData:
        """Fallback method to extract notes from exported files."""
        # This would be implemented for file-based extraction
        # For now, return empty slide data
        logger.warning("File-based extraction not yet implemented")
        return SlideData(
            slide_index=slide_index,
            slide_title=f"Slide {slide_index + 1}",
            speaker_notes="",
            presentation_path=presentation_path,
            timestamp=datetime.now()
        )
    
    async def get_current_slide_index(self) -> int:
        """Get the current slide index from PowerPoint."""
        try:
            import subprocess
            
            applescript = '''
            tell application "Microsoft PowerPoint"
                if (count of presentations) > 0 then
                    set pres to presentation 1
                    set currentSlideIndex to slide index of slide range of selection of document window 1 of pres
                    return currentSlideIndex
                else
                    return -1
                end if
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Convert from 1-based PowerPoint index to 0-based
                return int(result.stdout.strip()) - 1
            else:
                logger.error(f"Failed to get current slide: {result.stderr}")
                return -1
                
        except Exception as e:
            logger.error(f"Error getting current slide index: {e}")
            return -1


class SpeakerNotesTool:
    """MCP tool for extracting and processing speaker notes."""
    
    def __init__(self):
        self.extractor = SpeakerNotesExtractor()
        
    async def extract_speaker_notes(self, slide_index: int, presentation_path: str = "") -> Dict[str, Any]:
        """
        Extract speaker notes from presentation and parse Orik tags.
        
        Args:
            slide_index: Current slide number (0-based)
            presentation_path: Path to presentation file (optional for active presentation)
            
        Returns:
            Dictionary containing slide data and extracted Orik content
        """
        try:
            # If no presentation path provided, use current active presentation
            if not presentation_path:
                presentation_path = "active_presentation"
            
            # Extract slide data
            slide_data = await self.extractor.extract_notes_from_powerpoint(
                presentation_path, slide_index
            )
            
            # Extract Orik content
            orik_content = OrikContent.extract_from_notes(slide_data)
            
            result = {
                "success": True,
                "slide_data": slide_data.to_dict(),
                "orik_content": orik_content.to_dict(),
                "has_orik_tags": orik_content.has_orik_tags,
                "tag_count": orik_content.tag_count,
                "extracted_tags": orik_content.extracted_tags
            }
            
            logger.info(f"Extracted notes for slide {slide_index}: {orik_content.tag_count} Orik tags found")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting speaker notes: {e}")
            return {
                "success": False,
                "error": str(e),
                "slide_data": None,
                "orik_content": None,
                "has_orik_tags": False,
                "tag_count": 0,
                "extracted_tags": []
            }
    
    async def get_current_slide_notes(self) -> Dict[str, Any]:
        """
        Get speaker notes for the currently active slide.
        
        Returns:
            Dictionary containing current slide data and Orik content
        """
        try:
            # Get current slide index
            current_index = await self.extractor.get_current_slide_index()
            
            if current_index < 0:
                return {
                    "success": False,
                    "error": "No active presentation or slide found",
                    "slide_data": None,
                    "orik_content": None
                }
            
            # Extract notes for current slide
            return await self.extract_speaker_notes(current_index)
            
        except Exception as e:
            logger.error(f"Error getting current slide notes: {e}")
            return {
                "success": False,
                "error": str(e),
                "slide_data": None,
                "orik_content": None
            }


# MCP Server setup
if mcp:
    app = Server("speaker-notes-tool")
    tool_instance = SpeakerNotesTool()
    
    @app.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="extract_speaker_notes",
                description="Extract speaker notes from presentation slide and parse Orik tags",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "slide_index": {
                            "type": "integer",
                            "description": "Slide number (0-based index)",
                            "minimum": 0
                        },
                        "presentation_path": {
                            "type": "string",
                            "description": "Path to presentation file (optional for active presentation)",
                            "default": ""
                        }
                    },
                    "required": ["slide_index"]
                }
            ),
            Tool(
                name="get_current_slide_notes",
                description="Get speaker notes for the currently active slide in PowerPoint",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    @app.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        try:
            if name == "extract_speaker_notes":
                slide_index = arguments.get("slide_index", 0)
                presentation_path = arguments.get("presentation_path", "")
                result = await tool_instance.extract_speaker_notes(slide_index, presentation_path)
                
            elif name == "get_current_slide_notes":
                result = await tool_instance.get_current_slide_notes()
                
            else:
                result = {"success": False, "error": f"Unknown tool: {name}"}
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            error_result = {"success": False, "error": str(e)}
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


# For standalone testing
async def main():
    """Main function for testing the tool."""
    logging.basicConfig(level=logging.INFO)
    
    tool = SpeakerNotesTool()
    
    # Test getting current slide notes
    print("Testing current slide notes extraction...")
    result = await tool.get_current_slide_notes()
    print(json.dumps(result, indent=2))
    
    # Test specific slide extraction
    print("\nTesting specific slide extraction...")
    result = await tool.extract_speaker_notes(0)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())