import pyttsx3
import threading
import logging
from typing import Optional

# Get loggers
main_logger = logging.getLogger('main')
error_logger = logging.getLogger('errors')

class TextToSpeech:
    """
    Text-to-Speech engine wrapper using Windows SAPI5.
    
    Attributes:
        rate (int): Speech rate in words per minute (default: 180)
        volume (float): Volume level 0.0 to 1.0 (default: 1.0)
    """
    
    def __init__(self, rate: int = 180, volume: float = 1.0):
        """
        Initialize the TTS engine with configurable rate and volume.
        
        Args:
            rate: Speech rate in WPM (default: 180)
            volume: Volume level 0.0-1.0 (default: 1.0)
        """
        main_logger.info("Initializing TextToSpeech.")
        try:
            self._engine = pyttsx3.init('sapi5')
        except Exception as e:
            error_logger.critical("Failed to initialize pyttsx3 engine. SAPI5 might be missing or broken.", exc_info=True)
            raise RuntimeError("Could not initialize TTS engine.") from e

        self._rate = rate
        self._volume = volume
        self._speaking = False
        self._async_thread: Optional[threading.Thread] = None
        
        # Configure engine
        self._engine.setProperty('rate', self._rate)
        self._engine.setProperty('volume', self._volume)
        
        # Get available voices and set a good default
        try:
            voices = self._engine.getProperty('voices')
            if voices:
                # Prefer a male voice for Jarvis-style
                chosen_voice = None
                for voice in voices:
                    if 'david' in voice.name.lower() or 'zira' in voice.name.lower():
                        chosen_voice = voice.id
                        break
                if chosen_voice:
                    self._engine.setProperty('voice', chosen_voice)
                    main_logger.info(f"Set TTS voice to: {chosen_voice}")
                else:
                    main_logger.warning("Could not find a preferred male voice (David/Zira). Using default.")
            else:
                main_logger.warning("No TTS voices found for SAPI5 engine.")
        except Exception as e:
            error_logger.error("Error while setting TTS voice.", exc_info=True)

        main_logger.info("TextToSpeech initialized successfully.")
    
    @property
    def rate(self) -> int:
        """Get current speech rate."""
        return self._rate
    
    @rate.setter
    def rate(self, value: int):
        """Set speech rate in WPM."""
        self._rate = value
        self._engine.setProperty('rate', value)
    
    @property
    def volume(self) -> float:
        """Get current volume level."""
        return self._volume
    
    @volume.setter
    def volume(self, value: float):
        """Set volume level (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, value))
        self._engine.setProperty('volume', self._volume)
    
    def speak(self, text: str) -> None:
        """
        Speak text synchronously (blocks until complete).
        
        Args:
            text: The text to speak
        """
        if not text:
            return
        
        main_logger.debug(f"Speaking (sync): '{text}'")
        self._speaking = True
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            error_logger.exception("Error during synchronous speech.")
        finally:
            self._speaking = False
    
    def speak_async(self, text: str) -> Optional[threading.Thread]:
        """
        Speak text asynchronously (non-blocking).
        
        Args:
            text: The text to speak
            
        Returns:
            The thread handling the speech, or None if text is empty.
        """
        if not text:
            return None
        
        def _speak_thread():
            self.speak(text)
        
        main_logger.debug(f"Speaking (async): '{text}'")
        self._async_thread = threading.Thread(target=_speak_thread, daemon=True)
        self._async_thread.start()
        return self._async_thread
    
    def stop(self) -> None:
        """Stop any ongoing speech."""
        main_logger.debug("Stopping any ongoing speech.")
        try:
            self._engine.stop()
        except Exception as e:
            error_logger.warning("Exception while stopping TTS engine.", exc_info=True)
        self._speaking = False
    
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self._speaking
    
    def list_voices(self) -> list:
        """List all available voices."""
        try:
            voices = self._engine.getProperty('voices')
            return [(v.id, v.name) for v in voices]
        except Exception as e:
            error_logger.error("Could not list TTS voices.", exc_info=True)
            return []
    
    def set_voice(self, voice_id: str) -> bool:
        """
        Set voice by ID.
        
        Args:
            voice_id: The voice ID to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            main_logger.info(f"Setting TTS voice to: {voice_id}")
            self._engine.setProperty('voice', voice_id)
            return True
        except Exception as e:
            error_logger.error(f"Failed to set TTS voice ID: {voice_id}", exc_info=True)
            return False
