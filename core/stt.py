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
        if not Model:
            raise ImportError("Vosk is not installed. Run: pip install vosk")
        if not pyaudio:
            raise ImportError("PyAudio is not installed. Run: pip install pyaudio")
        
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Vosk model not found at: {model_path}")
        
        self._model = Model(str(model_path))
        self._recognizer = KaldiRecognizer(self._model, self.SAMPLE_RATE)
        self._recognizer.SetWords(True)
        
        self._audio = pyaudio.PyAudio()
        self._stream: Optional[pyaudio.Stream] = None
        
        self._listening = False
        self._audio_queue = queue.Queue()
        self._listen_thread: Optional[threading.Thread] = None
    
    def start_listening(self) -> None:
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
        while self._listening:
            try:
                if self._stream and self._stream.is_active():
                    data = self._stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                    self._audio_queue.put(data)
            except Exception:
                break
    
    def phrases(self):
        """
        Yields completed phrases from the continuous audio stream.
        This is a generator function.
        """
        if not self._listening:
            self.start_listening()
        
        while self._listening:
            try:
                data = self._audio_queue.get(timeout=0.5)
                
                if self._recognizer.AcceptWaveform(data):
                    result = json.loads(self._recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        yield text
                else:
                    # Optional: Could yield partial results here if needed
                    pass
            except queue.Empty:
                continue # Just means no audio data, which is fine
            except Exception as e:
                print(f"[STT ERROR] Error in phrase generator: {e}")
                break

    def stop_listening(self) -> None:
        self._listening = False
        if self._listen_thread:
            self._listen_thread.join(timeout=1.0)
            self._listen_thread = None
    
    def cleanup(self) -> None:
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
        self.cleanup()