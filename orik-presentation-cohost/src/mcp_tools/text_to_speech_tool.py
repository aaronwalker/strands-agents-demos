"""TextToSpeechTool MCP server for converting Orik's responses to speech using Amazon Polly."""

import asyncio
import logging
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import base64

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception

try:
    import mcp
    from mcp.server import Server
    from mcp.types import Tool, TextContent
except ImportError:
    # Fallback for development/testing
    mcp = None
    Server = object
    Tool = dict
    TextContent = str

# Import our models
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.audio_models import VoiceConfig, AudioResult
from models.enums import AudioFormat


logger = logging.getLogger(__name__)


class SSMLProcessor:
    """Handles SSML (Speech Synthesis Markup Language) processing for enhanced speech delivery."""
    
    @staticmethod
    def add_sarcastic_emphasis(text: str) -> str:
        """Add SSML tags to enhance sarcastic delivery."""
        # Add emphasis to key sarcastic words
        sarcastic_words = [
            "brilliant", "amazing", "wonderful", "perfect", "excellent",
            "sure", "obviously", "clearly", "definitely", "absolutely"
        ]
        
        processed_text = text
        for word in sarcastic_words:
            # Case-insensitive replacement with emphasis
            import re
            pattern = r'\b' + re.escape(word) + r'\b'
            replacement = f'<emphasis level="strong">{word}</emphasis>'
            processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)
        
        return processed_text
    
    @staticmethod
    def add_pauses_for_effect(text: str) -> str:
        """Add strategic pauses for comedic timing."""
        # Add pauses after certain phrases for effect
        pause_patterns = [
            (r'(\.\.\.)(\s*)', r'\1<break time="1s"/>\2'),  # After ellipsis
            (r'(Oh,?)(\s+)', r'\1<break time="0.5s"/>\2'),  # After "Oh"
            (r'(Well,?)(\s+)', r'\1<break time="0.5s"/>\2'),  # After "Well"
            (r'(Sure,?)(\s+)', r'\1<break time="0.5s"/>\2'),  # After "Sure"
        ]
        
        processed_text = text
        for pattern, replacement in pause_patterns:
            import re
            processed_text = re.sub(pattern, replacement, processed_text)
        
        return processed_text
    
    @staticmethod
    def wrap_in_prosody(text: str, voice_config: VoiceConfig) -> str:
        """Wrap text in SSML prosody tags with voice configuration."""
        # First apply sarcastic emphasis and pauses
        enhanced_text = SSMLProcessor.add_sarcastic_emphasis(text)
        enhanced_text = SSMLProcessor.add_pauses_for_effect(enhanced_text)
        
        # Wrap in prosody tags
        prosody_text = voice_config.to_ssml_prosody(enhanced_text)
        
        # Wrap in speak tags for complete SSML document
        ssml_text = f'<speak>{prosody_text}</speak>'
        
        return ssml_text


class AudioCache:
    """Manages caching of TTS audio to reduce API calls and improve performance."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize audio cache."""
        if cache_dir is None:
            cache_dir = os.path.join(os.path.expanduser("~"), ".orik_cache", "audio")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache metadata file
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from file."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache metadata: {e}")
        
        return {}
    
    def _save_metadata(self):
        """Save cache metadata to file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def _get_cache_key(self, text: str, voice_config: VoiceConfig) -> str:
        """Generate cache key for text and voice configuration."""
        # Create a hash of the text and voice config
        content = f"{text}|{voice_config.voice_id}|{voice_config.speed}|{voice_config.pitch}|{voice_config.engine}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cached_audio(self, text: str, voice_config: VoiceConfig) -> Optional[AudioResult]:
        """Retrieve cached audio if available."""
        try:
            cache_key = self._get_cache_key(text, voice_config)
            
            if cache_key not in self.metadata:
                return None
            
            cache_info = self.metadata[cache_key]
            cache_file = self.cache_dir / f"{cache_key}.mp3"
            
            if not cache_file.exists():
                # Remove stale metadata entry
                del self.metadata[cache_key]
                self._save_metadata()
                return None
            
            # Read cached audio data
            with open(cache_file, 'rb') as f:
                audio_data = f.read()
            
            # Create AudioResult from cached data
            audio_result = AudioResult(
                audio_data=audio_data,
                format=AudioFormat.MP3,
                duration_ms=cache_info.get('duration_ms', 0),
                voice_config=voice_config,
                text_source=text
            )
            
            logger.info(f"Retrieved cached audio for text: {text[:50]}...")
            return audio_result
            
        except Exception as e:
            logger.error(f"Error retrieving cached audio: {e}")
            return None
    
    def cache_audio(self, text: str, voice_config: VoiceConfig, audio_result: AudioResult):
        """Cache audio result for future use."""
        try:
            cache_key = self._get_cache_key(text, voice_config)
            cache_file = self.cache_dir / f"{cache_key}.mp3"
            
            # Save audio data to file
            with open(cache_file, 'wb') as f:
                f.write(audio_result.audio_data)
            
            # Update metadata
            self.metadata[cache_key] = {
                'text': text[:100],  # Store truncated text for reference
                'voice_id': voice_config.voice_id,
                'duration_ms': audio_result.duration_ms,
                'cached_at': datetime.now().isoformat(),
                'file_size': len(audio_result.audio_data)
            }
            
            self._save_metadata()
            logger.info(f"Cached audio for text: {text[:50]}...")
            
        except Exception as e:
            logger.error(f"Error caching audio: {e}")
    
    def clear_cache(self):
        """Clear all cached audio files."""
        try:
            for cache_file in self.cache_dir.glob("*.mp3"):
                cache_file.unlink()
            
            self.metadata.clear()
            self._save_metadata()
            
            logger.info("Audio cache cleared")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            total_files = len(list(self.cache_dir.glob("*.mp3")))
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.mp3"))
            
            return {
                'total_cached_items': len(self.metadata),
                'total_files': total_files,
                'total_size_bytes': total_size,
                'cache_directory': str(self.cache_dir)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}


class PollyTTSClient:
    """Client for Amazon Polly text-to-speech service."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize Polly client."""
        self.region_name = region_name
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Polly client with proper error handling."""
        if not boto3:
            raise ImportError("boto3 is required for Amazon Polly integration")
        
        try:
            self._client = boto3.client('polly', region_name=self.region_name)
            # Test the connection
            self._client.describe_voices()
            logger.info(f"Successfully initialized Polly client in region {self.region_name}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except ClientError as e:
            logger.error(f"Failed to initialize Polly client: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing Polly client: {e}")
            raise
    
    async def synthesize_speech(self, text: str, voice_config: VoiceConfig, 
                               use_ssml: bool = True) -> AudioResult:
        """
        Synthesize speech using Amazon Polly.
        
        Args:
            text: Text to convert to speech
            voice_config: Voice configuration parameters
            use_ssml: Whether to process text as SSML
            
        Returns:
            AudioResult containing audio data and metadata
        """
        try:
            # Prepare text for synthesis
            if use_ssml:
                processed_text = SSMLProcessor.wrap_in_prosody(text, voice_config)
                text_type = 'ssml'
            else:
                processed_text = text
                text_type = 'text'
            
            # Prepare Polly parameters
            polly_params = voice_config.to_polly_params()
            polly_params.update({
                'Text': processed_text,
                'TextType': text_type
            })
            
            logger.info(f"Synthesizing speech with Polly: {text[:50]}...")
            
            # Call Polly API
            response = self._client.synthesize_speech(**polly_params)
            
            # Extract audio data
            audio_data = response['AudioStream'].read()
            
            # Estimate duration (rough calculation for MP3)
            # This is approximate - for precise duration, we'd need audio analysis
            estimated_duration_ms = len(text) * 100  # ~100ms per character (rough estimate)
            
            # Create AudioResult
            audio_result = AudioResult(
                audio_data=audio_data,
                format=AudioFormat.MP3,
                duration_ms=estimated_duration_ms,
                voice_config=voice_config,
                text_source=text
            )
            
            logger.info(f"Successfully synthesized {len(audio_data)} bytes of audio")
            return audio_result
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Polly API error ({error_code}): {error_message}")
            raise Exception(f"TTS synthesis failed: {error_message}")
            
        except Exception as e:
            logger.error(f"Unexpected error in speech synthesis: {e}")
            raise
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices from Polly."""
        try:
            response = self._client.describe_voices()
            return response.get('Voices', [])
            
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test connection to Polly service."""
        try:
            self._client.describe_voices(MaxItems=1)
            return True
        except Exception as e:
            logger.error(f"Polly connection test failed: {e}")
            return False


class TextToSpeechTool:
    """MCP tool for converting text to speech using Amazon Polly."""
    
    def __init__(self, region_name: str = 'us-east-1', cache_dir: Optional[str] = None):
        """Initialize the TTS tool."""
        self.polly_client = PollyTTSClient(region_name)
        self.audio_cache = AudioCache(cache_dir)
        
        # Default Orik voice configuration
        self.default_voice_config = VoiceConfig(
            voice_id="Matthew",
            speed=1.1,
            pitch="-10%",
            volume=1.0,
            engine="standard"
        )
    
    async def synthesize_speech(self, text: str, voice_config: Optional[Dict[str, Any]] = None,
                               use_cache: bool = True, use_ssml: bool = True) -> Dict[str, Any]:
        """
        Convert text to speech using Amazon Polly.
        
        Args:
            text: Text to convert to speech
            voice_config: Optional voice configuration override
            use_cache: Whether to use cached audio if available
            use_ssml: Whether to enhance text with SSML for sarcastic delivery
            
        Returns:
            Dictionary containing audio data and metadata
        """
        try:
            # Validate input
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            # Create voice configuration
            if voice_config:
                config = VoiceConfig(**voice_config)
            else:
                config = self.default_voice_config
            
            # Check cache first if enabled
            if use_cache:
                cached_result = self.audio_cache.get_cached_audio(text, config)
                if cached_result:
                    return {
                        "success": True,
                        "audio_data": base64.b64encode(cached_result.audio_data).decode(),
                        "audio_result": cached_result.to_dict(),
                        "cached": True,
                        "ssml_used": use_ssml
                    }
            
            # Synthesize speech
            audio_result = await self.polly_client.synthesize_speech(text, config, use_ssml)
            
            # Cache the result if caching is enabled
            if use_cache:
                self.audio_cache.cache_audio(text, config, audio_result)
            
            result = {
                "success": True,
                "audio_data": base64.b64encode(audio_result.audio_data).decode(),
                "audio_result": audio_result.to_dict(),
                "cached": False,
                "ssml_used": use_ssml
            }
            
            logger.info(f"Successfully synthesized speech for: {text[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio_data": None,
                "audio_result": None,
                "cached": False,
                "ssml_used": use_ssml
            }    

    async def get_voice_config(self) -> Dict[str, Any]:
        """
        Get the current default voice configuration.
        
        Returns:
            Dictionary containing voice configuration details
        """
        try:
            return {
                "success": True,
                "voice_config": {
                    "voice_id": self.default_voice_config.voice_id,
                    "speed": self.default_voice_config.speed,
                    "pitch": self.default_voice_config.pitch,
                    "volume": self.default_voice_config.volume,
                    "engine": self.default_voice_config.engine
                },
                "polly_params": self.default_voice_config.to_polly_params()
            }
            
        except Exception as e:
            logger.error(f"Error getting voice config: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_voice_config(self, voice_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the default voice configuration.
        
        Args:
            voice_config: New voice configuration parameters
            
        Returns:
            Dictionary confirming the update
        """
        try:
            # Validate and create new voice config
            new_config = VoiceConfig(**voice_config)
            self.default_voice_config = new_config
            
            return {
                "success": True,
                "message": "Voice configuration updated successfully",
                "new_config": {
                    "voice_id": new_config.voice_id,
                    "speed": new_config.speed,
                    "pitch": new_config.pitch,
                    "volume": new_config.volume,
                    "engine": new_config.engine
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating voice config: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """
        Get list of available voices from Amazon Polly.
        
        Returns:
            Dictionary containing available voices
        """
        try:
            voices = self.polly_client.get_available_voices()
            
            # Filter for English voices suitable for Orik
            english_voices = [
                voice for voice in voices 
                if voice.get('LanguageCode', '').startswith('en-')
            ]
            
            # Highlight recommended voices for Orik
            recommended_voices = [
                voice for voice in english_voices
                if voice.get('Id') in ['Matthew', 'Brian', 'Russell', 'Joey']
            ]
            
            return {
                "success": True,
                "total_voices": len(voices),
                "english_voices": len(english_voices),
                "recommended_voices": recommended_voices,
                "all_english_voices": english_voices
            }
            
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_tts_connection(self) -> Dict[str, Any]:
        """
        Test connection to Amazon Polly service.
        
        Returns:
            Dictionary containing connection test results
        """
        try:
            connection_ok = self.polly_client.test_connection()
            
            if connection_ok:
                # Test synthesis with a short phrase
                test_result = await self.synthesize_speech(
                    "Testing Orik's voice", 
                    use_cache=False, 
                    use_ssml=False
                )
                
                synthesis_ok = test_result.get("success", False)
                
                return {
                    "success": True,
                    "connection_status": "connected",
                    "synthesis_test": "passed" if synthesis_ok else "failed",
                    "region": self.polly_client.region_name,
                    "default_voice": self.default_voice_config.voice_id
                }
            else:
                return {
                    "success": False,
                    "connection_status": "failed",
                    "synthesis_test": "not_attempted",
                    "region": self.polly_client.region_name
                }
                
        except Exception as e:
            logger.error(f"Error testing TTS connection: {e}")
            return {
                "success": False,
                "error": str(e),
                "connection_status": "error"
            }
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get audio cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        try:
            stats = self.audio_cache.get_cache_stats()
            
            return {
                "success": True,
                "cache_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def clear_audio_cache(self) -> Dict[str, Any]:
        """
        Clear the audio cache.
        
        Returns:
            Dictionary confirming cache clearance
        """
        try:
            self.audio_cache.clear_cache()
            
            return {
                "success": True,
                "message": "Audio cache cleared successfully"
            }
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# MCP Server setup
if mcp:
    app = Server("text-to-speech-tool")
    tool_instance = TextToSpeechTool()
    
    @app.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="synthesize_speech",
                description="Convert text to speech using Amazon Polly with Orik's sarcastic voice configuration and SSML enhancement",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to convert to speech",
                            "minLength": 1
                        },
                        "voice_config": {
                            "type": "object",
                            "description": "Optional voice configuration override",
                            "properties": {
                                "voice_id": {"type": "string", "default": "Matthew"},
                                "speed": {"type": "number", "minimum": 0.5, "maximum": 2.0, "default": 1.1},
                                "pitch": {"type": "string", "default": "-10%"},
                                "volume": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 1.0},
                                "engine": {"type": "string", "enum": ["standard", "neural"], "default": "neural"}
                            }
                        },
                        "use_cache": {
                            "type": "boolean",
                            "description": "Whether to use cached audio if available",
                            "default": True
                        },
                        "use_ssml": {
                            "type": "boolean",
                            "description": "Whether to enhance text with SSML for sarcastic delivery",
                            "default": True
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="get_voice_config",
                description="Get the current default voice configuration for Orik",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="update_voice_config",
                description="Update the default voice configuration for Orik",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "voice_id": {"type": "string"},
                        "speed": {"type": "number", "minimum": 0.5, "maximum": 2.0},
                        "pitch": {"type": "string"},
                        "volume": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "engine": {"type": "string", "enum": ["standard", "neural"]}
                    },
                    "required": ["voice_id"]
                }
            ),
            Tool(
                name="get_available_voices",
                description="Get list of available voices from Amazon Polly, with recommendations for Orik",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="test_tts_connection",
                description="Test connection to Amazon Polly service and perform synthesis test",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_cache_stats",
                description="Get audio cache statistics and usage information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="clear_audio_cache",
                description="Clear the audio cache to free up disk space",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    @app.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        try:
            if name == "synthesize_speech":
                text = arguments.get("text")
                voice_config = arguments.get("voice_config")
                use_cache = arguments.get("use_cache", True)
                use_ssml = arguments.get("use_ssml", True)
                result = await tool_instance.synthesize_speech(text, voice_config, use_cache, use_ssml)
                
            elif name == "get_voice_config":
                result = await tool_instance.get_voice_config()
                
            elif name == "update_voice_config":
                voice_config = arguments
                result = await tool_instance.update_voice_config(voice_config)
                
            elif name == "get_available_voices":
                result = await tool_instance.get_available_voices()
                
            elif name == "test_tts_connection":
                result = await tool_instance.test_tts_connection()
                
            elif name == "get_cache_stats":
                result = await tool_instance.get_cache_stats()
                
            elif name == "clear_audio_cache":
                result = await tool_instance.clear_audio_cache()
                
            else:
                result = {"success": False, "error": f"Unknown tool: {name}"}
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            error_result = {"success": False, "error": str(e)}
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


# For standalone testing
async def main():
    """Main function for testing the tool."""
    logging.basicConfig(level=logging.INFO)
    
    tool = TextToSpeechTool()
    
    # Test connection
    print("Testing TTS connection...")
    result = await tool.test_tts_connection()
    print(json.dumps(result, indent=2))
    
    if result.get("success"):
        # Test speech synthesis
        print("\nTesting speech synthesis...")
        test_text = "Oh brilliant, Aaron. Just brilliant. I'm sure this demo will work perfectly."
        result = await tool.synthesize_speech(test_text)
        
        if result.get("success"):
            print(f"Successfully synthesized {len(result['audio_data'])} characters of base64 audio data")
            print(f"Audio metadata: {json.dumps(result['audio_result'], indent=2)}")
        else:
            print(f"Synthesis failed: {result.get('error')}")
    
    # Test voice configuration
    print("\nTesting voice configuration...")
    result = await tool.get_voice_config()
    print(json.dumps(result, indent=2))
    
    # Test available voices
    print("\nTesting available voices...")
    result = await tool.get_available_voices()
    if result.get("success"):
        print(f"Found {result['total_voices']} total voices, {result['english_voices']} English voices")
        print(f"Recommended voices for Orik: {len(result['recommended_voices'])}")
    
    # Test cache stats
    print("\nTesting cache statistics...")
    result = await tool.get_cache_stats()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())