from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

aws_docs_client = MCPClient(
    lambda: stdio_client(StdioServerParameters(command="uvx", args=["strands-agents-mcp-server"]))
)

with aws_docs_client:
   agent = Agent(tools=aws_docs_client.list_tools_sync())
   response = agent("Tell me about Strands Agents and how to use it with Python")