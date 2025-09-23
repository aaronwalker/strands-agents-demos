"""Unit tests for SpeakerNotesTool MCP server."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import json
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_tools.speaker_notes_tool import SpeakerNotesTool, SpeakerNotesExtractor
from models.slide_data import SlideData
from models.orik_content import OrikContent


class TestSpeakerNotesExtractor:
    """Test cases for SpeakerNotesExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = SpeakerNotesExtractor()
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_extract_notes_from_powerpoint_success(self, mock_subprocess):
        """Test successful PowerPoint notes extraction."""
        # Mock successful AppleScript execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Test Slide Title|||[Orik] This is a test note with Orik tag"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        result = await self.extractor.extract_notes_from_powerpoint("test.pptx", 0)
        
        assert isinstance(result, SlideData)
        assert result.slide_index == 0
        assert result.slide_title == "Test Slide Title"
        assert result.speaker_notes == "[Orik] This is a test note with Orik tag"
        assert result.presentation_path == "test.pptx"
        assert isinstance(result.timestamp, datetime)
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_extract_notes_from_powerpoint_error(self, mock_subprocess):
        """Test PowerPoint notes extraction with error."""
        # Mock failed AppleScript execution
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "PowerPoint not running"
        mock_subprocess.return_value = mock_result
        
        with pytest.raises(Exception, match="Failed to extract notes"):
            await self.extractor.extract_notes_from_powerpoint("test.pptx", 0)
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_extract_notes_from_powerpoint_timeout(self, mock_subprocess):
        """Test PowerPoint notes extraction with timeout."""
        # Mock timeout
        import subprocess
        mock_subprocess.side_effect = subprocess.TimeoutExpired("osascript", 10)
        
        with pytest.raises(Exception, match="PowerPoint interaction timed out"):
            await self.extractor.extract_notes_from_powerpoint("test.pptx", 0)
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_extract_notes_applescript_error_response(self, mock_subprocess):
        """Test handling of AppleScript error responses."""
        # Mock AppleScript returning error
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "ERROR: No presentation open"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        with pytest.raises(Exception, match="ERROR: No presentation open"):
            await self.extractor.extract_notes_from_powerpoint("test.pptx", 0)
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_get_current_slide_index_success(self, mock_subprocess):
        """Test successful current slide index retrieval."""
        # Mock successful AppleScript execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "3"  # PowerPoint returns 1-based, we convert to 0-based
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        result = await self.extractor.get_current_slide_index()
        
        assert result == 2  # Should be converted to 0-based index
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_get_current_slide_index_error(self, mock_subprocess):
        """Test current slide index retrieval with error."""
        # Mock failed AppleScript execution
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "PowerPoint not running"
        mock_subprocess.return_value = mock_result
        
        result = await self.extractor.get_current_slide_index()
        
        assert result == -1
    
    @pytest.mark.asyncio
    async def test_extract_notes_from_file_fallback(self):
        """Test fallback file-based extraction."""
        result = await self.extractor.extract_notes_from_file("test.pptx", 2)
        
        assert isinstance(result, SlideData)
        assert result.slide_index == 2
        assert result.slide_title == "Slide 3"  # 0-based + 1
        assert result.speaker_notes == ""
        assert result.presentation_path == "test.pptx"


class TestSpeakerNotesTool:
    """Test cases for SpeakerNotesTool class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = SpeakerNotesTool()
    
    @pytest.mark.asyncio
    async def test_extract_speaker_notes_with_orik_tags(self):
        """Test speaker notes extraction with Orik tags."""
        # Mock the extractor
        mock_slide_data = SlideData(
            slide_index=0,
            slide_title="Test Slide",
            speaker_notes="[Orik] Aaron is about to make another brilliant point [Orik] This should be interesting",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        with patch.object(self.tool.extractor, 'extract_notes_from_powerpoint', return_value=mock_slide_data):
            result = await self.tool.extract_speaker_notes(0, "test.pptx")
        
        assert result["success"] is True
        assert result["has_orik_tags"] is True
        assert result["tag_count"] == 2
        assert len(result["extracted_tags"]) == 2
        assert "Aaron is about to make another brilliant point" in result["extracted_tags"]
        assert "This should be interesting" in result["extracted_tags"]
    
    @pytest.mark.asyncio
    async def test_extract_speaker_notes_no_orik_tags(self):
        """Test speaker notes extraction without Orik tags."""
        # Mock the extractor
        mock_slide_data = SlideData(
            slide_index=1,
            slide_title="Regular Slide",
            speaker_notes="This is just regular speaker notes without any tags",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        with patch.object(self.tool.extractor, 'extract_notes_from_powerpoint', return_value=mock_slide_data):
            result = await self.tool.extract_speaker_notes(1, "test.pptx")
        
        assert result["success"] is True
        assert result["has_orik_tags"] is False
        assert result["tag_count"] == 0
        assert len(result["extracted_tags"]) == 0
    
    @pytest.mark.asyncio
    async def test_extract_speaker_notes_empty_orik_tag(self):
        """Test speaker notes extraction with empty Orik tag."""
        # Mock the extractor
        mock_slide_data = SlideData(
            slide_index=2,
            slide_title="Empty Tag Slide",
            speaker_notes="Some notes [Orik]   ",  # Empty tag with just whitespace
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        with patch.object(self.tool.extractor, 'extract_notes_from_powerpoint', return_value=mock_slide_data):
            result = await self.tool.extract_speaker_notes(2, "test.pptx")
        
        assert result["success"] is True
        assert result["has_orik_tags"] is False  # Empty tag should not count
        assert result["tag_count"] == 0
    
    @pytest.mark.asyncio
    async def test_extract_speaker_notes_orik_with_following_content(self):
        """Test speaker notes extraction where Orik tag has content after it."""
        # Mock the extractor
        mock_slide_data = SlideData(
            slide_index=3,
            slide_title="Content After Tag",
            speaker_notes="Some notes [Orik] and more notes",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        with patch.object(self.tool.extractor, 'extract_notes_from_powerpoint', return_value=mock_slide_data):
            result = await self.tool.extract_speaker_notes(3, "test.pptx")
        
        assert result["success"] is True
        assert result["has_orik_tags"] is True
        assert result["tag_count"] == 1
        assert "and more notes" in result["extracted_tags"]
    
    @pytest.mark.asyncio
    async def test_extract_speaker_notes_extraction_error(self):
        """Test speaker notes extraction with extraction error."""
        # Mock the extractor to raise an exception
        with patch.object(self.tool.extractor, 'extract_notes_from_powerpoint', side_effect=Exception("PowerPoint error")):
            result = await self.tool.extract_speaker_notes(0, "test.pptx")
        
        assert result["success"] is False
        assert "PowerPoint error" in result["error"]
        assert result["slide_data"] is None
        assert result["orik_content"] is None
        assert result["has_orik_tags"] is False
        assert result["tag_count"] == 0
    
    @pytest.mark.asyncio
    async def test_extract_speaker_notes_default_presentation_path(self):
        """Test speaker notes extraction with default presentation path."""
        # Mock the extractor
        mock_slide_data = SlideData(
            slide_index=0,
            slide_title="Test Slide",
            speaker_notes="[Orik] Test content",
            presentation_path="active_presentation",
            timestamp=datetime.now()
        )
        
        with patch.object(self.tool.extractor, 'extract_notes_from_powerpoint', return_value=mock_slide_data) as mock_extract:
            result = await self.tool.extract_speaker_notes(0)  # No presentation_path provided
        
        # Should call with "active_presentation" as default
        mock_extract.assert_called_once_with("active_presentation", 0)
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_current_slide_notes_success(self):
        """Test getting current slide notes successfully."""
        # Mock the extractor methods
        mock_slide_data = SlideData(
            slide_index=2,
            slide_title="Current Slide",
            speaker_notes="[Orik] Current slide content",
            presentation_path="active_presentation",
            timestamp=datetime.now()
        )
        
        with patch.object(self.tool.extractor, 'get_current_slide_index', return_value=2), \
             patch.object(self.tool.extractor, 'extract_notes_from_powerpoint', return_value=mock_slide_data):
            result = await self.tool.get_current_slide_notes()
        
        assert result["success"] is True
        assert result["slide_data"]["slide_index"] == 2
        assert result["has_orik_tags"] is True
    
    @pytest.mark.asyncio
    async def test_get_current_slide_notes_no_active_slide(self):
        """Test getting current slide notes when no active slide."""
        # Mock the extractor to return -1 (no active slide)
        with patch.object(self.tool.extractor, 'get_current_slide_index', return_value=-1):
            result = await self.tool.get_current_slide_notes()
        
        assert result["success"] is False
        assert "No active presentation or slide found" in result["error"]
        assert result["slide_data"] is None
        assert result["orik_content"] is None
    
    @pytest.mark.asyncio
    async def test_get_current_slide_notes_extraction_error(self):
        """Test getting current slide notes with extraction error."""
        # Mock the extractor methods
        with patch.object(self.tool.extractor, 'get_current_slide_index', return_value=1), \
             patch.object(self.tool.extractor, 'extract_notes_from_powerpoint', side_effect=Exception("Extraction failed")):
            result = await self.tool.get_current_slide_notes()
        
        assert result["success"] is False
        assert "Extraction failed" in result["error"]


class TestOrikTagExtraction:
    """Test cases for Orik tag extraction patterns."""
    
    def test_single_orik_tag(self):
        """Test extraction of single Orik tag."""
        slide_data = SlideData(
            slide_index=0,
            slide_title="Test",
            speaker_notes="[Orik] Single tag content",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        orik_content = OrikContent.extract_from_notes(slide_data)
        
        assert orik_content.has_orik_tags is True
        assert orik_content.tag_count == 1
        assert orik_content.extracted_tags[0] == "Single tag content"
    
    def test_multiple_orik_tags(self):
        """Test extraction of multiple Orik tags."""
        slide_data = SlideData(
            slide_index=0,
            slide_title="Test",
            speaker_notes="[Orik] First tag [Orik] Second tag [Orik] Third tag",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        orik_content = OrikContent.extract_from_notes(slide_data)
        
        assert orik_content.has_orik_tags is True
        assert orik_content.tag_count == 3
        assert "First tag" in orik_content.extracted_tags
        assert "Second tag" in orik_content.extracted_tags
        assert "Third tag" in orik_content.extracted_tags
    
    def test_case_insensitive_orik_tags(self):
        """Test case-insensitive Orik tag extraction."""
        slide_data = SlideData(
            slide_index=0,
            slide_title="Test",
            speaker_notes="[orik] lowercase [ORIK] uppercase [Orik] mixed case",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        orik_content = OrikContent.extract_from_notes(slide_data)
        
        assert orik_content.has_orik_tags is True
        assert orik_content.tag_count == 3
    
    def test_orik_tags_with_newlines(self):
        """Test Orik tag extraction across newlines."""
        slide_data = SlideData(
            slide_index=0,
            slide_title="Test",
            speaker_notes="[Orik] First line content\nSecond line\n[Orik] Another tag",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        orik_content = OrikContent.extract_from_notes(slide_data)
        
        assert orik_content.has_orik_tags is True
        assert orik_content.tag_count == 2
        # First tag should capture content across newlines until next tag
        assert "First line content\nSecond line" in orik_content.extracted_tags
        assert "Another tag" in orik_content.extracted_tags
    
    def test_empty_orik_tags_filtered_out(self):
        """Test that empty Orik tags are filtered out."""
        slide_data = SlideData(
            slide_index=0,
            slide_title="Test",
            speaker_notes="[Orik]   [Orik] Valid content [Orik]    ",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        orik_content = OrikContent.extract_from_notes(slide_data)
        
        assert orik_content.has_orik_tags is True
        assert orik_content.tag_count == 1
        assert orik_content.extracted_tags[0] == "Valid content"
    
    def test_no_orik_tags(self):
        """Test notes without any Orik tags."""
        slide_data = SlideData(
            slide_index=0,
            slide_title="Test",
            speaker_notes="Regular speaker notes without any special tags",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        orik_content = OrikContent.extract_from_notes(slide_data)
        
        assert orik_content.has_orik_tags is False
        assert orik_content.tag_count == 0
        assert len(orik_content.extracted_tags) == 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])