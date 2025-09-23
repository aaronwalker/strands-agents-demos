# Orik Presentation Co-host - Project Structure

## Overview

This document describes the project structure and organization of the Orik Presentation Co-host system.

## Directory Structure

```
orik-presentation-cohost/
├── src/                          # Source code
│   ├── models/                   # Core data models ✓ IMPLEMENTED
│   │   ├── __init__.py          # Model exports
│   │   ├── enums.py             # System enumerations
│   │   ├── slide_data.py        # SlideData model
│   │   ├── orik_content.py      # OrikContent model
│   │   ├── orik_response.py     # OrikResponse model
│   │   ├── system_status.py     # SystemStatus model
│   │   ├── audio_models.py      # Audio-related models
│   │   └── personality.py       # OrikPersonality model
│   ├── mcp_tools/               # MCP server implementations
│   │   ├── __init__.py
│   │   ├── speaker_notes_tool.py    # [TODO: Task 2]
│   │   ├── dig_at_aaron_tool.py     # [TODO: Task 3]
│   │   └── text_to_speech_tool.py   # [TODO: Task 4]
│   ├── services/                # Core services
│   │   ├── __init__.py
│   │   ├── audio_playback_service.py    # [TODO: Task 5]
│   │   ├── presentation_monitor.py      # [TODO: Task 6]
│   │   └── error_recovery_manager.py    # [TODO: Task 9]
│   ├── agent/                   # Orik agent controller
│   │   ├── __init__.py
│   │   ├── orik_agent_controller.py     # [TODO: Task 7]
│   │   └── personality_manager.py       # [TODO: Task 7]
│   ├── ui/                      # User interface components
│   │   ├── __init__.py
│   │   ├── orik_avatar_ui.py           # [TODO: Task 8]
│   │   └── status_display.py           # [TODO: Task 8]
│   ├── utils/                   # Utility functions ✓ IMPLEMENTED
│   │   ├── __init__.py          # Utility exports
│   │   ├── validation.py        # Data validation functions
│   │   └── logging_config.py    # Logging configuration
│   └── __init__.py              # Package initialization
├── tests/                       # Test suite ✓ IMPLEMENTED
│   ├── __init__.py
│   ├── test_models.py           # Model unit tests
│   └── test_validation.py       # Validation unit tests
├── config/                      # Configuration files ✓ IMPLEMENTED
│   └── default_config.json      # Default system configuration
├── docs/                        # Documentation
│   └── project_structure.md     # This file
├── requirements.txt             # Python dependencies ✓ IMPLEMENTED
├── test_basic_functionality.py  # Basic functionality test ✓ IMPLEMENTED
└── README.md                    # Project overview ✓ IMPLEMENTED
```

## Implemented Components (Task 1)

### Core Data Models ✓

All core data models have been implemented with full validation and functionality:

- **SlideData**: Represents presentation slide information with speaker notes
- **OrikContent**: Extracts and manages [Orik] tagged content from speaker notes
- **OrikResponse**: Represents generated responses from Orik with metadata
- **SystemStatus**: Tracks system operational state and component health
- **AudioResult & VoiceConfig**: Audio processing and TTS configuration
- **OrikPersonality**: Configures Orik's behavior and response patterns

### Validation Functions ✓

Comprehensive validation utilities for:
- Slide data validation and conversion
- Orik tag extraction and validation
- System status validation
- Presentation path validation
- Audio configuration validation

### Project Infrastructure ✓

- Directory structure for all components
- Configuration management system
- Logging infrastructure
- Test framework setup
- Dependency management
- Basic functionality validation

## Key Features Implemented

### Data Model Features
- Automatic [Orik] tag extraction from speaker notes
- Personality-driven response configuration
- System health monitoring and status tracking
- Audio configuration with Amazon Polly integration
- Comprehensive data validation and error handling

### Validation Features
- Input sanitization and type checking
- Range validation for numeric parameters
- File path and format validation
- Content length and safety validation
- Error handling with descriptive messages

### Testing Infrastructure
- Unit tests for all data models
- Validation function testing
- Basic functionality verification
- Test data generation utilities

## Next Steps

The foundation is now complete. The next tasks will implement:

1. **Task 2**: SpeakerNotesTool MCP server
2. **Task 3**: DigAtAaronTool MCP server  
3. **Task 4**: TextToSpeechTool MCP server
4. **Task 5**: AudioPlaybackService
5. **Task 6**: PresentationMonitor service
6. **Task 7**: Orik Agent Controller
7. **Task 8**: OrikAvatarUI component
8. **Task 9**: Error handling and recovery system
9. **Task 10**: Main application orchestrator

## Configuration

The system uses JSON-based configuration with the following key sections:
- Orik personality settings
- Voice and TTS configuration
- Presentation monitoring settings
- Audio playback configuration
- MCP server endpoints
- Logging configuration
- UI settings

## Testing

Run the basic functionality test to verify the core models:

```bash
python3 test_basic_functionality.py
```

All tests should pass, confirming that the data models and validation functions are working correctly.