"""pyttsx3 TTS provider - Fast local TTS"""

import logging
from typing import Optional
from .base import TTSProviderBase

logger = logging.getLogger(__name__)


class Pyttsx3TTSProvider(TTSProviderBase):
    """
    TTS provider using pyttsx3 (local, offline, instant).

    Pros:
        - Very fast (~instant generation)
        - No API costs
        - Works offline
        - No network latency

    Cons:
        - Robotic/synthetic voice quality
        - Limited voice options
        - Platform-dependent voices
    """

    def __init__(self):
        """Initialize pyttsx3 TTS provider"""
        try:
            import pyttsx3

            # Initialize with espeak driver explicitly
            self.engine = pyttsx3.init(driverName='espeak', debug=False)

            # Get available voices before trying to set properties
            voices = self.engine.getProperty('voices')
            logger.info(f"Found {len(voices) if voices else 0} voices")

            # Configure voice properties safely
            try:
                # Rate: speed of speech (default ~200)
                self.engine.setProperty('rate', 180)  # Slightly slower for clarity
            except Exception as e:
                logger.warning(f"Could not set rate: {e}")

            try:
                # Volume: 0.0 to 1.0
                self.engine.setProperty('volume', 1.0)
            except Exception as e:
                logger.warning(f"Could not set volume: {e}")

            # Try to select a working English voice
            if voices:
                selected = False
                # Try voices in order of preference
                for voice in voices:
                    try:
                        # Skip the broken gmw/en voice
                        if 'gmw/en' in voice.id:
                            continue
                        # Try english voices first
                        if 'english' in voice.name.lower() or 'en' in voice.id:
                            self.engine.setProperty('voice', voice.id)
                            logger.info(f"Selected voice: {voice.name} ({voice.id})")
                            selected = True
                            break
                    except Exception as e:
                        logger.debug(f"Could not set voice {voice.id}: {e}")
                        continue

                # If no english voice worked, try the first available voice
                if not selected and voices:
                    for voice in voices:
                        try:
                            if 'gmw/en' not in voice.id:  # Skip broken voice
                                self.engine.setProperty('voice', voice.id)
                                logger.info(f"Using fallback voice: {voice.name} ({voice.id})")
                                break
                        except:
                            continue

            logger.info("pyttsx3 TTS provider initialized")

        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
            raise

    def generate_speech(self, text: str, output_file: str, voice: Optional[str] = None) -> bool:
        """
        Generate speech using pyttsx3.

        Args:
            text: Text to convert to speech
            output_file: Path to save WAV file
            voice: Voice ID (optional, uses default if not specified)

        Returns:
            bool: True if successful, False otherwise
        """
        if not text or not text.strip():
            return False

        try:
            # Set voice if specified
            if voice:
                voices = self.engine.getProperty('voices')
                for v in voices:
                    if voice in v.id or voice in v.name:
                        self.engine.setProperty('voice', v.id)
                        break

            # Save to file
            self.engine.save_to_file(text, output_file)
            self.engine.runAndWait()

            logger.debug(f"pyttsx3 TTS completed: {output_file}")
            return True

        except Exception as e:
            logger.error(f"pyttsx3 TTS error: {e}")
            return False

    def get_available_voices(self) -> list:
        """Get list of available pyttsx3 voices"""
        try:
            voices = self.engine.getProperty('voices')
            return [v.name for v in voices]
        except:
            return []

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "pyttsx3"
