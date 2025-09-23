# Orik MCP Tools

This directory contains MCP (Model Context Protocol) servers for the Orik Presentation Co-host system.

## Available Tools

### SpeakerNotesTool
Extracts speaker notes from Microsoft PowerPoint presentations on macOS and parses [Orik] tags.

### DigAtAaronTool  
Generates sarcastic one-liners targeting Aaron with context awareness and repetition avoidance.

## SpeakerNotesTool MCP Server

The SpeakerNotesTool is an MCP server that extracts speaker notes from Microsoft PowerPoint presentations on macOS and parses [Orik] tags for the Orik Presentation Co-host system.

## Features

- **PowerPoint Integration**: Uses AppleScript to interact with Microsoft PowerPoint on macOS
- **Orik Tag Parsing**: Extracts content tagged with `[Orik]` markers from speaker notes
- **Real-time Monitoring**: Can get current slide information from active presentations
- **Robust Error Handling**: Graceful degradation when PowerPoint is not available
- **Comprehensive Testing**: Full test suite with mocked PowerPoint interactions

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required dependencies:
   ```bash
   pip install pytest pytest-asyncio
   ```
3. Make sure Microsoft PowerPoint is installed on macOS

## Usage

### As an MCP Server

1. Start the MCP server:
   ```bash
   python3 src/mcp_tools/run_speaker_notes_server.py
   ```

2. The server provides two tools:
   - `extract_speaker_notes`: Extract notes from a specific slide
   - `get_current_slide_notes`: Get notes from the currently active slide

### MCP Configuration

Add to your MCP configuration file:

```json
{
  "mcpServers": {
    "speaker-notes-tool": {
      "command": "python3",
      "args": ["src/mcp_tools/run_speaker_notes_server.py"],
      "cwd": ".",
      "env": {
        "PYTHONPATH": "src",
        "LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": [
        "extract_speaker_notes",
        "get_current_slide_notes"
      ]
    }
  }
}
```

### Direct Usage

```python
from mcp_tools.speaker_notes_tool import SpeakerNotesTool
import asyncio

async def main():
    tool = SpeakerNotesTool()
    
    # Get current slide notes
    result = await tool.get_current_slide_notes()
    print(result)
    
    # Extract notes from specific slide
    result = await tool.extract_speaker_notes(slide_index=0, presentation_path="my_presentation.pptx")
    print(result)

asyncio.run(main())
```

## Orik Tag Format

The tool recognizes `[Orik]` tags in speaker notes:

```
Regular speaker notes here.

[Orik] This content will be extracted for Orik to respond to

More regular notes.

[Orik] Another comment for Orik
This content spans multiple lines
until the next tag or end of notes

[Orik] Third sarcastic comment
```

### Tag Rules

- Tags are case-insensitive: `[Orik]`, `[orik]`, `[ORIK]` all work
- Content is captured from the tag until the next `[` character or end of notes
- Empty tags (just whitespace after `[Orik]`) are filtered out
- Multiple tags per slide are supported
- Content can span multiple lines

## API Reference

### SpeakerNotesTool Methods

#### `extract_speaker_notes(slide_index: int, presentation_path: str = "") -> Dict[str, Any]`

Extract speaker notes from a specific slide.

**Parameters:**
- `slide_index`: 0-based slide index
- `presentation_path`: Path to presentation file (optional for active presentation)

**Returns:**
```json
{
  "success": true,
  "slide_data": {
    "slide_index": 0,
    "slide_title": "Introduction",
    "speaker_notes": "Welcome everyone [Orik] Time for Aaron to embarrass himself",
    "presentation_path": "presentation.pptx",
    "timestamp": "2023-12-07T10:30:00"
  },
  "orik_content": {
    "raw_text": "Welcome everyone [Orik] Time for Aaron to embarrass himself",
    "extracted_tags": ["Time for Aaron to embarrass himself"],
    "context": "Introduction",
    "has_orik_tags": true,
    "tag_count": 1
  },
  "has_orik_tags": true,
  "tag_count": 1,
  "extracted_tags": ["Time for Aaron to embarrass himself"]
}
```

#### `get_current_slide_notes() -> Dict[str, Any]`

Get speaker notes for the currently active slide in PowerPoint.

**Returns:** Same format as `extract_speaker_notes`

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/test_speaker_notes_tool.py -v

# Run specific test categories
python -m pytest tests/test_speaker_notes_tool.py::TestOrikTagExtraction -v
python -m pytest tests/test_speaker_notes_tool.py::TestSpeakerNotesTool -v

# Test with the demo script
python test_mcp_server.py
```

## PowerPoint Setup

For the tool to work with PowerPoint:

1. **Open PowerPoint**: The application must be running
2. **Open a Presentation**: Have a presentation file open
3. **Add Speaker Notes**: Add notes to slides with `[Orik]` tags
4. **Slide Selection**: Make sure a slide is selected for current slide detection

### Example Speaker Notes

```
This slide introduces our new feature.

[Orik] Oh great, another "revolutionary" feature that's probably just a button color change

Key benefits include:
- Improved user experience
- Better performance
- Enhanced security

[Orik] Let me guess, "enhanced security" means they finally fixed the password field
```

## Troubleshooting

### Common Issues

1. **"PowerPoint not running" errors**
   - Ensure Microsoft PowerPoint is open
   - Make sure you have a presentation loaded
   - Check that PowerPoint has proper permissions

2. **AppleScript timeout errors**
   - PowerPoint might be busy or unresponsive
   - Try closing and reopening PowerPoint
   - Reduce the number of open presentations

3. **No Orik tags found**
   - Check that tags are properly formatted: `[Orik]`
   - Ensure there's content after the tag
   - Verify the slide has speaker notes

4. **Permission errors**
   - Grant accessibility permissions to Terminal/IDE in System Preferences
   - Allow AppleScript to control PowerPoint

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Limitations

- **macOS Only**: Uses AppleScript, which is macOS-specific
- **PowerPoint Required**: Requires Microsoft PowerPoint (not Keynote or other apps)
- **Active Presentation**: Works with currently open presentations
- **Single Presentation**: Designed for one active presentation at a time

## Future Enhancements

- Support for other presentation software (Keynote, Google Slides)
- File-based extraction for offline processing
- Windows COM automation support
- Batch processing of multiple presentations
- Real-time slide change monitoring

---

# DigAtAaronTool MCP Server

The DigAtAaronTool is an MCP server that generates sarcastic one-liners targeting Aaron with context awareness and repetition avoidance for the Orik Presentation Co-host system.

## Features

- **Curated Sarcasm Library**: Over 30 hand-crafted sarcastic one-liners targeting Aaron
- **Context Awareness**: Selects appropriate digs based on slide content and presentation context
- **Repetition Avoidance**: Intelligent selection algorithm that avoids recently used digs
- **Category Variety**: Multiple categories including presentation skills, technical competence, design choices, and general sarcasm
- **Usage Tracking**: Comprehensive statistics and usage history management
- **Weighted Selection**: Prefers less-used categories and digs for better variety

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required dependencies:
   ```bash
   pip install pytest pytest-asyncio
   ```

## Usage

### As an MCP Server

1. Start the MCP server:
   ```bash
   python3 src/mcp_tools/run_dig_at_aaron_server.py
   ```

2. The server provides three tools:
   - `get_aaron_dig`: Generate a sarcastic one-liner with optional context
   - `reset_dig_history`: Reset usage history for a new presentation
   - `get_dig_stats`: Get current usage statistics and library information

### MCP Configuration

Add to your MCP configuration file:

```json
{
  "mcpServers": {
    "dig-at-aaron-tool": {
      "command": "python3",
      "args": ["src/mcp_tools/run_dig_at_aaron_server.py"],
      "cwd": ".",
      "env": {
        "PYTHONPATH": "src",
        "LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": [
        "get_aaron_dig",
        "reset_dig_history",
        "get_dig_stats"
      ]
    }
  }
}
```

### Direct Usage

```python
from mcp_tools.dig_at_aaron_tool import DigAtAaronTool
import asyncio

async def main():
    tool = DigAtAaronTool()
    
    # Get a random dig
    result = await tool.get_aaron_dig()
    print(result["dig"])
    
    # Get a context-aware dig
    result = await tool.get_aaron_dig(context="Aaron is about to demo the security feature")
    print(result["dig"])
    
    # Reset history for new presentation
    await tool.reset_dig_history()
    
    # Get usage statistics
    stats = await tool.get_dig_stats()
    print(stats)

asyncio.run(main())
```

## Dig Categories

The tool organizes sarcastic one-liners into several categories:

### Presentation Skills
Targets Aaron's presentation and speaking abilities:
- "Sure, let's all pretend Aaron rehearsed this part"
- "Oh look, Aaron's reading directly from his slides again"
- "Wow Aaron, that transition was smoother than sandpaper"

### Technical Competence  
Focuses on Aaron's technical knowledge and explanations:
- "Wow Aaron, groundbreaking insight... from 2012"
- "Aaron's technical depth is about as shallow as a puddle"
- "I'm sure Aaron totally understands what he just said"

### Design Choices
Comments on Aaron's slide design and visual choices:
- "Another slide where Aaron proves bullet points are a design choice"
- "Aaron's slide design aesthetic: 'More is more'"
- "I see Aaron went with the 'wall of text' approach again"

### General Sarcasm
Broadly applicable sarcastic comments:
- "Oh brilliant, Aaron. Just brilliant"
- "Aaron never fails to... well, actually he fails quite often"
- "I'm sure the audience is hanging on Aaron's every word"

### Context-Specific
Special digs for specific presentation topics:
- **Demo**: "I'm sure this demo will work perfectly, just like Aaron's last one"
- **Architecture**: "Aaron's architecture diagrams are as clear as mud"
- **Performance**: "Aaron's performance metrics are about as reliable as his predictions"
- **Security**: "Aaron's security approach: 'Hope for the best'"

## API Reference

### DigAtAaronTool Methods

#### `get_aaron_dig(context: Optional[str] = None, used_digs: Optional[List[str]] = None, avoid_repetition: bool = True) -> Dict[str, Any]`

Generate a sarcastic one-liner targeting Aaron.

**Parameters:**
- `context`: Optional context about current slide/topic to influence selection
- `used_digs`: List of previously used digs to avoid repetition
- `avoid_repetition`: Whether to avoid recently used digs

**Returns:**
```json
{
  "success": true,
  "dig": "Sure, let's all pretend Aaron rehearsed this part",
  "response": {
    "response_text": "Sure, let's all pretend Aaron rehearsed this part",
    "confidence": 0.9,
    "response_type": "random_dig",
    "generation_time": "2023-12-07T10:30:00",
    "source_content": "Aaron's presentation introduction",
    "is_high_confidence": true,
    "word_count": 9,
    "estimated_duration_seconds": 3.6
  },
  "usage_stats": {
    "used_digs_count": 1,
    "category_usage": {"presentation_skills": 1},
    "last_category": "presentation_skills"
  },
  "context_used": true
}
```

#### `reset_dig_history() -> Dict[str, Any]`

Reset the dig usage history for a new presentation.

**Returns:**
```json
{
  "success": true,
  "message": "Dig usage history reset successfully",
  "timestamp": "2023-12-07T10:30:00"
}
```

#### `get_dig_stats() -> Dict[str, Any]`

Get current dig usage statistics and library information.

**Returns:**
```json
{
  "success": true,
  "usage_stats": {
    "used_digs_count": 5,
    "category_usage": {
      "presentation_skills": 2,
      "technical_competence": 1,
      "general_sarcasm": 2
    },
    "last_category": "general_sarcasm"
  },
  "library_stats": {
    "total_presentation_skills": 8,
    "total_technical_competence": 8,
    "total_design_choices": 8,
    "total_general_sarcasm": 8,
    "context_specific_categories": 5
  },
  "timestamp": "2023-12-07T10:30:00"
}
```

## Context Awareness

The tool uses context to select appropriate digs:

### Keyword Matching
- **"demo"** → Selects demo-specific digs
- **"architecture"** → Focuses on technical architecture digs  
- **"security"** → Uses security-related sarcasm
- **"performance"** → Targets performance claims
- **"slide", "design"** → Comments on visual design choices
- **"technical", "code"** → Focuses on technical competence
- **"present", "speak"** → Targets presentation skills

### Example Context Usage
```python
# Demo context
await tool.get_aaron_dig(context="Aaron is about to demo the new feature")
# Might return: "I'm sure this demo will work perfectly, just like Aaron's last one"

# Architecture context  
await tool.get_aaron_dig(context="Here's the system architecture Aaron designed")
# Might return: "Aaron's architecture diagrams are as clear as mud"

# General context
await tool.get_aaron_dig(context="Aaron's presentation skills")
# Might return: "Sure, let's all pretend Aaron rehearsed this part"
```

## Repetition Avoidance Algorithm

The tool uses several strategies to ensure variety:

1. **Usage Tracking**: Maintains a set of recently used digs
2. **Category Rotation**: Avoids using the same category consecutively when possible
3. **Weighted Selection**: Prefers less-used categories using weighted random selection
4. **History Reset**: Clears usage history when all digs have been used
5. **Presentation Reset**: Allows manual reset for new presentations

## Testing

Run the comprehensive test suite:

```bash
# Run all DigAtAaronTool tests
python -m pytest tests/test_dig_at_aaron_tool.py -v

# Run specific test categories
python -m pytest tests/test_dig_at_aaron_tool.py::TestDigLibrary -v
python -m pytest tests/test_dig_at_aaron_tool.py::TestDigSelector -v
python -m pytest tests/test_dig_at_aaron_tool.py::TestDigAtAaronTool -v

# Run integration tests
python -m pytest tests/test_dig_at_aaron_tool.py::TestDigAtAaronToolIntegration -v

# Test with the standalone script
python src/mcp_tools/dig_at_aaron_tool.py
```

## Performance Characteristics

- **Response Time**: < 50ms for dig selection
- **Memory Usage**: < 5MB for dig library and usage tracking
- **Variety**: > 50% unique digs over 20 consecutive calls
- **Context Accuracy**: Appropriate category selection based on keywords

## Troubleshooting

### Common Issues

1. **Repetitive digs**
   - Check if `avoid_repetition` is enabled
   - Reset dig history with `reset_dig_history()`
   - Verify sufficient digs in library categories

2. **Context not working**
   - Ensure context string contains relevant keywords
   - Check that context-specific categories have content
   - Verify context is being passed correctly

3. **Low variety**
   - Reset usage history periodically
   - Check category usage statistics
   - Ensure multiple categories are available

### Debug Mode

Enable debug logging to see selection process:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Will show category selection and dig choice reasoning
result = await tool.get_aaron_dig(context="demo")
```

## Extending the Library

To add new digs or categories:

1. **Add to existing categories**: Append to the appropriate list in `DigLibrary`
2. **Add new context categories**: Add entries to `CONTEXT_SPECIFIC` dictionary
3. **Update tests**: Add test cases for new content
4. **Verify quality**: Ensure digs are appropriate length and tone

Example:
```python
# Add to existing category
DigLibrary.PRESENTATION_SKILLS.append("Aaron's new sarcastic dig here")

# Add new context category
DigLibrary.CONTEXT_SPECIFIC["deployment"] = [
    "Aaron's deployment strategy: 'Deploy and pray'",
    "I'm sure Aaron's deployment will go smoothly"
]
```