"""Tests for the Orik Agent Controller."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Import the classes we're testing
from src.agent.orik_agent_controller import (
    OrikAgentController, 
    ResponseGenerator, 
    MCPClient, 
    MCPClientConfig
)
from src.models.slide_data import SlideData, SlideEvent
from src.models.orik_content import OrikContent
from src.models.orik_response import OrikResponse
from src.models.personality import OrikPersonality
from src.models.system_status import SystemStatus
from src.models.audio_models import AudioResult, VoiceConfig
from src.models.enums import ResponseType, PresentationSoftware, AudioFormat


class TestMCPClient:
    """Test cases for MCPClient."""
    
    def test_mcp_client_initialization(self):
        """Test MCPClient initialization."""
        config = MCPClientConfig(
            name="test-client",
            command="python",
            args=["-m", "test_module"]
        )
        
        client = MCPClient(config)
        
        assert client.config == config
        assert not client.is_connected
        assert client._process is None
    
    @pytest.mark.asyncio
    async def test_mcp_client_connect_success(self):
        """Test successful MCP client connection."""
        config = MCPClientConfig("test-client", "python", ["-m", "test"])
        client = MCPClient(config)
        
        # Test connection
        result = await client.connect()
        
        assert result is True
        assert client.is_connected
    
    @pytest.mark.asyncio
    async def test_mcp_client_disconnect(self):
        """Test MCP client disconnection."""
        config = MCPClientConfig("test-client", "python", ["-m", "test"])
        client = MCPClient(config)
        
        # Connect first
        await client.connect()
        assert client.is_connected
        
        # Disconnect
        await client.disconnect()
        assert not client.is_connected
    
    @pytest.mark.asyncio
    async def test_mcp_client_call_tool_success(self):
        """Test successful tool call."""
        config = MCPClientConfig("test-client", "python", ["-m", "test"])
        client = MCPClient(config)
        await client.connect()
        
        result = await client.call_tool("test_tool", {"param": "value"})
        
        assert result["success"] is True
        assert result["tool_name"] == "test_tool"
        assert result["arguments"] == {"param": "value"}
    
    @pytest.mark.asyncio
    async def test_mcp_client_call_tool_not_connected(self):
        """Test tool call when not connected."""
        config = MCPClientConfig("test-client", "python", ["-m", "test"])
        client = MCPClient(config)
        
        with pytest.raises(RuntimeError, match="is not connected"):
            await client.call_tool("test_tool", {})


class TestResponseGenerator:
    """Test cases for ResponseGenerator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.personality = OrikPersonality.create_default()
        self.generator = ResponseGenerator(self.personality)
    
    @pytest.mark.asyncio
    async def test_generate_tagged_response(self):
        """Test response generation for tagged content."""
        # Create slide data with Orik tags
        slide_data = SlideData(
            slide_index=0,
            slide_title="Test Slide",
            speaker_notes="[Orik] Aaron is about to explain something complex",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        orik_content = OrikContent.extract_from_notes(slide_data)
        
        response = await self.generator.generate_response(orik_content)
        
        assert isinstance(response, OrikResponse)
        assert response.response_type == ResponseType.TAGGED
        assert response.confidence > 0.5
        assert len(response.response_text) > 0
        assert "Aaron is about to explain something complex" in response.source_content
    
    @pytest.mark.asyncio
    async def test_generate_response_no_tags(self):
        """Test response generation when no Orik tags present."""
        # Create slide data without Orik tags
        slide_data = SlideData(
            slide_index=0,
            slide_title="Test Slide",
            speaker_notes="Regular speaker notes without tags",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        orik_content = OrikContent.extract_from_notes(slide_data)
        
        # Mock personality to always interrupt for testing
        with patch.object(self.personality, 'should_interrupt', return_value=True):
            response = await self.generator.generate_response(orik_content)
        
        assert isinstance(response, OrikResponse)
        assert response.response_type in [ResponseType.CONTEXTUAL, ResponseType.RANDOM_DIG]
    
    @pytest.mark.asyncio
    async def test_generate_response_silent(self):
        """Test response generation when Orik should stay silent."""
        slide_data = SlideData(
            slide_index=0,
            slide_title="Test Slide", 
            speaker_notes="Regular notes",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        orik_content = OrikContent.extract_from_notes(slide_data)
        
        # Mock personality to never interrupt
        with patch.object(self.personality, 'should_interrupt', return_value=False):
            response = await self.generator.generate_response(orik_content)
        
        # When Orik doesn't interrupt, he should return a silent response
        assert response.response_text == "[SILENT]"
        assert response.confidence == 0.0
    
    def test_add_to_history(self):
        """Test adding responses to conversation history."""
        response1 = OrikResponse(
            response_text="First response",
            confidence=0.8,
            response_type=ResponseType.TAGGED,
            generation_time=datetime.now()
        )
        
        response2 = OrikResponse(
            response_text="Second response",
            confidence=0.7,
            response_type=ResponseType.RANDOM_DIG,
            generation_time=datetime.now()
        )
        
        self.generator.add_to_history(response1)
        self.generator.add_to_history(response2)
        
        assert len(self.generator.conversation_history) == 2
        assert self.generator.conversation_history[0] == response1
        assert self.generator.conversation_history[1] == response2
    
    def test_get_recent_responses(self):
        """Test getting recent responses from history."""
        # Add multiple responses
        for i in range(7):
            response = OrikResponse(
                response_text=f"Response {i}",
                confidence=0.8,
                response_type=ResponseType.TAGGED,
                generation_time=datetime.now()
            )
            self.generator.add_to_history(response)
        
        # Get recent responses
        recent = self.generator.get_recent_responses(3)
        
        assert len(recent) == 3
        assert recent[0].response_text == "Response 4"
        assert recent[1].response_text == "Response 5"
        assert recent[2].response_text == "Response 6"


class TestOrikAgentController:
    """Test cases for OrikAgentController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the PresentationMonitor to avoid AppleScript dependency
        with patch('src.agent.orik_agent_controller.PresentationMonitor') as mock_monitor, \
             patch('src.agent.orik_agent_controller.AudioPlaybackService') as mock_audio:
            self.controller = OrikAgentController()
    
    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self, 'controller'):
            self.controller.shutdown()
    
    def test_initialization(self):
        """Test OrikAgentController initialization."""
        assert isinstance(self.controller.personality, OrikPersonality)
        assert isinstance(self.controller.response_generator, ResponseGenerator)
        assert not self.controller.is_monitoring
        assert self.controller.current_slide_data is None
        assert len(self.controller.mcp_clients) == 3  # speaker_notes, dig_at_aaron, text_to_speech
    
    def test_mcp_client_initialization(self):
        """Test MCP client initialization."""
        clients = self.controller.mcp_clients
        
        assert "speaker_notes" in clients
        assert "dig_at_aaron" in clients
        assert "text_to_speech" in clients
        
        # Check client configurations
        speaker_notes_client = clients["speaker_notes"]
        assert speaker_notes_client.config.name == "speaker-notes-tool"
        assert "speaker_notes_server" in " ".join(speaker_notes_client.config.args)
    
    @pytest.mark.asyncio
    async def test_start_monitoring_success(self):
        """Test successful monitoring startup."""
        # Mock the dependencies
        with patch.object(self.controller, '_connect_mcp_clients', new_callable=AsyncMock) as mock_connect, \
             patch.object(self.controller, '_initialize_audio_service') as mock_audio, \
             patch.object(self.controller.presentation_monitor, 'start_monitoring', new_callable=AsyncMock) as mock_monitor:
            
            await self.controller.start_monitoring()
            
            assert self.controller.is_monitoring
            mock_connect.assert_called_once()
            mock_audio.assert_called_once()
            mock_monitor.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_monitoring_already_started(self):
        """Test starting monitoring when already started."""
        self.controller.is_monitoring = True
        
        with patch.object(self.controller, '_connect_mcp_clients', new_callable=AsyncMock) as mock_connect:
            await self.controller.start_monitoring()
            
            # Should not call connect again
            mock_connect.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_stop_monitoring(self):
        """Test stopping monitoring."""
        # Set up as if monitoring is active
        self.controller.is_monitoring = True
        
        with patch.object(self.controller.presentation_monitor, 'stop_monitoring', new_callable=AsyncMock) as mock_stop, \
             patch.object(self.controller, '_disconnect_mcp_clients', new_callable=AsyncMock) as mock_disconnect, \
             patch.object(self.controller.audio_service, 'shutdown') as mock_shutdown:
            
            await self.controller.stop_monitoring()
            
            assert not self.controller.is_monitoring
            mock_stop.assert_called_once()
            mock_disconnect.assert_called_once()
            mock_shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_slide_change(self):
        """Test processing slide change events."""
        slide_data = SlideData(
            slide_index=1,
            slide_title="Test Slide",
            speaker_notes="[Orik] This is a test slide for Aaron",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        # Mock the response processing
        with patch.object(self.controller, '_process_response', new_callable=AsyncMock) as mock_process:
            await self.controller.process_slide_change(slide_data)
            
            # Check that slide data was stored
            assert self.controller.current_slide_data == slide_data
            
            # Check that response was generated and processed
            mock_process.assert_called_once()
            
            # Check that response was added to history
            recent_responses = self.controller.get_recent_responses(1)
            assert len(recent_responses) == 1
            assert recent_responses[0].response_type == ResponseType.TAGGED
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_success(self):
        """Test successful speech synthesis."""
        # Mock TTS client
        mock_client = Mock()
        mock_client.is_connected = True
        mock_client.call_tool = AsyncMock(return_value={
            "success": True,
            "audio_data": "base64_encoded_audio_data"
        })
        
        self.controller.mcp_clients["text_to_speech"] = mock_client
        
        result = await self.controller._synthesize_speech("Test text")
        
        assert isinstance(result, AudioResult)
        assert result.text_source == "Test text"
        mock_client.call_tool.assert_called_once_with("synthesize_speech", {
            "text": "Test text",
            "use_ssml": True,
            "use_cache": True
        })
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_client_not_available(self):
        """Test speech synthesis when TTS client not available."""
        # Remove TTS client
        self.controller.mcp_clients["text_to_speech"].is_connected = False
        
        result = await self.controller._synthesize_speech("Test text")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_force_response(self):
        """Test forcing a response from Orik."""
        prompt = "What do you think about this slide?"
        
        with patch.object(self.controller, '_process_response', new_callable=AsyncMock) as mock_process:
            response = await self.controller.force_response(prompt)
            
            assert isinstance(response, OrikResponse)
            assert response.source_content == prompt
            mock_process.assert_called_once_with(response)
    
    def test_get_system_status(self):
        """Test getting system status."""
        status = self.controller.get_system_status()
        
        assert isinstance(status, SystemStatus)
        assert status.is_monitoring == self.controller.is_monitoring
    
    def test_update_personality(self):
        """Test updating Orik's personality."""
        new_personality = OrikPersonality(
            base_prompt="New personality",
            sarcasm_level=0.9,
            interruption_frequency=0.5
        )
        
        self.controller.update_personality(new_personality)
        
        assert self.controller.personality == new_personality
        assert self.controller.response_generator.personality == new_personality
    
    @pytest.mark.asyncio
    async def test_handle_slide_event_slide_changed(self):
        """Test handling slide changed events."""
        slide_data = SlideData(
            slide_index=0,
            slide_title="Test",
            speaker_notes="Test notes",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        event = SlideEvent(
            event_type="slide_changed",
            slide_data=slide_data
        )
        
        with patch.object(self.controller, 'process_slide_change', new_callable=AsyncMock) as mock_process:
            await self.controller._handle_slide_event(event)
            
            mock_process.assert_called_once_with(slide_data)
    
    @pytest.mark.asyncio
    async def test_handle_presentation_started(self):
        """Test handling presentation started events."""
        # Add some history first
        response = OrikResponse(
            response_text="Old response",
            confidence=0.8,
            response_type=ResponseType.TAGGED,
            generation_time=datetime.now()
        )
        self.controller.response_generator.add_to_history(response)
        
        # Mock dig client
        mock_dig_client = Mock()
        mock_dig_client.is_connected = True
        mock_dig_client.call_tool = AsyncMock(return_value={"success": True})
        self.controller.mcp_clients["dig_at_aaron"] = mock_dig_client
        
        await self.controller._handle_presentation_started()
        
        # Check that history was cleared
        assert len(self.controller.response_generator.conversation_history) == 0
        
        # Check that dig history was reset
        mock_dig_client.call_tool.assert_called_once_with("reset_dig_history", {})
    
    @pytest.mark.asyncio
    async def test_handle_presentation_ended(self):
        """Test handling presentation ended events."""
        # Set up some state
        self.controller.current_slide_data = SlideData(
            slide_index=0,
            slide_title="Test",
            speaker_notes="Test",
            presentation_path="test.pptx",
            timestamp=datetime.now()
        )
        
        with patch.object(self.controller.audio_service, 'stop_playback') as mock_stop:
            await self.controller._handle_presentation_ended()
            
            # Check that state was cleared
            assert self.controller.current_slide_data is None
            mock_stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_mcp_clients(self):
        """Test connecting MCP clients."""
        # Mock all clients
        for client in self.controller.mcp_clients.values():
            client.connect = AsyncMock(return_value=True)
        
        await self.controller._connect_mcp_clients()
        
        # Check that all clients were connected
        for client in self.controller.mcp_clients.values():
            client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_mcp_clients_failure(self):
        """Test MCP client connection failure."""
        # Mock all clients to fail
        for client in self.controller.mcp_clients.values():
            client.connect = AsyncMock(return_value=False)
        
        with pytest.raises(RuntimeError, match="Failed to connect any MCP clients"):
            await self.controller._connect_mcp_clients()
    
    @pytest.mark.asyncio
    async def test_test_mcp_connections(self):
        """Test testing MCP connections."""
        # Mock clients
        for name, client in self.controller.mcp_clients.items():
            client.is_connected = True
            client.call_tool = AsyncMock(return_value={"success": True})
        
        results = await self.controller.test_mcp_connections()
        
        assert len(results) == 3
        assert all(results.values())  # All should be True
    
    def test_audio_callbacks(self):
        """Test audio playback callbacks."""
        # Test audio started callback
        audio_result = AudioResult(
            audio_data=b"test",
            format=AudioFormat.MP3,
            duration_ms=1000,
            voice_config=VoiceConfig(),
            text_source="Test"
        )
        
        # Should not raise any exceptions
        self.controller._on_audio_playback_started(audio_result)
        self.controller._on_audio_playback_finished(audio_result)
        
        # Test error callback
        error = Exception("Test error")
        self.controller._on_audio_playback_error(error)
        
        # Check that error was recorded in system status
        assert self.controller.system_status.has_errors
        assert "Test error" in self.controller.system_status.error_state
    
    def test_context_manager(self):
        """Test using OrikAgentController as context manager."""
        with patch.object(OrikAgentController, 'shutdown') as mock_shutdown:
            with OrikAgentController() as controller:
                assert isinstance(controller, OrikAgentController)
            
            mock_shutdown.assert_called_once()


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Integration test
class TestOrikAgentControllerIntegration:
    """Integration tests for OrikAgentController."""
    
    @pytest.mark.asyncio
    async def test_full_slide_processing_workflow(self):
        """Test the complete slide processing workflow."""
        # Mock dependencies to avoid AppleScript requirement
        with patch('src.agent.orik_agent_controller.PresentationMonitor') as mock_monitor, \
             patch('src.agent.orik_agent_controller.AudioPlaybackService') as mock_audio:
            controller = OrikAgentController()
        
        try:
            # Mock all external dependencies
            with patch.object(controller, '_connect_mcp_clients', new_callable=AsyncMock), \
                 patch.object(controller, '_initialize_audio_service'), \
                 patch.object(controller.presentation_monitor, 'start_monitoring', new_callable=AsyncMock), \
                 patch.object(controller, '_synthesize_speech', new_callable=AsyncMock) as mock_tts, \
                 patch.object(controller.audio_service, 'play_audio', new_callable=AsyncMock) as mock_audio:
                
                # Set up TTS mock to return audio result
                mock_audio_result = AudioResult(
                    audio_data=b"mock_audio",
                    format=AudioFormat.MP3,
                    duration_ms=2000,
                    voice_config=VoiceConfig(),
                    text_source="Mock response"
                )
                mock_tts.return_value = mock_audio_result
                
                # Start monitoring
                await controller.start_monitoring()
                assert controller.is_monitoring
                
                # Create slide with Orik content
                slide_data = SlideData(
                    slide_index=0,
                    slide_title="Integration Test Slide",
                    speaker_notes="[Orik] Aaron is about to demonstrate something amazing",
                    presentation_path="test.pptx",
                    timestamp=datetime.now()
                )
                
                # Process slide change
                await controller.process_slide_change(slide_data)
                
                # Verify the workflow
                assert controller.current_slide_data == slide_data
                
                # Check that response was generated
                recent_responses = controller.get_recent_responses(1)
                assert len(recent_responses) == 1
                assert recent_responses[0].response_type == ResponseType.TAGGED
                
                # Check that TTS was called
                mock_tts.assert_called_once()
                
                # Check that audio was played
                mock_audio.assert_called_once_with(mock_audio_result)
                
                # Stop monitoring
                await controller.stop_monitoring()
                assert not controller.is_monitoring
                
        finally:
            controller.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])