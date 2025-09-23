#!/usr/bin/env python3
"""Runner script for DigAtAaronTool MCP server."""

import asyncio
import logging
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import mcp
    from mcp.server.stdio import stdio_server
except ImportError:
    print("MCP library not found. Please install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

from mcp_tools.dig_at_aaron_tool import app


async def main():
    """Run the DigAtAaronTool MCP server."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting DigAtAaronTool MCP server...")
    
    try:
        # Run the MCP server using stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())