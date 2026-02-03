"""
Text-to-Speech Module using pyttsx3 with Windows SAPI5
Provides synchronous and asynchronous speech capabilities.
"""

import pyttsx3
import threading
from typing import Optional


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
        self._engine = pyttsx3.init('sapi5')
        self._rate = rate
        self._volume = volume
        self._speaking = False
        self._async_thread: Optional[threading.Thread] = None
        
        # Configure engine
        self._engine.setProperty('rate', self._rate)
        self._engine.setProperty('volume', self._volume)
        
        # Get available voices and set a good default
        voices = self._engine.getProperty('voices')
        if voices:
            # Prefer a male voice for Jarvis-style
            for voice in voices:
                if 'david' in voice.name.lower() or 'male' in voice.name.lower():
                    self._engine.setProperty('voice', voice.id)
                    break
    
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
        
        self._speaking = True
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        finally:
            self._speaking = False
    
    def speak_async(self, text: str) -> threading.Thread:
        """
        Speak text asynchronously (non-blocking).
        
        Args:
            text: The text to speak
            
        Returns:
            The thread handling the speech
        """
        if not text:
            return None
        
        def _speak_thread():
            self.speak(text)
        
        self._async_thread = threading.Thread(target=_speak_thread, daemon=True)
        self._async_thread.start()
        return self._async_thread
    
    def stop(self) -> None:
        """Stop any ongoing speech."""
        try:
            self._engine.stop()
        except Exception:
            pass
        self._speaking = False
    
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self._speaking
    
    def list_voices(self) -> list:
        """List all available voices."""
        voices = self._engine.getProperty('voices')
        return [(v.id, v.name) for v in voices]
    
    def set_voice(self, voice_id: str) -> bool:
        """
        Set voice by ID.
        
        Args:
            voice_id: The voice ID to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._engine.setProperty('voice', voice_id)
            return True
        except Exception:
            return False


# Quick test when run directly
if __name__ == "__main__":
    tts = TextToSpeech()
    print("Available voices:")
    for vid, name in tts.list_voices():
        print(f"  - {name}")
    print()
    tts.speak("Hello sir, Text to Speech systems are online and operational.")
