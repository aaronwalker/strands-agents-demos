# Orik Presentation Co-host

A sarcastic AI presentation co-host agent that automatically responds to tagged speaker notes during presentations.

## Project Structure

```
orik-presentation-cohost/
├── src/
│   ├── models/           # Core data models and interfaces
│   ├── mcp_tools/        # MCP server implementations
│   ├── services/         # Core services (audio, presentation monitoring)
│   ├── ui/              # User interface components
│   ├── agent/           # Orik agent controller
│   └── utils/           # Utility functions and helpers
├── tests/               # Unit and integration tests
├── config/              # Configuration files
└── docs/               # Documentation
```

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Configure AWS credentials for Polly TTS
3. Run the application: `python src/main.py`

## Requirements

- Python 3.8+
- Windows (for PowerPoint COM automation)
- AWS account (for Polly TTS)