import openai
import logging
import os
from enum import Enum
try:
    from helpers.speech_to_text import SpeechToText
except ImportError:
    SpeechToText = None  # Handle missing import in container
from helpers.LLMs import BaseLLM
import re
from typing import Dict, List, Optional

# Try relative import first (for Nevil nodes), fall back to agents path
try:
    from .completion.factory import get_completion_provider
except ImportError:
    try:
        from agents.completion.factory import get_completion_provider
    except ImportError:
        # Final fallback - import from nodes path
        from nodes.ai_cognition.completion.factory import get_completion_provider

# Configure logging
logger = logging.getLogger("streamlit")
logger.setLevel(logging.DEBUG)

class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Context management settings (can be overridden by subclasses)
        self.prune_threshold = 110000    # Start pruning at 110k tokens
        self.prune_target = 90000        # Prune down to 90k
        self.keep_recent_n = 25          # Keep last 25 messages
        self._did_prune = False          # Track if pruning occurred
		
        # Load environment variables centrally
        self._load_env_variables()
        # Initialize completion provider based on COMPLETION_API env var
        # Provider handles its own env var loading internally
        self.completion_provider = get_completion_provider()
		
    def _load_env_variables(self):
        """
        Load common environment variables for all agents.

        Child agents can override this to add their specific env vars.
        """
        # Log which completion provider will be used
        nevil_ai = os.getenv("NEVIL_AI", "ollama")
        self.logger.info(f"Using completion provider: {nevil_ai}")
    
    def transcribe_audio(self, audio_file: str) -> Optional[str]:
        """Transcribe audio file using configured STT service"""
        try:
            # Check if STT service is initialized
            if not hasattr(self, 'stt_service') or self.stt_service is None:
                # Try to initialize STT service if the agent has an initialize_stt method
                if hasattr(self, 'initialize_stt'):
                    logger.info("Attempting to initialize STT service")
                    self.initialize_stt()
                
                # Check again if STT service is now available
                if not hasattr(self, 'stt_service') or self.stt_service is None:
                    logger.error("No STT service configured")
                    return None
                
            # Transcribe audio
            text, _ = self.stt_service.transcribe(audio_file)  # Ignore processing time
            
            # Clean up transcription
            if text:
                # Remove extra spaces
                text = re.sub(r'\s+', ' ', text)
                # Fix spacing after punctuation
                text = re.sub(r'([.,!?])([^\s])', r'\1 \2', text)
                # Ensure proper spacing between words
                text = re.sub(r'\s+', ' ', text)
                text = text.strip()
                
            return text
            
        except Exception as e:
            logger.error(f"Error in audio transcription: {str(e)}")
            return None

    def get_chat_response(self, unformatted_messages: str, formatted_messages: Optional[List[Dict[str, str]]] = None, file_path: Optional[str] = None, assistant_id: Optional[str] = None, temperature: Optional[float] = None, tools: Optional[List[Dict]] = None, tool_choice: Optional[str] = "auto"):
        #print(f"DEBUG: BaseAgent.get_chat_response called for {self.__class__.__name__}")

        use_openai = os.getenv("USE_OPENAI", "false").lower() == "true"

        if use_openai:
            model = os.getenv("OPENAI_MODEL") or os.getenv("REACT_APP_OPENAI_MODEL", "gpt-4o-mini")
            logger.info(f"Using OpenAI model: {model}")
        else:
            model = os.getenv("OLLAMA_MODEL")
            if not model:
                raise ValueError("OLLAMA_MODEL environment variable must be set in .env file")
            logger.info(f"Using Ollama model: {model}")

        #TODO: Add support for other models, passed in by named and role agents
        #Dum = RagerAgent(name="Dum", model="gpt-4o")
        #Woz = RagerAgent(name="Woz", model="gpt-4o")
        #Worker = RagerAgent(name="Worker", model="gpt-4-turbo")
        #Piper = RagerAgent(name="Piper", model="gpt-4-mini")

        try:
            # Collect all system messages from the agent hierarchy
            system_messages = []

            # Check for base_messages (defined in AgentSupervisor)
            if hasattr(self, 'base_messages'):
                system_messages.extend(self.base_messages)

            # Check for additional_messages (defined in specific agents like AgentBlane)
            if hasattr(self, 'additional_messages'):
                #print(f"DEBUG: Found {len(self.additional_messages)} additional_messages")
                system_messages.extend(self.additional_messages)

            # If formatted messages are provided, combine with system messages
            if formatted_messages is not None:
                combined_messages = system_messages + formatted_messages #+ projects_message + notes_message
                return self.completion_provider.get_completion(combined_messages, temperature=temperature)
            # Otherwise, create a message from the unformatted messages and combine with system messages
            else:
                user_message = [{"role": "user", "content": unformatted_messages}]
                combined_messages = system_messages + user_message #+ projects_message + notes_message
                return self.completion_provider.get_completion(combined_messages, temperature=temperature)
        except Exception as e:
            logger.error(f"Error getting chat response: {str(e)}")
            return None
    
    def _check_context_length(self, combined_messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Check context length and prune if needed.
        Subclasses can override to provide custom summarization.
        
        Returns:
            Warning string if context still too large, None otherwise
        """
        from helpers.context import count_message_tokens, prune_with_summary
        
        # Get model name (set by subclass)
        model_name = getattr(self, 'model_name', 'gpt-4')
        
        total_tokens = count_message_tokens(combined_messages, model=model_name)
        logging.info(f"Total context length: {total_tokens:,} tokens")
        
        self._did_prune = False
        
        # Prune if over threshold
        if total_tokens > self.prune_threshold:
            logging.info(f"Token count {total_tokens} exceeds {self.prune_threshold}, pruning")
            
            # Get summarization callback if available
            summarize_callback = getattr(self, '_get_summarization_callback', lambda: None)()
            
            combined_messages[:], self._did_prune = prune_with_summary(
                combined_messages,
                target_tokens=self.prune_target,
                model=model_name,
                summarize_callback=summarize_callback,
                keep_recent_n=self.keep_recent_n
            )
            
            total_tokens = count_message_tokens(combined_messages, model_name)
            logging.info(f"After pruning: {total_tokens} tokens")
        
        # Warn if still too large
        if total_tokens > 120000:
            warning = f"⚠️ Context approaching 128k limit. Current: {total_tokens:,} tokens."
            logging.warning(warning)
            return warning
        
        return None