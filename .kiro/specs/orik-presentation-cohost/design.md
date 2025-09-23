# Design Document

## Overview

The Orik Presentation Co-host system is a Strands agent-based application that monitors presentation software, extracts tagged content from speaker notes, generates sarcastic responses using Orik's personality, and delivers them via text-to-speech. The system uses the Model Context Protocol (MCP) architecture to integrate various tools and services, creating a seamless real-time presentation enhancement experience.

The core architecture follows a reactive event-driven pattern where slide changes trigger a pipeline of operations: note extraction → content filtering → response generation → speech synthesis → audio playback. The system maintains Orik's personality through a combination of prompt engineering and pre-defined response libraries.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Presentation  │    │   Orik Agent     │    │   Audio Output  │
│   Software      │───▶│   Controller     │───▶│   System        │
│   (PowerPoint)  │    │                  │    │   (Speakers)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       ▲
         │                        ▼                       │
         │              ┌──────────────────┐              │
         │              │   MCP Tools      │              │
         │              │   Ecosystem      │              │
         │              └──────────────────┘              │
         │                        │                       │
         │                        ▼                       │
         │              ┌──────────────────┐              │
         │              │   Amazon Polly   │──────────────┘
         │              │   TTS Service    │
         │              └──────────────────┘
         │
         ▼
┌─────────────────┐
│   Visual UI     │
│   (Orik Avatar) │
└─────────────────┘
```

### Component Architecture

The system consists of four main layers:

1. **Presentation Integration Layer**: Monitors slide changes and extracts speaker notes
2. **Agent Processing Layer**: Strands agent with Orik personality and MCP tools
3. **Service Integration Layer**: Amazon Polly TTS and audio playback services
4. **User Interface Layer**: Visual avatar and system status display

## Components and Interfaces

### 1. Orik Agent Controller

**Purpose**: Central orchestrator that manages the entire workflow and maintains Orik's personality.

**Key Responsibilities**:
- Initialize and manage MCP client connections
- Coordinate between presentation monitoring and response generation
- Maintain conversation context and personality state
- Handle error recovery and system resilience

**Interface**:
```python
class OrikAgentController:
    def __init__(self, mcp_clients: List[MCPClient])
    async def start_monitoring(self) -> None
    async def stop_monitoring(self) -> None
    async def process_slide_change(self, slide_data: SlideData) -> None
    def get_system_status(self) -> SystemStatus
```

### 2. SpeakerNotesTool (MCP Tool)

**Purpose**: Extracts speaker notes from presentation software and filters for Orik tags.

**Key Responsibilities**:
- Connect to presentation software APIs (PowerPoint COM, Google Slides API)
- Monitor slide change events
- Extract and parse speaker notes content
- Filter and extract [Orik] tagged content
- Handle multiple presentation software formats

**Interface**:
```python
@mcp.tool(description="Reads presentation speaker notes and extracts Orik-tagged content")
def extract_speaker_notes(slide_index: int, presentation_path: str) -> SpeakerNotesResult:
    """
    Args:
        slide_index: Current slide number (0-based)
        presentation_path: Path to presentation file
    
    Returns:
        SpeakerNotesResult with extracted Orik content and metadata
    """
```

**Integration Strategy**:
- **PowerPoint**: Use `win32com.client` for Windows COM automation
- **Google Slides**: Use Google Slides API with OAuth authentication
- **Keynote**: Use AppleScript automation on macOS
- **Generic**: File-based monitoring for exported notes

### 3. DigAtAaronTool (MCP Tool)

**Purpose**: Provides a library of pre-written sarcastic one-liners targeting Aaron.

**Key Responsibilities**:
- Maintain a curated library of sarcastic comments
- Select appropriate one-liners based on context
- Ensure variety in repeated presentations
- Track usage to avoid repetition

**Interface**:
```python
@mcp.tool(description="Generates random sarcastic one-liners targeting Aaron")
def get_aaron_dig(context: Optional[str] = None, used_digs: List[str] = []) -> DigResult:
    """
    Args:
        context: Optional context about current slide/topic
        used_digs: List of previously used digs to avoid repetition
    
    Returns:
        DigResult with selected one-liner and metadata
    """
```

**One-liner Categories**:
- Presentation skills ("Sure, let's all pretend Aaron rehearsed this part")
- Technical competence ("Wow Aaron, groundbreaking insight… from 2012")
- Design choices ("Another slide where Aaron proves bullet points are a design choice")
- General sarcasm ("Oh brilliant, Aaron. Just brilliant")

### 4. TextToSpeechTool (MCP Tool)

**Purpose**: Converts Orik's text responses to speech using Amazon Polly.

**Key Responsibilities**:
- Interface with Amazon Polly API
- Configure voice parameters for Orik's personality
- Handle audio format conversion
- Manage TTS request queuing and rate limiting
- Cache frequently used phrases

**Interface**:
```python
@mcp.tool(description="Converts text to speech using Amazon Polly")
def synthesize_speech(text: str, voice_config: VoiceConfig) -> AudioResult:
    """
    Args:
        text: Text to convert to speech
        voice_config: Voice settings (voice_id, speed, pitch, etc.)
    
    Returns:
        AudioResult with audio data and metadata
    """
```

**Voice Configuration**:
- **Voice**: Matthew (Neural) for sarcastic male voice
- **Speed**: 1.1x (slightly faster for snark effect)
- **Pitch**: -10% (slightly lower for authority)
- **SSML Support**: For emphasis and pauses

### 5. AudioPlaybackService

**Purpose**: Manages audio output and speaker integration.

**Key Responsibilities**:
- Queue and play TTS audio
- Handle audio device selection
- Manage volume and audio mixing
- Provide playback status and controls

**Interface**:
```python
class AudioPlaybackService:
    def __init__(self, device_id: Optional[str] = None)
    async def play_audio(self, audio_data: bytes, format: AudioFormat) -> None
    def set_volume(self, volume: float) -> None
    def get_playback_status(self) -> PlaybackStatus
    async def stop_playback(self) -> None
```

### 6. PresentationMonitor

**Purpose**: Monitors presentation software for slide changes and events.

**Key Responsibilities**:
- Detect slide change events across different presentation software
- Extract current slide metadata
- Handle presentation software lifecycle events
- Provide fallback monitoring methods

**Interface**:
```python
class PresentationMonitor:
    def __init__(self, software_type: PresentationSoftware)
    async def start_monitoring(self, callback: Callable[[SlideEvent], None]) -> None
    async def stop_monitoring(self) -> None
    def get_current_slide(self) -> SlideInfo
    def is_presentation_active(self) -> bool
```

### 7. OrikAvatarUI

**Purpose**: Provides visual feedback showing Orik's activity and status.

**Key Responsibilities**:
- Display Orik's ghostly avatar
- Animate avatar during speech
- Show system status and errors
- Provide manual controls for demo purposes

**Interface**:
```python
class OrikAvatarUI:
    def __init__(self, window_config: WindowConfig)
    def show_avatar(self) -> None
    def hide_avatar(self) -> None
    def set_speaking_state(self, is_speaking: bool) -> None
    def show_error(self, error_message: str) -> None
    def update_status(self, status: str) -> None
```

## Data Models

### Core Data Structures

```python
@dataclass
class SlideData:
    slide_index: int
    slide_title: str
    speaker_notes: str
    presentation_path: str
    timestamp: datetime

@dataclass
class OrikContent:
    raw_text: str
    extracted_tags: List[str]
    context: Optional[str]
    slide_reference: SlideData

@dataclass
class OrikResponse:
    response_text: str
    confidence: float
    response_type: ResponseType  # TAGGED, RANDOM_DIG, CONTEXTUAL
    generation_time: datetime

@dataclass
class AudioResult:
    audio_data: bytes
    format: AudioFormat
    duration_ms: int
    voice_config: VoiceConfig

@dataclass
class SystemStatus:
    is_monitoring: bool
    presentation_connected: bool
    tts_available: bool
    audio_ready: bool
    last_activity: datetime
    error_state: Optional[str]
```

### Personality Configuration

```python
@dataclass
class OrikPersonality:
    base_prompt: str
    sarcasm_level: float  # 0.0 to 1.0
    interruption_frequency: float  # 0.0 to 1.0
    aaron_dig_probability: float  # 0.0 to 1.0
    response_templates: List[str]
    forbidden_topics: List[str]
```

## Error Handling

### Error Categories and Strategies

1. **Presentation Software Connection Errors**
   - **Strategy**: Graceful degradation with file-based monitoring
   - **Recovery**: Automatic retry with exponential backoff
   - **User Feedback**: Status indicator showing connection state

2. **TTS Service Errors**
   - **Strategy**: Queue requests and retry failed calls
   - **Fallback**: Local TTS engine if available
   - **Recovery**: Cache successful responses to reduce API calls

3. **Audio Playback Errors**
   - **Strategy**: Multiple audio backend support (pygame, pyaudio, system default)
   - **Recovery**: Automatic device switching
   - **User Feedback**: Audio status indicator

4. **Agent Processing Errors**
   - **Strategy**: Continue operation with reduced functionality
   - **Recovery**: Reset agent state and reinitialize
   - **Logging**: Comprehensive error logging for debugging

### Error Recovery Patterns

```python
class ErrorRecoveryManager:
    def __init__(self):
        self.retry_strategies = {
            PresentationError: ExponentialBackoffRetry(max_attempts=3),
            TTSError: LinearRetry(max_attempts=5, delay=1.0),
            AudioError: ImmediateRetry(max_attempts=2)
        }
    
    async def handle_error(self, error: Exception, context: str) -> RecoveryResult:
        # Implement recovery logic based on error type
        pass
```

## Testing Strategy

### Unit Testing

1. **MCP Tools Testing**
   - Mock presentation software APIs
   - Test tag extraction logic
   - Validate response generation
   - Test TTS integration

2. **Agent Behavior Testing**
   - Personality consistency tests
   - Response appropriateness validation
   - Context handling verification
   - Error scenario testing

3. **Integration Testing**
   - End-to-end workflow testing
   - Multi-tool coordination testing
   - Error recovery testing
   - Performance benchmarking

### Test Data and Scenarios

```python
# Test presentation with various Orik tags
TEST_SLIDES = [
    {
        "notes": "[Orik] This is where Aaron usually loses everyone",
        "expected_response_type": "TAGGED"
    },
    {
        "notes": "Regular speaker notes without tags",
        "expected_response_type": "RANDOM_DIG"
    },
    {
        "notes": "[Orik] [Orik] Multiple tags on same slide",
        "expected_response_type": "TAGGED"
    }
]
```

### Performance Testing

- **Response Time**: < 2 seconds from slide change to audio output
- **Memory Usage**: < 100MB baseline, < 200MB during active processing
- **CPU Usage**: < 10% during idle monitoring, < 30% during response generation
- **Audio Latency**: < 500ms from TTS completion to audio start

### Demo Testing Scenarios

1. **Happy Path Demo**: Smooth presentation with various Orik interactions
2. **Error Recovery Demo**: Simulated failures and recovery
3. **Personality Showcase**: Demonstration of different response types
4. **Multi-slide Rapid Fire**: Quick slide changes to test responsiveness

## Security Considerations

### Data Privacy
- Speaker notes are processed locally when possible
- TTS requests to AWS Polly include only the response text, not original notes
- No persistent storage of presentation content

### API Security
- AWS credentials managed through IAM roles and environment variables
- Presentation software APIs accessed with minimal required permissions
- Rate limiting on external API calls

### System Security
- Sandboxed execution environment for MCP tools
- Input validation for all external data
- Secure handling of audio device access

## Deployment Architecture

### Development Environment
- Local development with mock presentation software
- Containerized MCP servers for consistent testing
- Hot-reload capability for rapid iteration

### Demo Environment
- Standalone executable with embedded dependencies
- Automatic presentation software detection
- Fallback modes for different operating systems

### Production Considerations
- Scalable MCP server deployment
- Load balancing for TTS services
- Monitoring and alerting for system health