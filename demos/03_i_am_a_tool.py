from strands import Agent, tool
import random

@tool
def random_number(start: int, end: int) -> int:
    """Generates a random number within a range.

    Return a random number with a start and end range
    """
    return random.randint(start, end)

agent = Agent(tools=[random_number])
agent("Generate a random number between 1 and 10")