# 🎪 Orik Presentation Co-host - How to Run Everything

This guide shows you how to run all components of the Orik Presentation Co-host system.

## 🚀 Quick Start

### Option 1: Run Complete System (Recommended)
```bash
cd orik-presentation-cohost
python3 run_orik_system.py
```

### Option 2: Quick Component Testing
```bash
# Test individual components
python3 quick_test.py avatar    # Visual avatar UI
python3 quick_test.py agent     # AI agent core
python3 quick_test.py system    # Complete system

# Run all tests
python3 quick_test.py tests
```

## 📋 Prerequisites

### Required Dependencies
```bash
# Install Python dependencies
pip3 install --break-system-packages -r requirements.txt

# Ensure tkinter is available (for Avatar UI)
brew install python-tk  # macOS with Homebrew

# For PowerPoint integration on macOS
pip3 install --break-system-packages py-applescript
```

### AWS Configuration (for TTS)
```bash
# Set up AWS credentials for Polly TTS
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"
```

## 🎯 Individual Components

### 1. Orik Avatar UI (Visual Interface)
```bash
python3 demo_avatar_ui.py
```
**What it does:**
- Shows Orik's ghostly avatar with animations
- Displays speaking states and system status
- Visual error indicators and recovery

### 2. Orik AI Agent (Core Intelligence)
```bash
python3 demo_orik_agent.py
```
**What it does:**
- Demonstrates Orik's sarcastic personality
- Shows response generation for different scenarios
- Tests personality configuration

### 3. Text-to-Speech System
```bash
python3 test_tts_basic_functionality.py
```
**What it does:**
- Tests Amazon Polly integration
- Demonstrates voice configuration
- Audio playback testing

### 4. Sarcastic One-liners
```bash
python3 test_dig_at_aaron_mcp.py
```
**What it does:**
- Tests the DigAtAaron tool
- Shows random sarcastic comments
- Demonstrates variety and context awareness

### 5. MCP Server Testing
```bash
python3 test_mcp_server.py
```
**What it does:**
- Tests MCP (Model Context Protocol) functionality
- Validates tool integration
- Server communication testing

## 🔧 MCP Servers (Background Services)

The system uses MCP servers for different tools. Run these in separate terminals:

### Terminal 1: Speaker Notes Server
```bash
python3 src/mcp_tools/run_speaker_notes_server.py
```

### Terminal 2: Text-to-Speech Server
```bash
python3 src/mcp_tools/run_text_to_speech_server.py
```

### Terminal 3: DigAtAaron Server
```bash
python3 src/mcp_tools/run_dig_at_aaron_server.py
```

## 🎮 Interactive Mode

Run the system in interactive mode for manual control:

```bash
python3 run_orik_system.py --mode interactive
```

**Interactive Commands:**
- `s` - Toggle Orik's speaking state
- `e` - Show error message
- `c` - Clear error
- `q` - Quit
- `h` - Show help

## 🧪 Testing

### Run All Unit Tests
```bash
python3 -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Test Avatar UI
python3 -m pytest tests/test_orik_avatar_ui.py -v

# Test Agent Controller
python3 -m pytest tests/test_orik_agent_controller.py -v

# Test MCP Tools
python3 -m pytest tests/test_*_tool.py -v

# Integration Tests
python3 -m pytest tests/test_avatar_integration.py -v
```

### Quick Test Script
```bash
# Test specific components
python3 quick_test.py avatar
python3 quick_test.py agent
python3 quick_test.py tts
python3 quick_test.py system

# Run all tests
python3 quick_test.py tests
```

## 🎪 Complete System Workflow

### 1. Automated Demo Mode (Default)
```bash
python3 run_orik_system.py
```
This runs a complete simulation showing:
- MCP servers starting up
- Avatar UI initialization
- Simulated presentation workflow
- Orik responding to slides
- Error handling and recovery

### 2. Interactive Mode
```bash
python3 run_orik_system.py --mode interactive
```
Allows manual control of Orik's behavior.

### 3. Skip MCP Servers (if already running)
```bash
python3 run_orik_system.py --no-servers
```

## 🔍 What Each Component Shows

### Avatar UI Demo
- **Visual**: Animated Orik avatar with blinking eyes
- **States**: Speaking vs idle animations
- **Status**: System health indicators
- **Errors**: Red error messages and recovery

### Agent Demo
- **Personality**: Sarcasm level and interruption frequency
- **Responses**: Different response types (tagged, random, contextual)
- **Scenarios**: Various presentation situations

### TTS Demo
- **Voices**: Amazon Polly voice configuration
- **Audio**: Actual speech synthesis and playback
- **SSML**: Emphasis and sarcastic delivery

### Complete System Demo
- **Integration**: All components working together
- **Workflow**: Realistic presentation monitoring
- **Real-time**: Live status updates and animations

## 🐛 Troubleshooting

### Common Issues

**tkinter not available:**
```bash
brew install python-tk  # macOS
sudo apt-get install python3-tk  # Ubuntu
```

**AWS credentials not set:**
```bash
aws configure  # Set up AWS CLI
# OR set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

**MCP servers not starting:**
- Check if ports are already in use
- Ensure all dependencies are installed
- Check firewall settings

**Avatar window not appearing:**
- Ensure you're in a GUI environment
- Check display settings
- Try running in interactive mode

### Debug Mode
```bash
# Run with debug logging
PYTHONPATH=src python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# Then run your component
"
```

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Avatar UI     │    │   Orik Agent     │    │   MCP Servers   │
│   (Visual)      │◄──►│   (Core AI)      │◄──►│   (Tools)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         │                        ▼                       │
         │              ┌──────────────────┐              │
         │              │   Presentation   │              │
         └─────────────►│   Monitor        │◄─────────────┘
                        └──────────────────┘
```

## 🎯 Next Steps

1. **Run the complete system**: `python3 run_orik_system.py`
2. **Test individual components**: Use `quick_test.py`
3. **Create a presentation**: Add `[Orik]` tags to PowerPoint speaker notes
4. **Customize personality**: Edit `src/models/personality.py`
5. **Add more one-liners**: Edit `src/mcp_tools/dig_at_aaron_tool.py`

## 🎉 Success Indicators

When everything is working correctly, you should see:
- ✅ Orik avatar window with animations
- ✅ MCP servers running without errors
- ✅ Audio playback for TTS
- ✅ Real-time status updates
- ✅ Smooth state transitions

**Enjoy your sarcastic AI presentation co-host!** 🎪