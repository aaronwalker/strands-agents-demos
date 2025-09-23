"""OrikContent model for extracted Orik-tagged content."""

from dataclasses import dataclass
from typing import List, Optional
import re

from .slide_data import SlideData


@dataclass
class OrikContent:
    """Represents content extracted from Orik tags in speaker notes."""
    
    raw_text: str
    extracted_tags: List[str]
    context: Optional[str]
    slide_reference: SlideData
    
    def __post_init__(self):
        """Validate and process Orik content after initialization."""
        if not isinstance(self.extracted_tags, list):
            raise ValueError("extracted_tags must be a list")
        
        if not isinstance(self.slide_reference, SlideData):
            raise ValueError("slide_reference must be a SlideData instance")
    
    @classmethod
    def extract_from_notes(cls, slide_data: SlideData) -> 'OrikContent':
        """Extract Orik-tagged content from slide speaker notes."""
        notes = slide_data.speaker_notes
        
        # Pattern to match [Orik] tags and their content
        # Captures content until next [tag] or end of string, including newlines
        orik_pattern = r'\[Orik\]\s*(.*?)(?=\[|$)'
        matches = re.findall(orik_pattern, notes, re.IGNORECASE | re.DOTALL)
        
        # Clean up extracted content
        extracted_tags = [match.strip() for match in matches if match.strip()]
        
        # Use slide title as context if available
        context = slide_data.slide_title if slide_data.slide_title else None
        
        return cls(
            raw_text=notes,
            extracted_tags=extracted_tags,
            context=context,
            slide_reference=slide_data
        )
    
    @property
    def has_orik_tags(self) -> bool:
        """Check if any Orik tags were found."""
        return len(self.extracted_tags) > 0
    
    @property
    def tag_count(self) -> int:
        """Get the number of Orik tags found."""
        return len(self.extracted_tags)
    
    def get_combined_content(self) -> str:
        """Get all Orik tag content combined into a single string."""
        return " ".join(self.extracted_tags)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'raw_text': self.raw_text,
            'extracted_tags': self.extracted_tags,
            'context': self.context,
            'slide_reference': self.slide_reference.to_dict(),
            'has_orik_tags': self.has_orik_tags,
            'tag_count': self.tag_count
        }