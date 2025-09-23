"""Presentation monitoring service for detecting slide changes and events."""

import asyncio
import logging
import threading
import time
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass

try:
    import applescript
    APPLESCRIPT_AVAILABLE = True
except ImportError:
    APPLESCRIPT_AVAILABLE = False

from ..models.slide_data import SlideData, SlideInfo, SlideEvent
from ..models.enums import PresentationSoftware


logger = logging.getLogger(__name__)


class PowerPointMacMonitor:
    """PowerPoint monitoring implementation for macOS using AppleScript."""
    
    def __init__(self):
        if not APPLESCRIPT_AVAILABLE:
            raise RuntimeError("AppleScript not available. Install py-applescript: pip install py-applescript")
        
        self.is_monitoring = False
        self.current_slide_index = -1
        self.presentation_path = ""
        self.total_slides = 0
        
    def is_powerpoint_running(self) -> bool:
        """Check if PowerPoint is running."""
        try:
            script = '''
            tell application "System Events"
                return (name of processes) contains "Microsoft PowerPoint"
            end tell
            '''
            result = applescript.run(script)
            return result.out if result.code == 0 else False
        except Exception as e:
            logger.debug(f"Error checking PowerPoint status: {e}")
            return False
    
    def get_current_slide_info(self) -> Optional[SlideInfo]:
        """Get current slide information from PowerPoint."""
        if not self.is_powerpoint_running():
            return None
        
        try:
            # Get current slide index and total slides
            script = '''
            tell application "Microsoft PowerPoint"
                if (count of presentations) > 0 then
                    set currentPres to presentation 1
                    set slideCount to count of slides of currentPres
                    
                    -- Try to get current slide from slide show view
                    try
                        set currentSlide to slide index of slide show view of slide show window 1
                        set isSlideshow to true
                    on error
                        -- If not in slideshow, get from normal view
                        try
                            set currentSlide to slide index of view of document window 1
                            set isSlideshow to false
                        on error
                            set currentSlide to 1
                            set isSlideshow to false
                        end try
                    end try
                    
                    -- Get slide title
                    try
                        set slideTitle to title of slide currentSlide of currentPres
                    on error
                        set slideTitle to "Slide " & currentSlide
                    end try
                    
                    return {currentSlide, slideCount, slideTitle, isSlideshow}
                else
                    return {0, 0, "", false}
                end if
            end tell
            '''
            
            result = applescript.run(script)
            if result.code == 0 and result.out:
                slide_index, total_slides, slide_title, is_slideshow = result.out
                return SlideInfo(
                    slide_index=int(slide_index) - 1,  # Convert to 0-based
                    slide_title=str(slide_title),
                    total_slides=int(total_slides),
                    is_slideshow_mode=bool(is_slideshow)
                )
        except Exception as e:
            logger.error(f"Error getting slide info: {e}")
        
        return None
    
    def get_presentation_path(self) -> str:
        """Get the path of the current presentation."""
        if not self.is_powerpoint_running():
            return ""
        
        try:
            script = '''
            tell application "Microsoft PowerPoint"
                if (count of presentations) > 0 then
                    set currentPres to presentation 1
                    try
                        return path of currentPres
                    on error
                        return name of currentPres
                    end try
                else
                    return ""
                end if
            end tell
            '''
            
            result = applescript.run(script)
            return result.out if result.code == 0 else ""
        except Exception as e:
            logger.error(f"Error getting presentation path: {e}")
            return ""
    
    def get_speaker_notes(self, slide_index: int) -> str:
        """Get speaker notes for a specific slide."""
        if not self.is_powerpoint_running():
            return ""
        
        try:
            # Convert to 1-based index for AppleScript
            applescript_index = slide_index + 1
            
            script = f'''
            tell application "Microsoft PowerPoint"
                if (count of presentations) > 0 then
                    set currentPres to presentation 1
                    if {applescript_index} <= (count of slides of currentPres) then
                        try
                            set targetSlide to slide {applescript_index} of currentPres
                            set notesPage to notes page of targetSlide
                            set notesText to content of text range of text frame of shape 2 of notesPage
                            return notesText
                        on error
                            return ""
                        end try
                    else
                        return ""
                    end if
                else
                    return ""
                end if
            end tell
            '''
            
            result = applescript.run(script)
            return result.out if result.code == 0 else ""
        except Exception as e:
            logger.error(f"Error getting speaker notes for slide {slide_index}: {e}")
            return ""


class PresentationMonitor:
    """Main presentation monitoring service."""
    
    def __init__(self, software_type: PresentationSoftware = PresentationSoftware.POWERPOINT):
        """
        Initialize the presentation monitor.
        
        Args:
            software_type: Type of presentation software to monitor
        """
        self.software_type = software_type
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Monitoring state
        self.current_slide_info: Optional[SlideInfo] = None
        self.last_check_time = datetime.now()
        self.poll_interval = 1.0  # seconds
        
        # Callbacks
        self.slide_change_callback: Optional[Callable[[SlideEvent], None]] = None
        self.presentation_start_callback: Optional[Callable[[SlideEvent], None]] = None
        self.presentation_end_callback: Optional[Callable[[SlideEvent], None]] = None
        
        # Initialize software-specific monitor
        self._init_software_monitor()
        
        logger.info(f"PresentationMonitor initialized for {software_type.value}")
    
    def _init_software_monitor(self) -> None:
        """Initialize the software-specific monitor."""
        if self.software_type == PresentationSoftware.POWERPOINT:
            try:
                self.software_monitor = PowerPointMacMonitor()
            except RuntimeError as e:
                logger.error(f"Failed to initialize PowerPoint monitor: {e}")
                raise
        else:
            raise NotImplementedError(f"Monitoring for {self.software_type.value} not yet implemented")
    
    async def start_monitoring(self, callback: Callable[[SlideEvent], None]) -> None:
        """
        Start monitoring for slide changes.
        
        Args:
            callback: Function to call when slide changes occur
        """
        if self.is_monitoring:
            logger.warning("Monitoring already started")
            return
        
        self.slide_change_callback = callback
        self.is_monitoring = True
        self.stop_event.clear()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Presentation monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring for slide changes."""
        if not self.is_monitoring:
            return
        
        logger.info("Stopping presentation monitoring")
        
        self.is_monitoring = False
        self.stop_event.set()
        
        # Wait for monitor thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
            if self.monitor_thread.is_alive():
                logger.warning("Monitor thread did not stop gracefully")
        
        logger.info("Presentation monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        logger.debug("Monitor loop started")
        
        presentation_was_active = False
        
        while self.is_monitoring and not self.stop_event.is_set():
            try:
                # Check if presentation software is running
                is_presentation_active = self._is_presentation_active()
                
                # Handle presentation lifecycle events
                if is_presentation_active and not presentation_was_active:
                    self._handle_presentation_started()
                elif not is_presentation_active and presentation_was_active:
                    self._handle_presentation_ended()
                
                presentation_was_active = is_presentation_active
                
                # Check for slide changes if presentation is active
                if is_presentation_active:
                    self._check_slide_changes()
                
                # Update last check time
                self.last_check_time = datetime.now()
                
                # Wait before next check
                self.stop_event.wait(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                # Continue monitoring despite errors
                self.stop_event.wait(self.poll_interval)
        
        logger.debug("Monitor loop ended")
    
    def _is_presentation_active(self) -> bool:
        """Check if presentation software is active."""
        try:
            if self.software_type == PresentationSoftware.POWERPOINT:
                return self.software_monitor.is_powerpoint_running()
            else:
                return False
        except Exception as e:
            logger.error(f"Error checking presentation status: {e}")
            return False
    
    def _check_slide_changes(self) -> None:
        """Check for slide changes and trigger callbacks."""
        try:
            current_info = self.software_monitor.get_current_slide_info()
            
            if current_info is None:
                return
            
            # Check if slide has changed
            if (self.current_slide_info is None or 
                current_info.slide_index != self.current_slide_info.slide_index):
                
                # Get full slide data
                slide_data = self._create_slide_data(current_info)
                
                # Create slide event
                event = SlideEvent(
                    event_type="slide_changed",
                    slide_data=slide_data
                )
                
                # Update current slide info
                self.current_slide_info = current_info
                
                # Trigger callback
                if self.slide_change_callback:
                    try:
                        self.slide_change_callback(event)
                    except Exception as e:
                        logger.error(f"Error in slide change callback: {e}")
                
                logger.info(f"Slide changed to {current_info.slide_index + 1}/{current_info.total_slides}: {current_info.slide_title}")
        
        except Exception as e:
            logger.error(f"Error checking slide changes: {e}")
    
    def _create_slide_data(self, slide_info: SlideInfo) -> SlideData:
        """Create SlideData from SlideInfo."""
        # Get speaker notes
        speaker_notes = ""
        try:
            speaker_notes = self.software_monitor.get_speaker_notes(slide_info.slide_index)
        except Exception as e:
            logger.warning(f"Could not get speaker notes: {e}")
        
        # Get presentation path
        presentation_path = ""
        try:
            presentation_path = self.software_monitor.get_presentation_path()
        except Exception as e:
            logger.warning(f"Could not get presentation path: {e}")
        
        return SlideData(
            slide_index=slide_info.slide_index,
            slide_title=slide_info.slide_title,
            speaker_notes=speaker_notes,
            presentation_path=presentation_path,
            timestamp=datetime.now()
        )
    
    def _handle_presentation_started(self) -> None:
        """Handle presentation started event."""
        logger.info("Presentation started")
        
        event = SlideEvent(
            event_type="presentation_started"
        )
        
        if self.presentation_start_callback:
            try:
                self.presentation_start_callback(event)
            except Exception as e:
                logger.error(f"Error in presentation start callback: {e}")
    
    def _handle_presentation_ended(self) -> None:
        """Handle presentation ended event."""
        logger.info("Presentation ended")
        
        event = SlideEvent(
            event_type="presentation_ended"
        )
        
        self.current_slide_info = None
        
        if self.presentation_end_callback:
            try:
                self.presentation_end_callback(event)
            except Exception as e:
                logger.error(f"Error in presentation end callback: {e}")
    
    def get_current_slide(self) -> Optional[SlideInfo]:
        """Get current slide information."""
        return self.current_slide_info
    
    def is_presentation_active(self) -> bool:
        """Check if presentation is currently active."""
        return self._is_presentation_active()
    
    def set_poll_interval(self, interval: float) -> None:
        """
        Set the polling interval for slide change detection.
        
        Args:
            interval: Polling interval in seconds
        """
        if interval < 0.1:
            raise ValueError("Poll interval must be at least 0.1 seconds")
        
        self.poll_interval = interval
        logger.debug(f"Poll interval set to {interval} seconds")
    
    def get_poll_interval(self) -> float:
        """Get current polling interval."""
        return self.poll_interval
    
    def set_presentation_start_callback(self, callback: Callable[[SlideEvent], None]) -> None:
        """Set callback for presentation start events."""
        self.presentation_start_callback = callback
    
    def set_presentation_end_callback(self, callback: Callable[[SlideEvent], None]) -> None:
        """Set callback for presentation end events."""
        self.presentation_end_callback = callback
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'is_monitoring': self.is_monitoring,
            'software_type': self.software_type.value,
            'presentation_active': self.is_presentation_active(),
            'current_slide': self.current_slide_info.to_dict() if self.current_slide_info else None,
            'last_check_time': self.last_check_time.isoformat(),
            'poll_interval': self.poll_interval
        }
    
    def shutdown(self) -> None:
        """Shutdown the presentation monitor."""
        logger.info("Shutting down PresentationMonitor")
        
        # Stop monitoring synchronously
        if self.is_monitoring:
            self.is_monitoring = False
            self.stop_event.set()
            
            # Wait for monitor thread to finish
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5.0)
                if self.monitor_thread.is_alive():
                    logger.warning("Monitor thread did not stop gracefully")
        
        logger.info("PresentationMonitor shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()