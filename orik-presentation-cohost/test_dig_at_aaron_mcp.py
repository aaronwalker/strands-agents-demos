#!/usr/bin/env python3
"""Test script for DigAtAaronTool MCP server functionality."""

import asyncio
import json
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from mcp_tools.dig_at_aaron_tool import DigAtAaronTool


async def test_dig_at_aaron_mcp():
    """Test the DigAtAaronTool MCP functionality."""
    print("=== Testing DigAtAaronTool MCP Server ===\n")
    
    tool = DigAtAaronTool()
    
    # Test 1: Basic dig generation
    print("1. Testing basic dig generation...")
    result = await tool.get_aaron_dig()
    print(f"   Success: {result['success']}")
    print(f"   Dig: {result['dig']}")
    print(f"   Response Type: {result['response']['response_type']}")
    print(f"   Confidence: {result['response']['confidence']}")
    print()
    
    # Test 2: Context-aware dig generation
    print("2. Testing context-aware dig generation...")
    contexts = [
        "Aaron is about to demo the new feature",
        "Here's Aaron's system architecture",
        "Aaron's slide design choices",
        "Aaron's performance metrics"
    ]
    
    for context in contexts:
        result = await tool.get_aaron_dig(context=context)
        print(f"   Context: {context}")
        print(f"   Dig: {result['dig']}")
        print()
    
    # Test 3: Repetition avoidance
    print("3. Testing repetition avoidance...")
    digs = []
    for i in range(8):
        result = await tool.get_aaron_dig()
        digs.append(result['dig'])
        print(f"   Dig {i+1}: {result['dig']}")
    
    unique_digs = set(digs)
    print(f"   Generated {len(digs)} digs, {len(unique_digs)} unique")
    print(f"   Variety rate: {len(unique_digs)/len(digs)*100:.1f}%")
    print()
    
    # Test 4: Usage statistics
    print("4. Testing usage statistics...")
    stats_result = await tool.get_dig_stats()
    print(f"   Success: {stats_result['success']}")
    print(f"   Used digs: {stats_result['usage_stats']['used_digs_count']}")
    print(f"   Category usage: {stats_result['usage_stats']['category_usage']}")
    print(f"   Library stats: {stats_result['library_stats']}")
    print()
    
    # Test 5: Reset functionality
    print("5. Testing reset functionality...")
    reset_result = await tool.reset_dig_history()
    print(f"   Reset success: {reset_result['success']}")
    print(f"   Message: {reset_result['message']}")
    
    # Verify reset worked
    stats_after_reset = await tool.get_dig_stats()
    print(f"   Used digs after reset: {stats_after_reset['usage_stats']['used_digs_count']}")
    print()
    
    # Test 6: Error handling
    print("6. Testing error handling...")
    # Test with invalid parameters (this should still work gracefully)
    result = await tool.get_aaron_dig(context="", used_digs=[], avoid_repetition=True)
    print(f"   Empty context success: {result['success']}")
    print()
    
    # Test 7: Full presentation simulation
    print("7. Testing full presentation simulation...")
    await tool.reset_dig_history()
    
    presentation_slides = [
        "Welcome to Aaron's presentation on cloud architecture",
        "Aaron will now demo the authentication system",
        "Here's Aaron's performance benchmarks",
        "Aaron's security implementation details",
        "Aaron's deployment strategy",
        "Thank you for attending Aaron's presentation"
    ]
    
    for i, slide_context in enumerate(presentation_slides, 1):
        result = await tool.get_aaron_dig(context=slide_context)
        print(f"   Slide {i}: {slide_context}")
        print(f"   Orik: {result['dig']}")
        print()
    
    # Final statistics
    final_stats = await tool.get_dig_stats()
    print(f"Final presentation stats:")
    print(f"   Total digs used: {final_stats['usage_stats']['used_digs_count']}")
    print(f"   Categories used: {list(final_stats['usage_stats']['category_usage'].keys())}")
    
    print("\n=== DigAtAaronTool MCP Server Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_dig_at_aaron_mcp())