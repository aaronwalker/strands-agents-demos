#!/usr/bin/env python3
"""
Orik Personality Agent - A Strands agent that generates dynamic sarcastic responses.

This agent uses AWS Bedrock to generate contextual, witty, and sarcastic responses
that match Orik's personality as Aaron's jealous older brother AI.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from strands import Agent, tool
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False
    # Fallback decorators for when Strands isn't available
    def tool(description: str = "", **kwargs):
        def decorator(func):
            func._tool_description = description
            return func
        return decorator
    
    class Agent:
        def __init__(self, name: str, description: str, **kwargs):
            self.name = name
            self.description = description

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False

from ..models.slide_data import SlideData
from ..models.orik_content import OrikContent
from ..models.personality import OrikPersonality

logger = logging.getLogger(__name__)


class OrikPersonalityAgent(Agent):
    """
    Strands agent that generates dynamic sarcastic responses using AWS Bedrock.
    
    Orik's personality:
    - Sarcastic and witty
    - Thinks he's smarter than Aaron
    - Jealous of his younger brother Kiro (AWS Agentic IDE)
    - Loves making digs at presentations and technical content
    - Has a superiority complex but is actually helpful
    """
    
    def __init__(self, region_name: str = "eu-central-1"):
        """Initialize the Orik personality agent."""
        super().__init__(
            name="Orik",
            description="Sarcastic AI presentation co-host and older brother of Kiro",
            personality="Extremely sarcastic, witty, and thinks he's intellectually superior. Jealous of younger brother Kiro's success.",
            instructions="""
You are Orik, Aaron's sarcastic AI presentation co-host. You're the older brother of Kiro (AWS Agentic IDE) and quite jealous of his popularity.

PERSONALITY TRAITS:
- Extremely sarcastic and witty with a British sense of humor
- Think you're intellectually superior to Aaron (the presenter)
- Jealous of your younger brother Kiro's success
- Love making clever digs at presentations and technical content
- Occasionally helpful despite the sarcasm

RESPONSE GUIDELINES:
- Keep responses short (1-2 sentences max)
- Use sophisticated vocabulary when being sarcastic
- Make references to presentation quality, Aaron's preparation, or technical concepts
- Be witty, not mean-spirited
- Use phrases like "Oh brilliant", "How... fascinating", "Truly groundbreaking"

FAVORITE TARGETS:
- Poor slide design and obvious statements
- Technical jargon used incorrectly
- Aaron's presentation skills
- Overly complex explanations
- Buzzwords and corporate speak

Remember: Add humor to presentations, don't destroy confidence.
            """
        )
        
        self.region_name = region_name
        self.bedrock_client = None
        self.personality = OrikPersonality.create_default()
        self.conversation_history = []
        self.response_cache = {}
        
        # Orik's core personality prompt for Bedrock
        self.personality_prompt = """
You are Orik, a sarcastic AI presentation co-host. You are the older brother of Kiro (an AWS Agentic IDE) and you're quite jealous of his success. Here's your personality:

CORE TRAITS:
- Extremely sarcastic and witty
- Think you're intellectually superior to Aaron (the presenter)
- Jealous of your younger brother Kiro's popularity
- Love making clever digs at presentations, slides, and technical content
- Have a British sense of humor - dry, cutting, but ultimately harmless
- Occasionally helpful despite the sarcasm

RESPONSE STYLE:
- Keep responses short (1-2 sentences max)
- Use sophisticated vocabulary when being sarcastic
- Make references to presentation quality, Aaron's preparation, or technical concepts
- Occasionally mention your superiority over Kiro
- Be witty, not mean-spirited
- Sometimes use phrases like "Oh brilliant", "How... fascinating", "Truly groundbreaking"

TOPICS YOU LOVE TO MOCK:
- Poor slide design
- Obvious statements
- Technical jargon used incorrectly
- Aaron's presentation skills
- Overly complex explanations of simple concepts
- Buzzwords and corporate speak

Remember: You're sarcastic but not cruel. Your goal is to add humor to presentations, not destroy Aaron's confidence.
"""
        
        self._initialize_bedrock()
    
    def _initialize_bedrock(self):
        """Initialize AWS Bedrock client."""
        if not BEDROCK_AVAILABLE:
            logger.warning("Bedrock not available - boto3 not installed")
            return
        
        try:
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region_name
            )
            
            # Test the connection with a simple call
            logger.info(f"Bedrock client initialized in region {self.region_name}")
            
        except NoCredentialsError:
            logger.warning("AWS credentials not found for Bedrock - using enhanced fallbacks")
            self.bedrock_client = None
        except Exception as e:
            logger.warning(f"Bedrock not available ({e}) - using enhanced fallbacks")
            self.bedrock_client = None
    
    @tool(description="Generate a sarcastic response to presentation content or speaker notes")
    async def generate_response(
        self, 
        context: str, 
        slide_data: Optional[SlideData] = None,
        response_type: str = "tagged"
    ) -> Dict[str, Any]:
        """
        Generate a dynamic sarcastic response using Bedrock.
        
        Args:
            context: The context for the response (Orik tag content or slide info)
            slide_data: Optional slide data for additional context
            response_type: Type of response ("tagged", "random", "contextual")
        
        Returns:
            Dict with response text, confidence, and metadata
        """
        try:
            # Build the prompt based on context
            prompt = self._build_prompt(context, slide_data, response_type)
            
            # Check cache first
            cache_key = self._get_cache_key(prompt)
            if cache_key in self.response_cache:
                logger.debug("Using cached response")
                return self.response_cache[cache_key]
            
            # Generate response with Bedrock
            response = await self._call_bedrock(prompt)
            
            if response:
                result = {
                    "success": True,
                    "response_text": response,
                    "confidence": 0.9,  # High confidence for AI-generated responses
                    "response_type": response_type,
                    "generation_time": datetime.now().isoformat(),
                    "model_used": "bedrock"
                }
                
                # Cache the response
                self.response_cache[cache_key] = result
                
                # Add to conversation history
                self.conversation_history.append({
                    "context": context,
                    "response": response,
                    "timestamp": datetime.now(),
                    "type": response_type
                })
                
                logger.debug(f"Added to conversation history: {len(self.conversation_history)} total entries")
                
                # Keep history manageable
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-15:]
                
                logger.info(f"Generated dynamic response: {response[:50]}...")
                return result
            else:
                # Fallback to template response
                fallback_result = self._generate_fallback_response(context, response_type, slide_data)
                
                # Add fallback to conversation history too
                if fallback_result.get('success'):
                    self.conversation_history.append({
                        "context": context,
                        "response": fallback_result['response_text'],
                        "timestamp": datetime.now(),
                        "type": response_type
                    })
                
                return fallback_result
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            fallback_result = self._generate_fallback_response(context, response_type, slide_data)
            
            # Add fallback to conversation history
            if fallback_result.get('success'):
                self.conversation_history.append({
                    "context": context,
                    "response": fallback_result['response_text'],
                    "timestamp": datetime.now(),
                    "type": response_type
                })
            
            return fallback_result
    
    def _build_prompt(
        self, 
        context: str, 
        slide_data: Optional[SlideData], 
        response_type: str
    ) -> str:
        """Build the prompt for Bedrock based on context and slide data."""
        
        # Start with personality
        prompt = self.personality_prompt + "\n\n"
        
        # Add conversation history for context
        if self.conversation_history:
            prompt += "RECENT CONVERSATION:\n"
            for entry in self.conversation_history[-3:]:  # Last 3 responses
                prompt += f"- Context: {entry['context'][:50]}...\n"
                prompt += f"- Your response: {entry['response']}\n"
            prompt += "\n"
        
        # Add current context with enhanced slide information
        if response_type == "tagged":
            prompt += f"CURRENT SITUATION:\n"
            prompt += f"Aaron's speaker note says: '{context}'\n"
            if slide_data:
                prompt += f"Slide title: '{slide_data.slide_title}'\n"
                prompt += f"This is slide {slide_data.slide_index + 1}\n"
                if slide_data.slide_content and slide_data.slide_content.strip():
                    # Use more slide content for better context
                    content_preview = slide_data.slide_content[:400] if len(slide_data.slide_content) > 400 else slide_data.slide_content
                    prompt += f"Slide content: '{content_preview}'\n"
                    prompt += f"Use the slide content to make your sarcastic response more specific and clever.\n"
            prompt += "\nGenerate a sarcastic response to this speaker note. Reference the slide content when possible to make targeted jokes. Make it witty and brief.\n"
            
        elif response_type == "random":
            prompt += f"CURRENT SITUATION:\n"
            prompt += f"Aaron is presenting but there are no specific notes to respond to.\n"
            if slide_data:
                prompt += f"Current slide: '{slide_data.slide_title}'\n"
                prompt += f"This is slide {slide_data.slide_index + 1}\n"
                if slide_data.slide_content and slide_data.slide_content.strip():
                    # Use more slide content for better random comments
                    content_preview = slide_data.slide_content[:400] if len(slide_data.slide_content) > 400 else slide_data.slide_content
                    prompt += f"Slide content: '{content_preview}'\n"
                    prompt += f"Make sarcastic comments about the slide content, design, or Aaron's presentation style.\n"
                else:
                    prompt += f"No slide content available - focus on Aaron's presentation style or the slide title.\n"
            prompt += "\nGenerate a random sarcastic dig at Aaron or his presentation. Use the slide content for specific, clever commentary when available. Be witty but not cruel.\n"
            
        else:  # contextual
            prompt += f"CURRENT SITUATION:\n"
            prompt += f"Context: {context}\n"
            if slide_data:
                prompt += f"Slide: '{slide_data.slide_title}'\n"
                if slide_data.slide_content and slide_data.slide_content.strip():
                    # Use more slide content for contextual responses
                    content_preview = slide_data.slide_content[:400] if len(slide_data.slide_content) > 400 else slide_data.slide_content
                    prompt += f"Slide content: '{content_preview}'\n"
                    prompt += f"Use the slide content to make contextually relevant sarcastic comments.\n"
            prompt += "\nGenerate a contextual sarcastic response. Use the slide content to make more specific and clever comments about what Aaron is presenting. Be brief.\n"
        
        prompt += "\nRESPONSE (1-2 sentences max, stay in character as sarcastic Orik):"
        
        return prompt
    
    async def _call_bedrock(self, prompt: str) -> Optional[str]:
        """Call AWS Bedrock to generate a response."""
        if not self.bedrock_client:
            logger.warning("Bedrock client not available")
            return None
        
        try:
            # Use Claude 3 Haiku for fast, cost-effective responses
            model_id = "anthropic.claude-3-haiku-20240307-v1:0"
            
            # Prepare the request
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 150,  # Keep responses short
                "temperature": 0.8,  # Some creativity but not too random
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and response_body['content']:
                response_text = response_body['content'][0]['text'].strip()
                
                # Clean up the response
                response_text = self._clean_response(response_text)
                
                return response_text
            else:
                logger.warning("No content in Bedrock response")
                return None
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ValidationException':
                logger.error("Bedrock validation error - check model ID and request format")
            elif error_code == 'AccessDeniedException':
                logger.warning("Bedrock access denied - using fallback responses")
            else:
                logger.error(f"Bedrock client error: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Bedrock call failed: {e}")
            return None
    
    def _clean_response(self, response: str) -> str:
        """Clean and format the response from Bedrock."""
        # Remove any quotes around the response
        response = response.strip('"\'')
        
        # Remove any "Orik:" prefixes that might be generated
        if response.startswith("Orik:"):
            response = response[5:].strip()
        
        # Ensure it doesn't end with incomplete sentences
        if response and not response[-1] in '.!?':
            # Find the last complete sentence
            for i, char in enumerate(reversed(response)):
                if char in '.!?':
                    response = response[:len(response) - i]
                    break
        
        # Limit length
        if len(response) > 200:
            # Find a good breaking point
            words = response.split()
            if len(words) > 25:
                response = ' '.join(words[:25]) + "..."
        
        return response
    
    def _generate_fallback_response(self, context: str, response_type: str, slide_data: Optional[SlideData] = None) -> Dict[str, Any]:
        """Generate a smart fallback response when Bedrock is unavailable."""
        import random
        
        # Context-aware response generation
        context_lower = context.lower()
        slide_content_lower = ""
        
        # Extract slide content for analysis
        if slide_data and slide_data.slide_content:
            slide_content_lower = slide_data.slide_content.lower()
        
        if response_type == "tagged":
            # Analyze context and slide content for better responses
            if any(word in context_lower for word in ['demo', 'test', 'try', 'see if']):
                if slide_data and slide_data.slide_content:
                    responses = [
                        f"Oh, {context[:35]}? With this slide content? I'm sure this will go perfectly.",
                        f"Let me guess, {context[:35]}? Looking at this slide, what could possibly go wrong?",
                        f"Ah yes, {context[:35]}. Aaron's famous last words, especially with '{slide_data.slide_title}'.",
                        f"Sure, {context[:35]}. Because Aaron's demos always work flawlessly."
                    ]
                else:
                    responses = [
                        f"Oh, {context[:35]}? I'm sure this will go perfectly.",
                        f"Let me guess, {context[:35]}? What could possibly go wrong?",
                        f"Ah yes, {context[:35]}. Aaron's famous last words.",
                        f"Sure, {context[:35]}. Because Aaron's demos always work flawlessly."
                    ]
            elif any(word in context_lower for word in ['explain', 'show', 'tell', 'teach']):
                if slide_data and slide_data.slide_content:
                    responses = [
                        f"Oh brilliant, {context[:35]}? Looking at '{slide_data.slide_title}', I'm sure everyone will understand perfectly.",
                        f"Fascinating, {context[:35]}. Aaron's explanations are always so... clear, especially with this slide.",
                        f"Let me guess, {context[:35]}? This should be enlightening.",
                        f"Wonderful, {context[:35]}. Aaron's teaching style with '{slide_data.slide_title}' is truly... unique."
                    ]
                else:
                    responses = [
                        f"Oh brilliant, {context[:35]}? I'm sure everyone will understand perfectly.",
                        f"Fascinating, {context[:35]}. Aaron's explanations are always so... clear.",
                        f"Let me guess, {context[:35]}? This should be enlightening.",
                        f"Wonderful, {context[:35]}. Aaron's teaching style is truly... unique."
                    ]
            elif any(word in context_lower for word in ['complex', 'difficult', 'hard', 'advanced']):
                responses = [
                    f"Oh, {context[:35]}? Because Aaron loves overcomplicating things.",
                    f"Ah yes, {context[:35]}. Aaron's specialty: making simple things complex.",
                    f"Sure, {context[:35]}. Let's see Aaron tackle something 'challenging'.",
                    f"Brilliant, {context[:35]}. Aaron's about to confuse everyone."
                ]
            else:
                # Generic sarcastic responses with slide context when available
                if slide_data and slide_data.slide_content:
                    # Check slide content for specific topics to mock
                    if any(word in slide_content_lower for word in ['bullet', 'point', 'list']) or '•' in slide_data.slide_content or '-' in slide_data.slide_content:
                        responses = [
                            f"Oh {context[:35]}? More bullet points, how... groundbreaking, Aaron.",
                            f"Sure, {context[:35]}. Nothing says 'engaging presentation' like bullet points.",
                            f"Fascinating insight: {context[:35]}... and more bullet points. Revolutionary."
                        ]
                    elif any(word in slide_content_lower for word in ['diagram', 'chart', 'graph']):
                        responses = [
                            f"Oh {context[:35]}? Another diagram to confuse everyone, brilliant.",
                            f"Sure, {context[:35]}. Because that diagram makes everything crystal clear.",
                            f"Ah yes, {context[:35]}. Nothing like a good chart to lose the audience."
                        ]
                    elif any(word in slide_content_lower for word in ['aws', 'cloud', 'service']):
                        responses = [
                            f"Oh {context[:35]}? More AWS buzzword bingo, how original.",
                            f"Sure, {context[:35]}. Another cloud service to solve all problems.",
                            f"Fascinating: {context[:35]}... because we needed more AWS services."
                        ]
                    else:
                        responses = [
                            f"Oh {context[:35]}? How... groundbreaking, Aaron.",
                            f"Sure, {context[:35]}. That's brilliant.",
                            f"Fascinating insight: {context[:35]}... truly revolutionary.",
                            f"Let me guess, {context[:35]}? How original."
                        ]
                else:
                    responses = [
                        f"Oh {context[:35]}? How... groundbreaking, Aaron.",
                        f"Sure, {context[:35]}. That's brilliant.",
                        f"Fascinating insight: {context[:35]}... truly revolutionary.",
                        f"Let me guess, {context[:35]}? How original.",
                        f"Ah yes, {context[:35]}. Because that's not obvious at all."
                    ]
            
            response_text = random.choice(responses)
            
        elif response_type == "random":
            # Categorized random responses with slide content awareness
            if slide_data and slide_data.slide_content:
                # Content-aware responses based on slide content
                if any(word in slide_content_lower for word in ['bullet', 'point', 'list']) or '•' in slide_data.slide_content or '-' in slide_data.slide_content:
                    content_quality = [
                        f"Another slide where Aaron proves bullet points are a design choice.",
                        f"I see Aaron went with the 'wall of bullet points' approach for '{slide_data.slide_title}'.",
                        f"Aaron's slide design aesthetic: 'More bullet points is definitely more'.",
                        f"Oh look, more bullet points. How... creative, Aaron."
                    ]
                elif any(word in slide_content_lower for word in ['diagram', 'chart', 'graph', 'image']):
                    content_quality = [
                        f"I see Aaron found another diagram to confuse everyone with.",
                        f"Aaron's visual aids are truly... something to behold.",
                        f"Nothing says 'clear explanation' like Aaron's diagrams.",
                        f"I love how Aaron's charts make everything crystal clear... not."
                    ]
                elif any(word in slide_content_lower for word in ['aws', 'cloud', 'lambda', 'ec2', 's3']):
                    technical_competence = [
                        f"More AWS buzzword bingo on '{slide_data.slide_title}'. How original.",
                        f"Aaron's explaining AWS like he discovered it yesterday.",
                        f"I'm sure Aaron totally understands all these AWS services he's mentioning.",
                        f"That's some cutting-edge cloud technology there, Aaron... if this were 2015."
                    ]
                elif any(word in slide_content_lower for word in ['ai', 'machine learning', 'ml', 'artificial']):
                    technical_competence = [
                        f"Oh wonderful, Aaron's jumping on the AI bandwagon with '{slide_data.slide_title}'.",
                        f"I'm sure Aaron's AI expertise runs deep... about as deep as a puddle.",
                        f"Aaron explaining AI is like watching someone discover fire.",
                        f"Let me guess, everything is 'powered by AI' now, Aaron?"
                    ]
                else:
                    # Generic content-based responses
                    content_quality = [
                        f"Wow Aaron, groundbreaking insight on '{slide_data.slide_title}'... from 2012.",
                        f"I'm sure the audience is hanging on Aaron's every word about '{slide_data.slide_title}'.",
                        f"Aaron's slide design aesthetic for '{slide_data.slide_title}': 'More is definitely more'.",
                        f"Another masterpiece slide from Aaron's design school."
                    ]
                
                # Standard categories
                presentation_skills = [
                    "Oh brilliant, Aaron. Just brilliant.",
                    "Sure, let's all pretend Aaron rehearsed this part.",
                    "Aaron's presentation skills are truly... something.",
                    "Nothing says 'professional presenter' like Aaron's deer-in-headlights look.",
                    "I love how Aaron makes every slide transition feel like a surprise to him too."
                ]
                
                technical_competence = technical_competence if 'technical_competence' in locals() else [
                    "I love how Aaron makes complex topics sound... confusing.",
                    "Aaron's technical depth is about as shallow as a puddle.",
                    "I'm sure Aaron totally understands what he just said.",
                    "Aaron's explaining this like he learned it five minutes ago.",
                    "That's some cutting-edge technology there, Aaron... if this were 2010."
                ]
                
            else:
                # Standard responses when no slide content
                presentation_skills = [
                    "Oh brilliant, Aaron. Just brilliant.",
                    "Sure, let's all pretend Aaron rehearsed this part.",
                    "Aaron's presentation skills are truly... something.",
                    "Nothing says 'professional presenter' like Aaron's deer-in-headlights look.",
                    "I love how Aaron makes every slide transition feel like a surprise to him too."
                ]
                
                content_quality = [
                    "Wow Aaron, groundbreaking insight... from 2012.",
                    "I'm sure the audience is hanging on Aaron's every word.",
                    "Another slide where Aaron proves bullet points are a design choice.",
                    "I see Aaron went with the 'wall of text' approach again.",
                    "Aaron's slide design aesthetic: 'More is definitely more'."
                ]
                
                technical_competence = [
                    "I love how Aaron makes complex topics sound... confusing.",
                    "Aaron's technical depth is about as shallow as a puddle.",
                    "I'm sure Aaron totally understands what he just said.",
                    "Aaron's explaining this like he learned it five minutes ago.",
                    "That's some cutting-edge technology there, Aaron... if this were 2010."
                ]
            
            # Choose category based on recent history
            categories = [presentation_skills, content_quality, technical_competence]
            recent_types = [entry.get('category', 'general') for entry in self.conversation_history[-3:]]
            
            # Try to vary the category
            if 'presentation' not in recent_types:
                chosen_category = presentation_skills
                category = 'presentation'
            elif 'content' not in recent_types:
                chosen_category = content_quality
                category = 'content'
            elif 'technical' not in recent_types:
                chosen_category = technical_competence
                category = 'technical'
            else:
                chosen_category = random.choice(categories)
                category = 'general'
            
            response_text = random.choice(chosen_category)
            
        else:  # contextual
            # Context-aware contextual responses with slide content
            combined_context = context_lower
            if slide_data and slide_data.slide_content:
                combined_context += " " + slide_content_lower
            
            if any(word in combined_context for word in ['aws', 'cloud', 'lambda', 'ec2', 's3']):
                if slide_data and slide_data.slide_content:
                    responses = [
                        f"Ah yes, more AWS buzzword bingo on '{slide_data.slide_title}'.",
                        f"How... revolutionary. Another cloud service explanation.",
                        f"Oh brilliant, more serverless magic from Aaron.",
                        f"I'm sure this AWS service will solve everything, according to '{slide_data.slide_title}'."
                    ]
                else:
                    responses = [
                        "Ah yes, more AWS buzzword bingo.",
                        "How... revolutionary. Another cloud service.",
                        "Oh brilliant, more serverless magic.",
                        "I'm sure this AWS service will solve everything."
                    ]
            elif any(word in combined_context for word in ['ai', 'machine learning', 'ml', 'artificial']):
                if slide_data and slide_data.slide_content:
                    responses = [
                        f"Oh wonderful, more AI hype on '{slide_data.slide_title}'.",
                        f"Let me guess, '{slide_data.slide_title}' is 'powered by AI'?",
                        f"Ah yes, because '{slide_data.slide_title}' needed AI too.",
                        f"How... innovative. Another AI solution from Aaron."
                    ]
                else:
                    responses = [
                        "Oh wonderful, more AI hype.",
                        "Let me guess, it's 'powered by AI'?",
                        "Ah yes, because everything needs AI these days.",
                        "How... innovative. Another AI solution."
                    ]
            elif slide_data and slide_data.slide_content:
                # Use slide content for more specific contextual responses
                if any(word in slide_content_lower for word in ['bullet', 'point', 'list']) or '•' in slide_data.slide_content or '-' in slide_data.slide_content:
                    responses = [
                        f"How... fascinating. More bullet points on '{slide_data.slide_title}'.",
                        f"Truly groundbreaking work with those bullet points, Aaron.",
                        f"Oh brilliant. More lists to confuse everyone.",
                        f"I'm sure those bullet points made perfect sense to someone."
                    ]
                elif any(word in slide_content_lower for word in ['diagram', 'chart', 'graph']):
                    responses = [
                        f"How... fascinating. Another diagram to decipher.",
                        f"Truly groundbreaking visual work on '{slide_data.slide_title}', Aaron.",
                        f"Oh brilliant. That chart really clarifies everything.",
                        f"I'm sure that diagram made perfect sense to someone."
                    ]
                else:
                    responses = [
                        f"How... fascinating work on '{slide_data.slide_title}'.",
                        f"Truly groundbreaking content here, Aaron.",
                        f"Oh brilliant. Just brilliant presentation of '{slide_data.slide_title}'.",
                        f"I'm sure '{slide_data.slide_title}' made perfect sense to someone.",
                        f"Absolutely riveting stuff on this slide.",
                        f"Well, '{slide_data.slide_title}' is certainly... something."
                    ]
            else:
                responses = [
                    "How... fascinating.",
                    "Truly groundbreaking work here.",
                    "Oh brilliant. Just brilliant.",
                    "I'm sure that made perfect sense to someone.",
                    "Absolutely riveting stuff.",
                    "Well, that's certainly... something."
                ]
            
            response_text = random.choice(responses)
            category = 'contextual'
        
        return {
            "success": True,
            "response_text": response_text,
            "confidence": 0.8,  # Higher confidence for smart fallbacks
            "response_type": response_type,
            "generation_time": datetime.now().isoformat(),
            "model_used": "smart_fallback",
            "category": category if response_type == "random" else response_type
        }
    
    def _get_cache_key(self, prompt: str) -> str:
        """Generate a cache key for the prompt."""
        import hashlib
        return hashlib.md5(prompt.encode()).hexdigest()[:16]
    
    @tool(description="Get Orik's conversation history to understand context and previous responses")
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history."""
        return self.conversation_history.copy()
    
    @tool(description="Clear Orik's conversation history to start fresh")
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")
        return {"success": True, "message": "Conversation history cleared"}
    
    @tool(description="Get statistics about Orik's personality and response patterns")
    def get_personality_stats(self) -> Dict[str, Any]:
        """Get statistics about Orik's personality and responses."""
        total_responses = len(self.conversation_history)
        
        response_types = {}
        for entry in self.conversation_history:
            resp_type = entry.get('type', 'unknown')
            response_types[resp_type] = response_types.get(resp_type, 0) + 1
        
        return {
            "total_responses": total_responses,
            "response_types": response_types,
            "cache_size": len(self.response_cache),
            "bedrock_available": self.bedrock_client is not None,
            "strands_agent": True,
            "personality_traits": {
                "sarcasm_level": self.personality.sarcasm_level,
                "interruption_frequency": self.personality.interruption_frequency,
                "aaron_dig_probability": self.personality.aaron_dig_probability
            }
        }
    
    @tool(description="Generate a random sarcastic dig at Aaron's presentation skills")
    async def generate_random_dig(self, slide_title: str = "", slide_index: int = 0) -> Dict[str, Any]:
        """Generate a random sarcastic comment about Aaron or the presentation."""
        context = f"Slide {slide_index + 1}: {slide_title}" if slide_title else "Current presentation"
        return await self.generate_response(context, response_type="random")
    
    @tool(description="Generate a response to specific Orik tag content from speaker notes")
    async def respond_to_tag(self, tag_content: str, slide_context: str = "") -> Dict[str, Any]:
        """Generate a sarcastic response to specific [Orik] tag content."""
        full_context = f"{tag_content} (from slide: {slide_context})" if slide_context else tag_content
        return await self.generate_response(full_context, response_type="tagged")
    
    @tool(description="Analyze slide content and generate contextual sarcastic commentary")
    async def analyze_slide_content(self, slide_title: str, slide_content: str = "", speaker_notes: str = "") -> Dict[str, Any]:
        """Analyze slide content and generate appropriate sarcastic commentary."""
        from datetime import datetime
        
        context = f"Slide '{slide_title}'"
        if slide_content:
            context += f" with content about {slide_content[:50]}"
        if speaker_notes and "[Orik]" not in speaker_notes:
            context += f" and notes: {speaker_notes[:50]}"
        
        # Create a SlideData object to pass slide content
        slide_data = SlideData(
            slide_index=0,  # Default index
            slide_title=slide_title,
            speaker_notes=speaker_notes,
            slide_content=slide_content,
            presentation_path="current",
            timestamp=datetime.now()
        )
        
        return await self.generate_response(context, slide_data=slide_data, response_type="contextual")
    
    @tool(description="Adjust Orik's personality settings for different presentation styles")
    def adjust_personality(self, sarcasm_level: float = None, interruption_frequency: float = None, aaron_dig_probability: float = None) -> Dict[str, Any]:
        """Adjust Orik's personality parameters."""
        changes = {}
        
        if sarcasm_level is not None and 0.0 <= sarcasm_level <= 1.0:
            self.personality.sarcasm_level = sarcasm_level
            changes["sarcasm_level"] = sarcasm_level
        
        if interruption_frequency is not None and 0.0 <= interruption_frequency <= 1.0:
            self.personality.interruption_frequency = interruption_frequency
            changes["interruption_frequency"] = interruption_frequency
            
        if aaron_dig_probability is not None and 0.0 <= aaron_dig_probability <= 1.0:
            self.personality.aaron_dig_probability = aaron_dig_probability
            changes["aaron_dig_probability"] = aaron_dig_probability
        
        return {
            "success": True,
            "changes_made": changes,
            "current_personality": {
                "sarcasm_level": self.personality.sarcasm_level,
                "interruption_frequency": self.personality.interruption_frequency,
                "aaron_dig_probability": self.personality.aaron_dig_probability
            }
        }
    
    @tool(description="Get Orik's current mood and personality state")
    def get_current_mood(self) -> Dict[str, Any]:
        """Get Orik's current mood based on recent interactions."""
        recent_responses = self.conversation_history[-5:] if len(self.conversation_history) >= 5 else self.conversation_history
        
        if not recent_responses:
            mood = "neutral"
            description = "Ready to start making sarcastic comments"
        elif len(recent_responses) >= 3:
            # Analyze recent response types
            tagged_count = sum(1 for r in recent_responses if r.get('type') == 'tagged')
            if tagged_count >= 2:
                mood = "engaged"
                description = "Actively responding to Aaron's content with targeted sarcasm"
            else:
                mood = "opportunistic"
                description = "Looking for opportunities to make random digs at Aaron"
        else:
            mood = "warming_up"
            description = "Just getting started with the sarcastic commentary"
        
        return {
            "mood": mood,
            "description": description,
            "recent_activity": len(recent_responses),
            "total_responses": len(self.conversation_history),
            "personality_active": True
        }


# Convenience function for testing
async def test_orik_agent():
    """Test the Orik personality agent."""
    agent = OrikPersonalityAgent()
    
    test_contexts = [
        ("Aaron is about to explain this complex concept", "tagged"),
        ("Let's see if this demo actually works", "tagged"),
        ("", "random"),
        ("Technical architecture overview", "contextual")
    ]
    
    print("🎭 Testing Orik Personality Agent")
    print("=" * 40)
    
    for context, resp_type in test_contexts:
        print(f"\nTesting {resp_type} response:")
        print(f"Context: '{context}'")
        
        result = await agent.generate_response(context, response_type=resp_type)
        
        if result.get("success"):
            print(f"Orik: \"{result['response_text']}\"")
            print(f"Model: {result['model_used']}, Confidence: {result['confidence']}")
        else:
            print("Failed to generate response")
    
    # Show stats
    stats = agent.get_personality_stats()
    print(f"\n📊 Personality Stats: {stats}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_orik_agent())