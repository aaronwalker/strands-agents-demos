from strands import Agent
from strands_tools import http_request
agent = Agent(tools=[http_request])
agent("What time is Aaron Walker session at the AWS Community Summit Manchester 2025")