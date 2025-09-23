# TextToSpeechTool MCP Server

The TextToSpeechTool is an MCP (Model Context Protocol) server that provides text-to-speech functionality using Amazon Polly. It's specifically configured for Orik's sarcastic personality with enhanced SSML processing and audio caching capabilities.

## Features

### Core Functionality
- **Amazon Polly Integration**: High-quality neural text-to-speech synthesis
- **Orik Voice Configuration**: Pre-configured with Matthew Neural voice optimized for sarcastic delivery
- **SSML Enhancement**: Automatic enhancement of text with emphasis and pauses for comedic effect
- **Audio Caching**: Intelligent caching system to reduce API calls and improve performance
- **Multiple Voice Support**: Access to all Amazon Polly voices with recommendations for Orik

### SSML Processing
- **Sarcastic Emphasis**: Automatically adds emphasis to sarcastic words like "brilliant", "perfect", "obviously"
- **Strategic Pauses**: Adds pauses after phrases like "Oh,", "Well,", "Sure," for comedic timing
- **Prosody Control**: Configurable speech rate, pitch, and volume for personality expression

### Audio Caching
- **Automatic Caching**: Caches synthesized audio to reduce API calls
- **Cache Management**: Tools to view cache statistics and clear cache when needed
- **Intelligent Key Generation**: Uses text content and voice configuration for cache keys

## Installation

### Prerequisites
```bash
# Install required Python packages
pip install boto3 mcp

# Configure AWS credentials (one of the following methods):
# 1. AWS CLI
aws configure

# 2. Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1

# 3. IAM roles (for EC2/Lambda deployment)
```

### Required AWS Permissions
The AWS credentials need the following Polly permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "polly:SynthesizeSpeech",
                "polly:DescribeVoices"
            ],
            "Resource": "*"
        }
    ]
}
```

## Usage

### Running the MCP Server
```bash
# From the project root
cd orik-presentation-cohost
python3 src/mcp_tools/run_text_to_speech_server.py
```

### MCP Configuration
Add to your MCP configuration file:
```json
{
  "mcpServers": {
    "text-to-speech-tool": {
      "command": "python3",
      "args": ["src/mcp_tools/run_text_to_speech_server.py"],
      "cwd": "orik-presentation-cohost",
      "env": {
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

## Available Tools

### 1. synthesize_speech
Convert text to speech using Amazon Polly with Orik's voice configuration.

**Parameters:**
- `text` (required): Text to convert to speech
- `voice_config` (optional): Voice configuration override
- `use_cache` (optional, default: true): Whether to use cached audio
- `use_ssml` (optional, default: true): Whether to enhance with SSML

**Example:**
```json
{
  "text": "Oh brilliant, Aaron. That's absolutely perfect.",
  "use_ssml": true,
  "use_cache": true
}
```

**Response:**
```json
{
  "success": true,
  "audio_data": "base64_encoded_mp3_data",
  "audio_result": {
    "format": "mp3",
    "duration_ms": 2500,
    "size_bytes": 15432
  },
  "cached": false,
  "ssml_used": true
}
```

### 2. get_voice_config
Get the current default voice configuration for Orik.

**Response:**
```json
{
  "success": true,
  "voice_config": {
    "voice_id": "Matthew",
    "speed": 1.1,
    "pitch": "-10%",
    "volume": 1.0,
    "engine": "neural"
  }
}
```

### 3. update_voice_config
Update the default voice configuration.

**Parameters:**
- `voice_id` (required): Amazon Polly voice ID
- `speed` (optional): Speech rate (0.5-2.0)
- `pitch` (optional): Pitch adjustment (e.g., "-10%")
- `volume` (optional): Volume level (0.0-1.0)
- `engine` (optional): Polly engine ("standard" or "neural")

### 4. get_available_voices
Get list of available voices from Amazon Polly with recommendations for Orik.

**Response:**
```json
{
  "success": true,
  "total_voices": 47,
  "english_voices": 24,
  "recommended_voices": [
    {
      "Id": "Matthew",
      "LanguageCode": "en-US",
      "Gender": "Male"
    }
  ]
}
```

### 5. test_tts_connection
Test connection to Amazon Polly service and perform a synthesis test.

**Response:**
```json
{
  "success": true,
  "connection_status": "connected",
  "synthesis_test": "passed",
  "region": "us-east-1",
  "default_voice": "Matthew"
}
```

### 6. get_cache_stats
Get audio cache statistics and usage information.

**Response:**
```json
{
  "success": true,
  "cache_stats": {
    "total_cached_items": 15,
    "total_files": 15,
    "total_size_bytes": 245760,
    "cache_directory": "/Users/user/.orik_cache/audio"
  }
}
```

### 7. clear_audio_cache
Clear the audio cache to free up disk space.

## Voice Configuration

### Default Orik Configuration
The tool comes pre-configured with settings optimized for Orik's sarcastic personality:

- **Voice**: Matthew (Neural) - Male English voice with good sarcasm delivery
- **Speed**: 1.1x - Slightly faster for snark effect
- **Pitch**: -10% - Slightly lower for authority and sarcasm
- **Engine**: Neural - Higher quality synthesis

### Recommended Alternative Voices
For different personality variations:
- **Brian** (en-GB): British accent for sophisticated sarcasm
- **Russell** (en-AU): Australian accent for laid-back sarcasm
- **Joey** (en-US): Younger male voice for playful sarcasm

## SSML Enhancement

The tool automatically enhances text with SSML tags for better sarcastic delivery:

### Automatic Emphasis
Words like "brilliant", "perfect", "obviously", "clearly" get emphasis tags:
```xml
<emphasis level="strong">brilliant</emphasis>
```

### Strategic Pauses
Pauses are added after certain phrases for comedic timing:
```xml
Oh,<break time="0.5s"/> that's interesting...
```

### Full SSML Example
Input: "Sure, Aaron. That's brilliant."
Output:
```xml
<speak>
  <prosody rate="1.1" pitch="-10%">
    <emphasis level="strong">Sure</emphasis>,<break time="0.5s"/> Aaron. 
    That's <emphasis level="strong">brilliant</emphasis>.
  </prosody>
</speak>
```

## Caching System

### Cache Location
- **Default**: `~/.orik_cache/audio/`
- **Configurable**: Pass `cache_dir` parameter to TextToSpeechTool constructor

### Cache Key Generation
Cache keys are generated from:
- Text content
- Voice ID
- Speed setting
- Pitch setting
- Engine type

### Cache Management
- Automatic cleanup of stale entries
- Metadata tracking for cache statistics
- Manual cache clearing capability

## Error Handling

### Common Issues and Solutions

1. **AWS Credentials Not Found**
   ```
   Error: NoCredentialsError
   Solution: Configure AWS credentials using aws configure or environment variables
   ```

2. **Polly Service Unavailable**
   ```
   Error: Connection failed
   Solution: Check internet connection and AWS service status
   ```

3. **Invalid Voice Configuration**
   ```
   Error: voice_id cannot be empty
   Solution: Provide valid voice configuration parameters
   ```

4. **Rate Limiting**
   ```
   Error: TooManyRequestsException
   Solution: Implement exponential backoff or use caching more aggressively
   ```

## Testing

### Unit Tests
```bash
# Run all tests
python3 -m pytest tests/test_text_to_speech_tool.py -v

# Run specific test categories
python3 -m pytest tests/test_text_to_speech_tool.py::TestSSMLProcessor -v
python3 -m pytest tests/test_text_to_speech_tool.py::TestAudioCache -v
```

### Basic Functionality Test
```bash
# Test without AWS credentials
python3 test_tts_basic_functionality.py
```

### Integration Test
```bash
# Test with AWS credentials (requires boto3 and AWS setup)
python3 src/mcp_tools/text_to_speech_tool.py
```

## Performance Considerations

### API Costs
- Amazon Polly charges per character synthesized
- Caching significantly reduces costs for repeated phrases
- Neural voices cost more than standard voices but provide better quality

### Response Times
- First synthesis: ~1-3 seconds (includes API call)
- Cached responses: ~50-100ms
- Network latency affects initial synthesis time

### Storage
- MP3 audio files are relatively small (~1KB per second of audio)
- Cache directory can grow over time
- Regular cache cleanup recommended for long-running systems

## Integration with Orik System

The TextToSpeechTool integrates with other Orik components:

1. **SpeakerNotesTool**: Provides text content for synthesis
2. **DigAtAaronTool**: Provides sarcastic one-liners for synthesis
3. **AudioPlaybackService**: Plays the synthesized audio
4. **OrikAgentController**: Orchestrates the TTS workflow

## Troubleshooting

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export FASTMCP_LOG_LEVEL=DEBUG
```

### Common Debugging Steps
1. Test AWS credentials: `aws sts get-caller-identity`
2. Test Polly access: `aws polly describe-voices --region us-east-1`
3. Check cache permissions: Verify write access to cache directory
4. Validate voice configuration: Use `get_voice_config` tool
5. Test connection: Use `test_tts_connection` tool

### Log Analysis
Key log messages to look for:
- "Successfully initialized Polly client" - AWS connection OK
- "Retrieved cached audio" - Cache working
- "Successfully synthesized X bytes" - Synthesis successful
- "Polly API error" - AWS service issues

## Future Enhancements

Potential improvements for future versions:
- Support for additional TTS providers (Azure, Google)
- Real-time streaming synthesis
- Voice cloning for custom Orik voice
- Emotion-based SSML enhancement
- Advanced caching strategies (LRU, size-based)
- Audio format conversion (WAV, OGG)
- Batch synthesis for multiple texts