"""Unit tests for DigAtAaronTool MCP server."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_tools.dig_at_aaron_tool import DigAtAaronTool, DigSelector, DigLibrary
from models.enums import ResponseType


class TestDigLibrary:
    """Test the DigLibrary class and its content."""
    
    def test_library_has_all_categories(self):
        """Test that all expected categories exist in the library."""
        assert hasattr(DigLibrary, 'PRESENTATION_SKILLS')
        assert hasattr(DigLibrary, 'TECHNICAL_COMPETENCE')
        assert hasattr(DigLibrary, 'DESIGN_CHOICES')
        assert hasattr(DigLibrary, 'GENERAL_SARCASM')
        assert hasattr(DigLibrary, 'CONTEXT_SPECIFIC')
    
    def test_library_categories_not_empty(self):
        """Test that all library categories contain content."""
        assert len(DigLibrary.PRESENTATION_SKILLS) > 0
        assert len(DigLibrary.TECHNICAL_COMPETENCE) > 0
        assert len(DigLibrary.DESIGN_CHOICES) > 0
        assert len(DigLibrary.GENERAL_SARCASM) > 0
        assert len(DigLibrary.CONTEXT_SPECIFIC) > 0
    
    def test_library_content_quality(self):
        """Test that library content meets quality standards."""
        # Check that all digs are strings and not empty
        for category in [DigLibrary.PRESENTATION_SKILLS, DigLibrary.TECHNICAL_COMPETENCE,
                        DigLibrary.DESIGN_CHOICES, DigLibrary.GENERAL_SARCASM]:
            for dig in category:
                assert isinstance(dig, str)
                assert len(dig.strip()) > 0
                assert len(dig) < 200  # Reasonable length limit
        
        # Check context-specific digs
        for context, digs in DigLibrary.CONTEXT_SPECIFIC.items():
            assert isinstance(context, str)
            assert len(digs) > 0
            for dig in digs:
                assert isinstance(dig, str)
                assert len(dig.strip()) > 0
    
    def test_library_contains_aaron_references(self):
        """Test that digs appropriately reference Aaron."""
        all_digs = (DigLibrary.PRESENTATION_SKILLS + 
                   DigLibrary.TECHNICAL_COMPETENCE + 
                   DigLibrary.DESIGN_CHOICES + 
                   DigLibrary.GENERAL_SARCASM)
        
        aaron_references = [dig for dig in all_digs if 'Aaron' in dig or 'aaron' in dig]
        assert len(aaron_references) > 0, "Library should contain digs that reference Aaron"


class TestDigSelector:
    """Test the DigSelector class functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.selector = DigSelector()
    
    def test_selector_initialization(self):
        """Test that selector initializes correctly."""
        assert len(self.selector.used_digs) == 0
        assert len(self.selector.category_usage) == 0
        assert self.selector.last_category is None
    
    def test_select_dig_basic(self):
        """Test basic dig selection without context."""
        dig = self.selector.select_dig()
        
        assert isinstance(dig, str)
        assert len(dig) > 0
        assert dig in self.selector.used_digs
        assert len(self.selector.category_usage) > 0
    
    def test_select_dig_with_context(self):
        """Test dig selection with context."""
        # Test demo context
        dig = self.selector.select_dig(context="Aaron is about to demo the feature")
        assert isinstance(dig, str)
        assert len(dig) > 0
        
        # Test architecture context
        dig = self.selector.select_dig(context="Here's the system architecture")
        assert isinstance(dig, str)
        assert len(dig) > 0
    
    def test_avoid_repetition(self):
        """Test that repetition avoidance works."""
        # Generate multiple digs and check for variety
        digs = []
        for _ in range(10):
            dig = self.selector.select_dig()
            digs.append(dig)
        
        # Should have some variety (not all the same)
        unique_digs = set(digs)
        assert len(unique_digs) > 1, "Should generate varied digs"
    
    def test_reset_usage_history(self):
        """Test resetting usage history."""
        # Generate some digs to populate history
        for _ in range(3):
            self.selector.select_dig()
        
        assert len(self.selector.used_digs) > 0
        assert len(self.selector.category_usage) > 0
        
        # Reset and verify
        self.selector.reset_usage_history()
        assert len(self.selector.used_digs) == 0
        assert len(self.selector.category_usage) == 0
        assert self.selector.last_category is None
    
    def test_get_usage_stats(self):
        """Test getting usage statistics."""
        # Generate some digs
        for _ in range(3):
            self.selector.select_dig()
        
        stats = self.selector.get_usage_stats()
        
        assert isinstance(stats, dict)
        assert "used_digs_count" in stats
        assert "category_usage" in stats
        assert "last_category" in stats
        assert stats["used_digs_count"] == 3
    
    def test_context_category_mapping(self):
        """Test that context maps to appropriate categories."""
        # Test various contexts
        contexts = [
            ("demo presentation", ["context_demo"]),
            ("system architecture", ["technical_competence"]),
            ("slide design", ["design_choices"]),
            ("Aaron's presentation", ["presentation_skills"])
        ]
        
        for context, expected_category_types in contexts:
            categories = self.selector._get_categories_for_context(context)
            assert len(categories) > 0
            # Should include base categories plus context-specific ones
            assert len(categories) >= 4  # At least the 4 base categories
    
    def test_category_selection_variety(self):
        """Test that category selection promotes variety."""
        # Mock the category usage to test variety preference
        self.selector.category_usage = {
            "presentation_skills": 5,
            "technical_competence": 1,
            "design_choices": 1,
            "general_sarcasm": 1
        }
        
        categories = ["presentation_skills", "technical_competence", "design_choices", "general_sarcasm"]
        
        # Should prefer less-used categories
        selected_category = self.selector._select_category(categories)
        assert selected_category in categories
        # Note: Due to randomness, we can't guarantee it won't select the most-used category,
        # but the weighting should make it less likely


class TestDigAtAaronTool:
    """Test the main DigAtAaronTool class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = DigAtAaronTool()
    
    @pytest.mark.asyncio
    async def test_get_aaron_dig_basic(self):
        """Test basic Aaron dig generation."""
        result = await self.tool.get_aaron_dig()
        
        assert result["success"] is True
        assert "dig" in result
        assert isinstance(result["dig"], str)
        assert len(result["dig"]) > 0
        assert "response" in result
        assert "usage_stats" in result
    
    @pytest.mark.asyncio
    async def test_get_aaron_dig_with_context(self):
        """Test Aaron dig generation with context."""
        context = "Aaron is demonstrating the new security feature"
        result = await self.tool.get_aaron_dig(context=context)
        
        assert result["success"] is True
        assert result["context_used"] is True
        assert result["response"]["source_content"] == context
        assert result["response"]["response_type"] == ResponseType.RANDOM_DIG.value
    
    @pytest.mark.asyncio
    async def test_get_aaron_dig_with_used_digs(self):
        """Test Aaron dig generation with used digs list."""
        used_digs = ["Some previously used dig"]
        result = await self.tool.get_aaron_dig(used_digs=used_digs)
        
        assert result["success"] is True
        assert result["dig"] not in used_digs
    
    @pytest.mark.asyncio
    async def test_get_aaron_dig_response_structure(self):
        """Test that the response has the correct structure."""
        result = await self.tool.get_aaron_dig()
        
        assert result["success"] is True
        
        # Check response object structure
        response = result["response"]
        assert "response_text" in response
        assert "confidence" in response
        assert "response_type" in response
        assert "generation_time" in response
        assert "source_content" in response
        
        # Check confidence is high for curated content
        assert response["confidence"] == 0.9
        assert response["response_type"] == ResponseType.RANDOM_DIG.value
    
    @pytest.mark.asyncio
    async def test_reset_dig_history(self):
        """Test resetting dig history."""
        # Generate some digs first
        await self.tool.get_aaron_dig()
        await self.tool.get_aaron_dig()
        
        # Reset history
        result = await self.tool.reset_dig_history()
        
        assert result["success"] is True
        assert "message" in result
        assert "timestamp" in result
        
        # Verify history is reset
        stats = self.tool.selector.get_usage_stats()
        assert stats["used_digs_count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_dig_stats(self):
        """Test getting dig statistics."""
        # Generate some digs first
        await self.tool.get_aaron_dig()
        await self.tool.get_aaron_dig()
        
        result = await self.tool.get_dig_stats()
        
        assert result["success"] is True
        assert "usage_stats" in result
        assert "library_stats" in result
        assert "timestamp" in result
        
        # Check library stats structure
        library_stats = result["library_stats"]
        assert "total_presentation_skills" in library_stats
        assert "total_technical_competence" in library_stats
        assert "total_design_choices" in library_stats
        assert "total_general_sarcasm" in library_stats
        assert "context_specific_categories" in library_stats
        
        # Verify counts are positive
        assert library_stats["total_presentation_skills"] > 0
        assert library_stats["total_technical_competence"] > 0
        assert library_stats["total_design_choices"] > 0
        assert library_stats["total_general_sarcasm"] > 0
        assert library_stats["context_specific_categories"] > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in tool methods."""
        # Mock an error in the selector
        with patch.object(self.tool.selector, 'select_dig', side_effect=Exception("Test error")):
            result = await self.tool.get_aaron_dig()
            
            assert result["success"] is False
            assert "error" in result
            assert result["dig"] is None
    
    @pytest.mark.asyncio
    async def test_variety_validation(self):
        """Test that the tool generates varied digs over multiple calls."""
        digs = []
        
        # Generate multiple digs
        for _ in range(10):
            result = await self.tool.get_aaron_dig()
            assert result["success"] is True
            digs.append(result["dig"])
        
        # Should have variety (not all the same)
        unique_digs = set(digs)
        assert len(unique_digs) > 1, "Should generate varied digs"
        
        # Should use different categories
        stats_result = await self.tool.get_dig_stats()
        category_usage = stats_result["usage_stats"]["category_usage"]
        assert len(category_usage) > 0, "Should use at least one category"
    
    @pytest.mark.asyncio
    async def test_context_awareness(self):
        """Test that context influences dig selection appropriately."""
        contexts = [
            "Aaron is about to demo the feature",
            "Here's the system architecture Aaron designed",
            "Aaron's slide design choices",
            "Aaron's presentation skills"
        ]
        
        results = []
        for context in contexts:
            result = await self.tool.get_aaron_dig(context=context)
            assert result["success"] is True
            assert result["context_used"] is True
            results.append(result)
        
        # All should be successful and have context
        assert all(r["success"] for r in results)
        assert all(r["context_used"] for r in results)


class TestDigAtAaronToolIntegration:
    """Integration tests for the DigAtAaronTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = DigAtAaronTool()
    
    @pytest.mark.asyncio
    async def test_full_presentation_simulation(self):
        """Test a full presentation simulation with multiple slides."""
        # Simulate a presentation with different slide contexts
        slide_contexts = [
            "Welcome to Aaron's presentation",
            "Aaron will demo the new feature",
            "Here's Aaron's system architecture",
            "Aaron's performance metrics",
            "Aaron's security implementation",
            "Thank you for watching Aaron's presentation"
        ]
        
        # Reset history for new presentation
        reset_result = await self.tool.reset_dig_history()
        assert reset_result["success"] is True
        
        # Generate digs for each slide
        digs = []
        for i, context in enumerate(slide_contexts):
            result = await self.tool.get_aaron_dig(context=context)
            assert result["success"] is True
            digs.append(result["dig"])
            
            print(f"Slide {i+1}: {context}")
            print(f"Orik: {result['dig']}")
            print()
        
        # Verify variety across the presentation
        unique_digs = set(digs)
        assert len(unique_digs) > len(digs) // 2, "Should have good variety across presentation"
        
        # Check final statistics
        stats_result = await self.tool.get_dig_stats()
        assert stats_result["success"] is True
        assert stats_result["usage_stats"]["used_digs_count"] == len(slide_contexts)
    
    @pytest.mark.asyncio
    async def test_repetition_avoidance_over_time(self):
        """Test that repetition avoidance works over extended use."""
        # Generate many digs to test repetition avoidance
        digs = []
        for _ in range(20):
            result = await self.tool.get_aaron_dig()
            assert result["success"] is True
            digs.append(result["dig"])
        
        # Calculate repetition rate
        unique_digs = set(digs)
        repetition_rate = 1 - (len(unique_digs) / len(digs))
        
        # Should have low repetition rate (< 50%)
        assert repetition_rate < 0.5, f"Repetition rate too high: {repetition_rate:.2%}"
        
        print(f"Generated {len(digs)} digs with {len(unique_digs)} unique digs")
        print(f"Repetition rate: {repetition_rate:.2%}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])