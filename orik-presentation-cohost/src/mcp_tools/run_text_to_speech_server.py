#!/usr/bin/env python3
"""Runner script for the TextToSpeechTool MCP server."""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the TextToSpeechTool MCP server."""
    try:
        # Import the MCP server
        from mcp_tools.text_to_speech_tool import app
        
        logger.info("Starting TextToSpeechTool MCP server...")
        
        # Run the MCP server
        import mcp.server.stdio
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
            
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Make sure boto3 and mcp are installed: pip install boto3 mcp")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error running TextToSpeechTool MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())