"""Orik Agent Controller - Central orchestrator for the Orik presentation co-host system."""

import asyncio
import logging
import json
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

# Import our models
from ..models.slide_data import SlideData, SlideEvent
from ..models.orik_content import OrikContent
from ..models.orik_response import OrikResponse
from ..models.personality import OrikPersonality
from ..models.system_status import SystemStatus
from ..models.audio_models import AudioResult, VoiceConfig
from ..models.enums import ResponseType, PresentationSoftware
from ..services.presentation_monitor import PresentationMonitor
from ..services.audio_playback_service import AudioPlaybackService


logger = logging.getLogger(__name__)


@dataclass
class MCPClientConfig:
    """Configuration for MCP client connections."""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    timeout: float = 30.0


class MCPClient:
    """Simple MCP client for tool communication."""
    
    def __init__(self, config: MCPClientConfig):
        self.config = config
        self.is_connected = False
        self._process = None
        
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        try:
            # In a real implementation, this would establish connection to MCP server
            # For now, we'll simulate the connection
            logger.info(f"Connecting to MCP server: {self.config.name}")
            
            # Simulate connection delay
            await asyncio.sleep(0.1)
            
            self.is_connected = True
            logger.info(f"Successfully connected to {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.config.name}: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self._process:
            try:
                self._process.terminate()
                await self._process.wait()
            except Exception as e:
                logger.error(f"Error terminating MCP process: {e}")
        
        self.is_connected = False
        logger.info(f"Disconnected from {self.config.name}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if not self.is_connected:
            raise RuntimeError(f"MCP client {self.config.name} is not connected")
        
        try:
            # In a real implementation, this would make actual MCP calls
            # For now, we'll simulate tool responses based on the tool implementations
            logger.debug(f"Calling tool {tool_name} on {self.config.name} with args: {arguments}")
            
            # Simulate tool call delay
            await asyncio.sleep(0.1)
            
            # Return simulated success response
            return {
                "success": True,
                "tool_name": tool_name,
                "arguments": arguments,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }


class ResponseGenerator:
    """Handles generation of Orik's responses based on personality and context."""
    
    def __init__(self, personality: OrikPersonality):
        self.personality = personality
        self.conversation_history: List[OrikResponse] = []
        
    async def generate_response(self, orik_content: OrikContent, 
                              context: Optional[Dict[str, Any]] = None) -> OrikResponse:
        """
        Generate an Orik response based on content and context.
        
        Args:
            orik_content: Extracted Orik content from slide
            context: Additional context for response generation
            
        Returns:
            Generated OrikResponse
        """
        try:
            if orik_content.has_orik_tags:
                return await self._generate_tagged_response(orik_content, context)
            else:
                return await self._generate_contextual_or_dig_response(orik_content, context)
                
        except ValueError as e:
            # Handle validation errors (like empty response text) by returning silent response
            if "response_text cannot be empty" in str(e):
                logger.debug("Generated silent response due to validation error")
                return self._create_silent_response()
            else:
                raise
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Return fallback response
            return OrikResponse(
                response_text="Well, this is awkward. Even I'm speechless.",
                confidence=0.5,
                response_type=ResponseType.CONTEXTUAL,
                generation_time=datetime.now(),
                source_content=orik_content.get_combined_content()
            )
    
    def _create_silent_response(self) -> OrikResponse:
        """Create a silent response for when Orik should stay quiet."""
        return OrikResponse(
            response_text="[SILENT]",  # Special marker for silent responses
            confidence=0.0,
            response_type=ResponseType.CONTEXTUAL,
            generation_time=datetime.now(),
            source_content=""
        )
    
    async def _generate_tagged_response(self, orik_content: OrikContent, 
                                       context: Optional[Dict[str, Any]]) -> OrikResponse:
        """Generate response for tagged Orik content."""
        combined_content = orik_content.get_combined_content()
        
        # Use personality templates to generate response
        if self.personality.response_templates:
            template = self.personality.response_templates[0]  # Use first template for now
            response_text = template.format(content=combined_content)
        else:
            response_text = f"Oh, {combined_content}? How... enlightening, Aaron."
        
        return OrikResponse(
            response_text=response_text,
            confidence=0.8,
            response_type=ResponseType.TAGGED,
            generation_time=datetime.now(),
            source_content=combined_content
        )
    
    async def _generate_contextual_or_dig_response(self, orik_content: OrikContent,
                                                  context: Optional[Dict[str, Any]]) -> OrikResponse:
        """Generate contextual response or random dig when no tags present."""
        
        # Decide whether to generate a response based on personality settings
        if not self.personality.should_interrupt():
            # Return silent response (Orik stays silent)
            return self._create_silent_response()
        
        # Generate a contextual response or dig
        if self.personality.should_dig_at_aaron():
            response_text = "I'm sure Aaron knows exactly what he's talking about... right?"
            response_type = ResponseType.RANDOM_DIG
        else:
            response_text = "Hmm, interesting approach, Aaron."
            response_type = ResponseType.CONTEXTUAL
        
        return OrikResponse(
            response_text=response_text,
            confidence=0.6,
            response_type=response_type,
            generation_time=datetime.now(),
            source_content=orik_content.context or ""
        )
    
    def add_to_history(self, response: OrikResponse):
        """Add response to conversation history."""
        self.conversation_history.append(response)
        
        # Keep only recent history (last 10 responses)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def get_recent_responses(self, count: int = 5) -> List[OrikResponse]:
        """Get recent responses from history."""
        return self.conversation_history[-count:] if self.conversation_history else []


class OrikAgentController:
    """Central orchestrator for the Orik presentation co-host system."""
    
    def __init__(self, 
                 presentation_software: PresentationSoftware = PresentationSoftware.POWERPOINT,
                 personality: Optional[OrikPersonality] = None):
        """
        Initialize the Orik Agent Controller.
        
        Args:
            presentation_software: Type of presentation software to monitor
            personality: Orik's personality configuration
        """
        # Core components
        self.personality = personality or OrikPersonality.create_default()
        self.response_generator = ResponseGenerator(self.personality)
        
        # Services
        self.presentation_monitor = PresentationMonitor(presentation_software)
        self.audio_service = AudioPlaybackService()
        
        # MCP clients
        self.mcp_clients: Dict[str, MCPClient] = {}
        self._initialize_mcp_clients()
        
        # State management
        self.is_monitoring = False
        self.current_slide_data: Optional[SlideData] = None
        self.system_status = SystemStatus(
            is_monitoring=False,
            presentation_connected=False,
            tts_available=False,
            audio_ready=False,
            last_activity=datetime.now()
        )
        
        # Callbacks
        self.on_response_generated: Optional[Callable[[OrikResponse], None]] = None
        self.on_audio_played: Optional[Callable[[AudioResult], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        
        logger.info("OrikAgentController initialized")
    
    def _initialize_mcp_clients(self):
        """Initialize MCP client configurations."""
        # Speaker Notes Tool
        self.mcp_clients["speaker_notes"] = MCPClient(MCPClientConfig(
            name="speaker-notes-tool",
            command="python",
            args=["-m", "src.mcp_tools.run_speaker_notes_server"]
        ))
        
        # Dig At Aaron Tool
        self.mcp_clients["dig_at_aaron"] = MCPClient(MCPClientConfig(
            name="dig-at-aaron-tool", 
            command="python",
            args=["-m", "src.mcp_tools.run_dig_at_aaron_server"]
        ))
        
        # Text To Speech Tool
        self.mcp_clients["text_to_speech"] = MCPClient(MCPClientConfig(
            name="text-to-speech-tool",
            command="python", 
            args=["-m", "src.mcp_tools.run_text_to_speech_server"]
        ))
    
    async def start_monitoring(self) -> None:
        """Start the Orik agent monitoring system."""
        if self.is_monitoring:
            logger.warning("Monitoring already started")
            return
        
        try:
            logger.info("Starting Orik agent monitoring...")
            
            # Connect MCP clients
            await self._connect_mcp_clients()
            
            # Initialize audio service
            self._initialize_audio_service()
            
            # Start presentation monitoring
            await self.presentation_monitor.start_monitoring(self._handle_slide_event)
            
            # Update system status
            self.is_monitoring = True
            self._update_system_status()
            
            logger.info("Orik agent monitoring started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            await self.stop_monitoring()
            if self.on_error:
                self.on_error(e)
            raise
    
    async def stop_monitoring(self) -> None:
        """Stop the Orik agent monitoring system."""
        if not self.is_monitoring:
            return
        
        logger.info("Stopping Orik agent monitoring...")
        
        try:
            # Stop presentation monitoring
            await self.presentation_monitor.stop_monitoring()
            
            # Disconnect MCP clients
            await self._disconnect_mcp_clients()
            
            # Shutdown audio service
            self.audio_service.shutdown()
            
            # Update state
            self.is_monitoring = False
            self._update_system_status()
            
            logger.info("Orik agent monitoring stopped")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            if self.on_error:
                self.on_error(e)
    
    async def _connect_mcp_clients(self):
        """Connect all MCP clients."""
        logger.info("Connecting MCP clients...")
        
        connection_tasks = []
        for name, client in self.mcp_clients.items():
            connection_tasks.append(self._connect_single_client(name, client))
        
        # Connect all clients concurrently
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        # Check results
        connected_count = 0
        for i, result in enumerate(results):
            client_name = list(self.mcp_clients.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to connect {client_name}: {result}")
            elif result:
                connected_count += 1
                logger.info(f"Connected {client_name}")
            else:
                logger.warning(f"Failed to connect {client_name}")
        
        logger.info(f"Connected {connected_count}/{len(self.mcp_clients)} MCP clients")
        
        if connected_count == 0:
            raise RuntimeError("Failed to connect any MCP clients")
    
    async def _connect_single_client(self, name: str, client: MCPClient) -> bool:
        """Connect a single MCP client with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if await client.connect():
                    return True
                else:
                    logger.warning(f"Connection attempt {attempt + 1} failed for {name}")
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} error for {name}: {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff
        
        return False
    
    async def _disconnect_mcp_clients(self):
        """Disconnect all MCP clients."""
        logger.info("Disconnecting MCP clients...")
        
        disconnect_tasks = []
        for client in self.mcp_clients.values():
            disconnect_tasks.append(client.disconnect())
        
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        logger.info("MCP clients disconnected")
    
    def _initialize_audio_service(self):
        """Initialize the audio playback service."""
        try:
            # Set up audio callbacks
            self.audio_service.on_playback_started = self._on_audio_playback_started
            self.audio_service.on_playback_finished = self._on_audio_playback_finished
            self.audio_service.on_playback_error = self._on_audio_playback_error
            
            logger.info("Audio service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize audio service: {e}")
            raise
    
    async def _handle_slide_event(self, event: SlideEvent):
        """Handle slide change events from the presentation monitor."""
        try:
            logger.info(f"Handling slide event: {event.event_type}")
            
            if event.event_type == "slide_changed" and event.slide_data:
                await self.process_slide_change(event.slide_data)
            elif event.event_type == "presentation_started":
                await self._handle_presentation_started()
            elif event.event_type == "presentation_ended":
                await self._handle_presentation_ended()
            
            self._update_system_status()
            
        except Exception as e:
            logger.error(f"Error handling slide event: {e}")
            if self.on_error:
                self.on_error(e)
    
    async def process_slide_change(self, slide_data: SlideData) -> None:
        """
        Process a slide change event and generate Orik's response.
        
        Args:
            slide_data: Data from the new slide
        """
        try:
            logger.info(f"Processing slide change: {slide_data.slide_index + 1} - {slide_data.slide_title}")
            
            # Update current slide
            self.current_slide_data = slide_data
            
            # Extract Orik content from speaker notes
            orik_content = OrikContent.extract_from_notes(slide_data)
            
            logger.debug(f"Extracted {orik_content.tag_count} Orik tags from slide notes")
            
            # Generate response
            response = await self.response_generator.generate_response(orik_content)
            
            # Add to history
            self.response_generator.add_to_history(response)
            
            # Process response if not silent
            if response.response_text != "[SILENT]" and response.confidence > 0.0:
                await self._process_response(response)
            else:
                logger.debug("Generated silent response - Orik stays quiet")
            
            # Trigger callback
            if self.on_response_generated:
                self.on_response_generated(response)
            
        except Exception as e:
            logger.error(f"Error processing slide change: {e}")
            if self.on_error:
                self.on_error(e)
    
    async def _process_response(self, response: OrikResponse):
        """Process an Orik response through TTS and audio playback."""
        try:
            logger.info(f"Processing response: {response.response_text[:50]}...")
            
            # Convert to speech using TTS tool
            audio_result = await self._synthesize_speech(response.response_text)
            
            if audio_result:
                # Play audio
                await self.audio_service.play_audio(audio_result)
                logger.info("Response queued for audio playback")
            else:
                logger.warning("Failed to synthesize speech for response")
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            if self.on_error:
                self.on_error(e)
    
    async def _synthesize_speech(self, text: str) -> Optional[AudioResult]:
        """Synthesize speech using the TTS MCP tool."""
        try:
            tts_client = self.mcp_clients.get("text_to_speech")
            if not tts_client or not tts_client.is_connected:
                logger.error("TTS client not available")
                return None
            
            # Call TTS tool
            result = await tts_client.call_tool("synthesize_speech", {
                "text": text,
                "use_ssml": True,
                "use_cache": True
            })
            
            if result.get("success"):
                # In a real implementation, we would parse the actual audio data
                # For now, create a mock AudioResult
                voice_config = VoiceConfig()  # Use default Orik voice
                
                return AudioResult(
                    audio_data=b"mock_audio_data",  # Would be actual audio from TTS
                    format=AudioFormat.MP3,
                    duration_ms=len(text) * 100,  # Rough estimate
                    voice_config=voice_config,
                    text_source=text
                )
            else:
                logger.error(f"TTS synthesis failed: {result.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return None
    
    async def _handle_presentation_started(self):
        """Handle presentation started event."""
        logger.info("Presentation started - Orik is ready to co-host")
        
        # Reset conversation history for new presentation
        self.response_generator.conversation_history.clear()
        
        # Reset dig history if using dig tool
        try:
            dig_client = self.mcp_clients.get("dig_at_aaron")
            if dig_client and dig_client.is_connected:
                await dig_client.call_tool("reset_dig_history", {})
        except Exception as e:
            logger.warning(f"Failed to reset dig history: {e}")
    
    async def _handle_presentation_ended(self):
        """Handle presentation ended event."""
        logger.info("Presentation ended - Orik signing off")
        
        # Stop any current audio playback
        self.audio_service.stop_playback()
        
        # Clear current slide data
        self.current_slide_data = None
    
    def _update_system_status(self):
        """Update the system status based on current state."""
        self.system_status.is_monitoring = self.is_monitoring
        self.system_status.presentation_connected = self.presentation_monitor.is_presentation_active()
        self.system_status.tts_available = (
            self.mcp_clients.get("text_to_speech", MCPClient(MCPClientConfig("", "", []))).is_connected
        )
        self.system_status.audio_ready = not self.audio_service.get_playback_status().value == "error"
        self.system_status.update_activity()
        
        # Clear any previous errors if all systems are operational
        if self.system_status.is_fully_operational:
            self.system_status.clear_error()
    
    def _on_audio_playback_started(self, audio_result: AudioResult):
        """Callback for when audio playback starts."""
        logger.debug(f"Audio playback started: {audio_result.text_source[:30]}...")
    
    def _on_audio_playback_finished(self, audio_result: AudioResult):
        """Callback for when audio playback finishes."""
        logger.debug(f"Audio playback finished: {audio_result.text_source[:30]}...")
        
        if self.on_audio_played:
            self.on_audio_played(audio_result)
    
    def _on_audio_playback_error(self, error: Exception):
        """Callback for audio playback errors."""
        logger.error(f"Audio playback error: {error}")
        self.system_status.set_error(f"Audio playback error: {error}")
        
        if self.on_error:
            self.on_error(error)
    
    # Public API methods
    
    def get_system_status(self) -> SystemStatus:
        """Get current system status."""
        self._update_system_status()
        return self.system_status
    
    def get_current_slide(self) -> Optional[SlideData]:
        """Get current slide data."""
        return self.current_slide_data
    
    def get_recent_responses(self, count: int = 5) -> List[OrikResponse]:
        """Get recent Orik responses."""
        return self.response_generator.get_recent_responses(count)
    
    def update_personality(self, personality: OrikPersonality):
        """Update Orik's personality configuration."""
        self.personality = personality
        self.response_generator.personality = personality
        logger.info("Orik personality updated")
    
    async def force_response(self, prompt: str) -> OrikResponse:
        """Force Orik to generate a response to a specific prompt."""
        try:
            # Create mock slide data for the prompt
            mock_slide = SlideData(
                slide_index=0,  # Use 0 instead of -1 to avoid validation error
                slide_title="Manual Prompt",
                speaker_notes=f"[Orik] {prompt}",
                presentation_path="manual",
                timestamp=datetime.now()
            )
            
            # Extract content and generate response
            orik_content = OrikContent.extract_from_notes(mock_slide)
            response = await self.response_generator.generate_response(orik_content)
            
            # Process the response
            if response.response_text.strip():
                await self._process_response(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error forcing response: {e}")
            return OrikResponse(
                response_text="I'm having technical difficulties. How embarrassing.",
                confidence=0.3,
                response_type=ResponseType.CONTEXTUAL,
                generation_time=datetime.now(),
                source_content=prompt
            )
    
    async def test_mcp_connections(self) -> Dict[str, bool]:
        """Test all MCP client connections."""
        results = {}
        
        for name, client in self.mcp_clients.items():
            try:
                if client.is_connected:
                    # Test with a simple call
                    result = await client.call_tool("test", {})
                    results[name] = result.get("success", False)
                else:
                    results[name] = False
            except Exception as e:
                logger.error(f"Error testing {name}: {e}")
                results[name] = False
        
        return results
    
    def shutdown(self):
        """Shutdown the Orik agent controller."""
        logger.info("Shutting down OrikAgentController")
        
        # Stop monitoring if active
        if self.is_monitoring:
            asyncio.create_task(self.stop_monitoring())
        
        # Shutdown services
        self.presentation_monitor.shutdown()
        self.audio_service.shutdown()
        
        logger.info("OrikAgentController shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()