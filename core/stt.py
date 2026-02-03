"""
Speech-to-Text Module using Vosk for offline recognition.
Streams audio from microphone and converts to text.
"""

import json
import queue
import threading
from typing import Optional, Callable
from pathlib import Path

try:
    import pyaudio
except ImportError:
    pyaudio = None

try:
    from vosk import Model, KaldiRecognizer, SetLogLevel
    SetLogLevel(-1)  # Suppress Vosk logs
except ImportError:
    Model = None
    KaldiRecognizer = None


class SpeechToText:
    """
    Speech-to-Text engine using Vosk for offline recognition.
    
    Streams audio from the microphone and provides text transcription.
    """
    
    # Audio settings
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 4000
    FORMAT = pyaudio.paInt16 if pyaudio else None
    CHANNELS = 1
    
    def __init__(self, model_path: str):
        """
        Initialize the STT engine with a Vosk model.
        
        Args:
            model_path: Path to the Vosk model directory
        """
        if not Model:
            raise ImportError("Vosk is not installed. Run: pip install vosk")
        if not pyaudio:
            raise ImportError("PyAudio is not installed. Run: pip install pyaudio")
        
        # Validate model path
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Vosk model not found at: {model_path}\n"
                f"Download from: https://alphacephei.com/vosk/models"
            )
        
        # Initialize Vosk
        self._model = Model(str(model_path))
        self._recognizer = KaldiRecognizer(self._model, self.SAMPLE_RATE)
        self._recognizer.SetWords(True)
        
        # Audio stream
        self._audio = pyaudio.PyAudio()
        self._stream: Optional[pyaudio.Stream] = None
        
        # State
        self._listening = False
        self._audio_queue = queue.Queue()
        self._listen_thread: Optional[threading.Thread] = None
    
    def start_listening(self) -> None:
        """Start the audio stream and begin listening."""
        if self._listening:
            return
        
        self._stream = self._audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.CHUNK_SIZE
        )
        
        self._listening = True
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
    
    def _listen_loop(self) -> None:
        """Internal loop to continuously read audio."""
        while self._listening:
            try:
                if self._stream and self._stream.is_active():
                    data = self._stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                    self._audio_queue.put(data)
            except Exception:
                break
    
    def get_text(self, timeout: float = 5.0) -> Optional[str]:
        """
        Listen and return recognized text.
        
        Args:
            timeout: Maximum seconds to wait for speech
            
        Returns:
            Recognized text or None if timeout/no speech
        """
        if not self._listening:
            self.start_listening()
        
        # Clear old audio
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break
        
        # Reset recognizer for fresh recognition
        self._recognizer = KaldiRecognizer(self._model, self.SAMPLE_RATE)
        
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                data = self._audio_queue.get(timeout=0.1)
                
                if self._recognizer.AcceptWaveform(data):
                    result = json.loads(self._recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        return text
            except queue.Empty:
                continue
            except Exception:
                break
        
        # Check partial result at timeout
        partial = json.loads(self._recognizer.PartialResult())
        text = partial.get('partial', '').strip()
        return text if text else None
    
    def check_for_wake_word(self, word: str, timeout: float = 0.5) -> bool:
        """
        Check if a specific wake word was spoken.
        
        Args:
            word: The wake word to detect (e.g., "jarvis")
            timeout: How long to listen for the word
            
        Returns:
            True if wake word detected, False otherwise
        """
        text = self.get_text(timeout=timeout)
        if text:
            return word.lower() in text.lower()
        return False
    
    def listen_continuous(self, callback: Callable[[str], None], 
                          stop_event: Optional[threading.Event] = None) -> None:
        """
        Continuously listen and call callback with recognized text.
        
        Args:
            callback: Function to call with each recognized phrase
            stop_event: Optional event to signal stop
        """
        if not self._listening:
            self.start_listening()
        
        while True:
            if stop_event and stop_event.is_set():
                break
            
            try:
                data = self._audio_queue.get(timeout=0.1)
                
                if self._recognizer.AcceptWaveform(data):
                    result = json.loads(self._recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        callback(text)
            except queue.Empty:
                continue
            except Exception:
                break
    
    def stop_listening(self) -> None:
        """Stop listening but keep resources allocated."""
        self._listening = False
        if self._listen_thread:
            self._listen_thread.join(timeout=1.0)
            self._listen_thread = None
    
    def cleanup(self) -> None:
        """Release all audio resources."""
        self.stop_listening()
        
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        
        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


# Quick test when run directly
if __name__ == "__main__":
    import sys
    
    model_path = "models/vosk-model-small-en-us-0.15"
    
    print(f"Loading Vosk model from: {model_path}")
    try:
        stt = SpeechToText(model_path)
        print("Model loaded successfully!")
        print("Listening... Say something (5 second timeout)")
        
        stt.start_listening()
        text = stt.get_text(timeout=5)
        
        if text:
            print(f"You said: {text}")
        else:
            print("No speech detected")
        
        stt.cleanup()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
