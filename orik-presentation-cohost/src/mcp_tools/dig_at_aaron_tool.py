"""DigAtAaronTool MCP server for generating sarcastic one-liners targeting Aaron."""

import asyncio
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
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

from models.orik_response import OrikResponse
from models.enums import ResponseType


logger = logging.getLogger(__name__)


class DigLibrary:
    """Curated library of sarcastic one-liners targeting Aaron."""
    
    # General presentation skills digs
    PRESENTATION_SKILLS = [
        "Sure, let's all pretend Aaron rehearsed this part",
        "Oh look, Aaron's reading directly from his slides again",
        "Wow Aaron, that transition was smoother than sandpaper",
        "I see Aaron's using the 'wing it and hope for the best' approach",
        "Aaron's presentation skills are truly... something",
        "Let me guess, Aaron practiced this in the shower this morning",
        "Aaron's confidence is inversely proportional to his preparation",
        "Nothing says 'professional presenter' like Aaron's deer-in-headlights look"
    ]
    
    # Technical competence digs
    TECHNICAL_COMPETENCE = [
        "Wow Aaron, groundbreaking insight... from 2012",
        "Aaron's technical depth is about as shallow as a puddle",
        "I'm sure Aaron totally understands what he just said",
        "Aaron's explaining this like he learned it five minutes ago",
        "That's some cutting-edge technology there, Aaron... if this were 2010",
        "Aaron's technical expertise shines through like a 5-watt bulb",
        "I love how Aaron makes complex topics sound... confusing",
        "Aaron's grasp of the technology is truly... aspirational"
    ]
    
    # Design and slide quality digs
    DESIGN_CHOICES = [
        "Another slide where Aaron proves bullet points are a design choice",
        "Aaron's slide design aesthetic: 'More is more'",
        "I see Aaron went with the 'wall of text' approach again",
        "Aaron's color scheme really captures that 'default PowerPoint' vibe",
        "Nothing says 'professional' like Aaron's Comic Sans font choice",
        "Aaron's slides have all the visual appeal of a tax document",
        "I love how Aaron makes every slide look like a ransom note",
        "Aaron's design philosophy: 'If it fits, it ships'"
    ]
    
    # General sarcasm and personality
    GENERAL_SARCASM = [
        "Oh brilliant, Aaron. Just brilliant",
        "Aaron never fails to... well, actually he fails quite often",
        "I'm sure the audience is hanging on Aaron's every word",
        "Aaron's enthusiasm is truly... noticeable",
        "Let me contain my excitement about Aaron's next point",
        "Aaron's about to blow our minds with his next revelation",
        "I can practically feel the audience's engagement levels soaring",
        "Aaron's really outdoing himself today... and that's saying something"
    ]
    
    # Context-specific digs for common presentation topics
    CONTEXT_SPECIFIC = {
        "demo": [
            "I'm sure this demo will work perfectly, just like Aaron's last one",
            "Aaron's demos have a 50/50 chance of working... and that's optimistic",
            "Let's all cross our fingers that Aaron's demo gods are smiling today"
        ],
        "architecture": [
            "Aaron's architecture diagrams are as clear as mud",
            "I love how Aaron makes simple architectures look impossibly complex",
            "Aaron's architectural decisions are truly... decisions"
        ],
        "performance": [
            "Aaron's performance metrics are about as reliable as his predictions",
            "I'm sure Aaron's performance numbers are totally accurate",
            "Aaron's optimization skills are truly... visible"
        ],
        "security": [
            "Aaron's security approach: 'Hope for the best'",
            "I'm sure Aaron's security implementation is bulletproof... like tissue paper",
            "Aaron's security expertise is truly... concerning"
        ],
        "integration": [
            "Aaron's integration strategy: 'It should just work'",
            "I love how Aaron makes integration sound so... simple",
            "Aaron's integration approach is as smooth as a gravel road"
        ]
    }


class DigSelector:
    """Handles selection of appropriate digs with variety and context awareness."""
    
    def __init__(self):
        self.used_digs: Set[str] = set()
        self.category_usage: Dict[str, int] = {}
        self.last_category: Optional[str] = None
        
    def select_dig(self, context: Optional[str] = None, avoid_recent: bool = True) -> str:
        """
        Select an appropriate dig based on context and usage history.
        
        Args:
            context: Optional context about current slide/topic
            avoid_recent: Whether to avoid recently used digs
            
        Returns:
            Selected sarcastic one-liner
        """
        # Determine appropriate categories based on context
        available_categories = self._get_categories_for_context(context)
        
        # Select category with preference for variety
        selected_category = self._select_category(available_categories)
        
        # Get digs from selected category
        category_digs = self._get_digs_from_category(selected_category)
        
        # Filter out recently used digs if requested
        if avoid_recent:
            available_digs = [dig for dig in category_digs if dig not in self.used_digs]
            if not available_digs:
                # If all digs have been used, reset and use all
                self.used_digs.clear()
                available_digs = category_digs
        else:
            available_digs = category_digs
        
        # Select random dig from available options
        selected_dig = random.choice(available_digs)
        
        # Update usage tracking
        self.used_digs.add(selected_dig)
        self.category_usage[selected_category] = self.category_usage.get(selected_category, 0) + 1
        self.last_category = selected_category
        
        logger.info(f"Selected dig from category '{selected_category}': {selected_dig[:50]}...")
        return selected_dig
    
    def _get_categories_for_context(self, context: Optional[str]) -> List[str]:
        """Get appropriate categories based on context."""
        base_categories = ["presentation_skills", "technical_competence", "design_choices", "general_sarcasm"]
        
        if not context:
            return base_categories
        
        context_lower = context.lower()
        
        # Check for context-specific keywords
        for keyword, _ in DigLibrary.CONTEXT_SPECIFIC.items():
            if keyword in context_lower:
                return [f"context_{keyword}"] + base_categories
        
        # Check for other contextual hints
        if any(word in context_lower for word in ["slide", "design", "layout", "visual"]):
            return ["design_choices"] + base_categories
        
        if any(word in context_lower for word in ["technical", "code", "implementation", "system"]):
            return ["technical_competence"] + base_categories
        
        if any(word in context_lower for word in ["present", "speak", "explain", "show"]):
            return ["presentation_skills"] + base_categories
        
        return base_categories
    
    def _select_category(self, available_categories: List[str]) -> str:
        """Select category with preference for variety."""
        # Avoid using the same category twice in a row if possible
        if len(available_categories) > 1 and self.last_category in available_categories:
            other_categories = [cat for cat in available_categories if cat != self.last_category]
            if other_categories:
                available_categories = other_categories
        
        # Prefer less-used categories
        category_weights = []
        for category in available_categories:
            usage_count = self.category_usage.get(category, 0)
            # Higher weight for less-used categories
            weight = max(1, 10 - usage_count)
            category_weights.append(weight)
        
        # Weighted random selection
        selected_category = random.choices(available_categories, weights=category_weights)[0]
        return selected_category
    
    def _get_digs_from_category(self, category: str) -> List[str]:
        """Get digs from the specified category."""
        if category == "presentation_skills":
            return DigLibrary.PRESENTATION_SKILLS
        elif category == "technical_competence":
            return DigLibrary.TECHNICAL_COMPETENCE
        elif category == "design_choices":
            return DigLibrary.DESIGN_CHOICES
        elif category == "general_sarcasm":
            return DigLibrary.GENERAL_SARCASM
        elif category.startswith("context_"):
            context_key = category.replace("context_", "")
            return DigLibrary.CONTEXT_SPECIFIC.get(context_key, DigLibrary.GENERAL_SARCASM)
        else:
            return DigLibrary.GENERAL_SARCASM
    
    def reset_usage_history(self):
        """Reset usage history for a new presentation."""
        self.used_digs.clear()
        self.category_usage.clear()
        self.last_category = None
        logger.info("Reset dig usage history")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return {
            "used_digs_count": len(self.used_digs),
            "category_usage": dict(self.category_usage),
            "last_category": self.last_category
        }


class DigAtAaronTool:
    """MCP tool for generating sarcastic one-liners targeting Aaron."""
    
    def __init__(self):
        self.selector = DigSelector()
        
    async def get_aaron_dig(self, context: Optional[str] = None, 
                           used_digs: Optional[List[str]] = None,
                           avoid_repetition: bool = True) -> Dict[str, Any]:
        """
        Generate a random sarcastic one-liner targeting Aaron.
        
        Args:
            context: Optional context about current slide/topic
            used_digs: List of previously used digs to avoid repetition
            avoid_repetition: Whether to avoid recently used digs
            
        Returns:
            Dictionary containing the selected dig and metadata
        """
        try:
            # Update selector with provided used digs if given
            if used_digs:
                self.selector.used_digs.update(used_digs)
            
            # Select appropriate dig
            selected_dig = self.selector.select_dig(context, avoid_repetition)
            
            # Create response object
            response = OrikResponse(
                response_text=selected_dig,
                confidence=0.9,  # High confidence for curated content
                response_type=ResponseType.RANDOM_DIG,
                generation_time=datetime.now(),
                source_content=context
            )
            
            # Get usage statistics
            usage_stats = self.selector.get_usage_stats()
            
            result = {
                "success": True,
                "dig": selected_dig,
                "response": response.to_dict(),
                "usage_stats": usage_stats,
                "context_used": context is not None
            }
            
            logger.info(f"Generated Aaron dig: {selected_dig[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error generating Aaron dig: {e}")
            return {
                "success": False,
                "error": str(e),
                "dig": None,
                "response": None,
                "usage_stats": None
            }
    
    async def reset_dig_history(self) -> Dict[str, Any]:
        """
        Reset the dig usage history for a new presentation.
        
        Returns:
            Dictionary confirming the reset
        """
        try:
            self.selector.reset_usage_history()
            
            return {
                "success": True,
                "message": "Dig usage history reset successfully",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error resetting dig history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_dig_stats(self) -> Dict[str, Any]:
        """
        Get current dig usage statistics.
        
        Returns:
            Dictionary containing usage statistics
        """
        try:
            stats = self.selector.get_usage_stats()
            
            # Add library information
            library_stats = {
                "total_presentation_skills": len(DigLibrary.PRESENTATION_SKILLS),
                "total_technical_competence": len(DigLibrary.TECHNICAL_COMPETENCE),
                "total_design_choices": len(DigLibrary.DESIGN_CHOICES),
                "total_general_sarcasm": len(DigLibrary.GENERAL_SARCASM),
                "context_specific_categories": len(DigLibrary.CONTEXT_SPECIFIC)
            }
            
            return {
                "success": True,
                "usage_stats": stats,
                "library_stats": library_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dig stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# MCP Server setup
if mcp:
    app = Server("dig-at-aaron-tool")
    tool_instance = DigAtAaronTool()
    
    @app.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="get_aaron_dig",
                description="Generate a random sarcastic one-liner targeting Aaron with context awareness and repetition avoidance",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "context": {
                            "type": "string",
                            "description": "Optional context about current slide/topic to influence dig selection",
                            "default": ""
                        },
                        "used_digs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of previously used digs to avoid repetition",
                            "default": []
                        },
                        "avoid_repetition": {
                            "type": "boolean",
                            "description": "Whether to avoid recently used digs",
                            "default": True
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="reset_dig_history",
                description="Reset the dig usage history for a new presentation",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_dig_stats",
                description="Get current dig usage statistics and library information",
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
            if name == "get_aaron_dig":
                context = arguments.get("context", None)
                used_digs = arguments.get("used_digs", [])
                avoid_repetition = arguments.get("avoid_repetition", True)
                result = await tool_instance.get_aaron_dig(context, used_digs, avoid_repetition)
                
            elif name == "reset_dig_history":
                result = await tool_instance.reset_dig_history()
                
            elif name == "get_dig_stats":
                result = await tool_instance.get_dig_stats()
                
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
    
    tool = DigAtAaronTool()
    
    # Test basic dig generation
    print("Testing basic dig generation...")
    result = await tool.get_aaron_dig()
    print(json.dumps(result, indent=2))
    
    # Test context-aware dig generation
    print("\nTesting context-aware dig generation...")
    result = await tool.get_aaron_dig(context="Aaron is about to demo the new security feature")
    print(json.dumps(result, indent=2))
    
    # Test multiple digs to show variety
    print("\nTesting variety in dig selection...")
    for i in range(3):
        result = await tool.get_aaron_dig()
        print(f"Dig {i+1}: {result.get('dig', 'Error')}")
    
    # Test usage statistics
    print("\nTesting usage statistics...")
    result = await tool.get_dig_stats()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())