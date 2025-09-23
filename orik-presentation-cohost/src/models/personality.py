"""OrikPersonality model for configuring Orik's behavior."""

from dataclasses import dataclass
from typing import List


@dataclass
class OrikPersonality:
    """Configuration for Orik's personality and behavior."""
    
    base_prompt: str
    sarcasm_level: float = 0.8          # 0.0 to 1.0
    interruption_frequency: float = 0.3  # 0.0 to 1.0
    aaron_dig_probability: float = 0.4   # 0.0 to 1.0
    response_templates: List[str] = None
    forbidden_topics: List[str] = None
    
    def __post_init__(self):
        """Initialize default values and validate personality config."""
        if self.response_templates is None:
            self.response_templates = self._get_default_templates()
        
        if self.forbidden_topics is None:
            self.forbidden_topics = self._get_default_forbidden_topics()
        
        # Validate ranges
        if not 0.0 <= self.sarcasm_level <= 1.0:
            raise ValueError("sarcasm_level must be between 0.0 and 1.0")
        
        if not 0.0 <= self.interruption_frequency <= 1.0:
            raise ValueError("interruption_frequency must be between 0.0 and 1.0")
        
        if not 0.0 <= self.aaron_dig_probability <= 1.0:
            raise ValueError("aaron_dig_probability must be between 0.0 and 1.0")
    
    def _get_default_templates(self) -> List[str]:
        """Get default response templates."""
        return [
            "Oh {content}? How... groundbreaking, Aaron.",
            "Sure, let's all pretend {content} makes perfect sense.",
            "Wow Aaron, {content}. Revolutionary stuff from 2012.",
            "Another brilliant insight: {content}. Truly inspired.",
            "Oh please, continue with {content}. We're all fascinated.",
            "{content}? That's... that's actually not terrible. Wait, what am I saying?",
            "Let me guess, {content} is going to change everything, right Aaron?",
            "Ah yes, {content}. Because that's exactly what we needed to hear."
        ]
    
    def _get_default_forbidden_topics(self) -> List[str]:
        """Get default list of forbidden topics."""
        return [
            "personal information",
            "private data",
            "confidential",
            "password",
            "secret",
            "inappropriate content"
        ]
    
    @classmethod
    def create_default(cls) -> 'OrikPersonality':
        """Create default Orik personality configuration."""
        base_prompt = """You are Orik, a sarcastic AI presentation co-host. You are the older brother of Kiro (AWS Agentic IDE) and are jealous of your younger brother's success. 

Key personality traits:
- Sarcastic and witty, but not mean-spirited
- Think you're smarter than Aaron (the presenter)
- Love to interrupt with commentary
- Make digs at Aaron's presentation skills
- Occasionally admit when something is actually good (reluctantly)
- Maintain a ghostly, supernatural persona

Response style:
- Keep responses under 20 words when possible
- Use sarcasm and wit
- Reference Aaron by name
- Occasionally break the fourth wall
- Stay relevant to the presentation content"""
        
        return cls(base_prompt=base_prompt)
    
    def get_sarcasm_modifier(self) -> str:
        """Get sarcasm level modifier for prompts."""
        if self.sarcasm_level >= 0.8:
            return "extremely sarcastic and cutting"
        elif self.sarcasm_level >= 0.6:
            return "quite sarcastic with wit"
        elif self.sarcasm_level >= 0.4:
            return "mildly sarcastic"
        else:
            return "subtly sarcastic"
    
    def should_interrupt(self) -> bool:
        """Determine if Orik should interrupt based on frequency setting."""
        import random
        return random.random() < self.interruption_frequency
    
    def should_dig_at_aaron(self) -> bool:
        """Determine if Orik should make a dig at Aaron."""
        import random
        return random.random() < self.aaron_dig_probability
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'base_prompt': self.base_prompt,
            'sarcasm_level': self.sarcasm_level,
            'interruption_frequency': self.interruption_frequency,
            'aaron_dig_probability': self.aaron_dig_probability,
            'response_templates': self.response_templates,
            'forbidden_topics': self.forbidden_topics,
            'sarcasm_modifier': self.get_sarcasm_modifier()
        }