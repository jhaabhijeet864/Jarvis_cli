import json
import queue
import threading
import logging
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

# Get loggers
stt_logger = logging.getLogger('stt')
error_logger = logging.getLogger('errors')

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
        stt_logger.info("Initializing SpeechToText.")
        if not Model:
            error_logger.critical("Vosk library not found. Please run: pip install vosk")
            raise ImportError("Vosk is not installed. Run: pip install vosk")
        if not pyaudio:
            error_logger.critical("PyAudio library not found. Please run: pip install pyaudio")
            raise ImportError("PyAudio is not installed. Run: pip install pyaudio")
        
        model_path = Path(model_path)
        if not model_path.exists():
            error_logger.critical(f"Vosk model not found at: {model_path}")
            raise FileNotFoundError(f"Vosk model not found at: {model_path}")
        
        stt_logger.info(f"Loading Vosk model from: {model_path}")
        self._model = Model(str(model_path))
        self._recognizer = KaldiRecognizer(self._model, self.SAMPLE_RATE)
        self._recognizer.SetWords(True)
        
        self._audio = pyaudio.PyAudio()
        self._stream: Optional[pyaudio.Stream] = None
        
        self._listening = False
        self._audio_queue = queue.Queue()
        self._listen_thread: Optional[threading.Thread] = None
        stt_logger.info("SpeechToText initialized successfully.")
    
    def start_listening(self) -> None:
        if self._listening:
            return
        
        stt_logger.info("Starting audio stream and listener thread.")
        try:
            self._stream = self._audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.SAMPLE_RATE,
                input=True,
                frames_per_buffer=self.CHUNK_SIZE
            )
        except Exception as e:
            error_logger.exception("Failed to open audio stream.")
            # Propagate exception to let the caller know something is wrong with audio input
            raise IOError("Could not open microphone stream.") from e
        
        self._listening = True
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
        stt_logger.info("Audio listener started.")
    
    def _listen_loop(self) -> None:
        while self._listening:
            try:
                if self._stream and self._stream.is_active():
                    data = self._stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                    self._audio_queue.put(data)
            except OSError as e:
                # This can happen if the microphone is disconnected
                error_logger.error(f"Audio stream read error: {e}. Stopping listener.")
                self._listening = False
            except Exception:
                error_logger.exception("Unexpected error in audio listen loop.")
                break
    
    def phrases(self):
        """
        Yields completed phrases from the continuous audio stream.
        This is a generator function.
        """
        if not self._listening:
            try:
                self.start_listening()
            except IOError:
                # If listening can't start (e.g., no mic), exit the generator
                stt_logger.error("Cannot start listening, microphone might not be available. Exiting phrase generator.")
                return

        while self._listening:
            try:
                data = self._audio_queue.get(timeout=0.5)
                
                if self._recognizer.AcceptWaveform(data):
                    result = json.loads(self._recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        stt_logger.debug(f"Recognized phrase: '{text}'")
                        yield text
                else:
                    partial_result = json.loads(self._recognizer.PartialResult())
                    if partial_result.get('partial', ''):
                        stt_logger.debug(f"Partial recognition: '{partial_result['partial']}'")

            except queue.Empty:
                continue # Just means no audio data in the last 0.5s, which is fine
            except Exception as e:
                error_logger.exception("Error in STT phrase generator loop.")
                break

    def stop_listening(self) -> None:
        if not self._listening:
            return
        
        stt_logger.info("Stopping audio listener.")
        self._listening = False
        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=1.0)
        self._listen_thread = None
        stt_logger.info("Audio listener stopped.")
    
    def cleanup(self) -> None:
        stt_logger.info("Cleaning up STT resources.")
        self.stop_listening()
        
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception as e:
                error_logger.warning(f"Error closing audio stream during cleanup: {e}", exc_info=True)
            self._stream = None
        
        if self._audio:
            try:
                self._audio.terminate()
            except Exception as e:
                error_logger.warning(f"Error terminating PyAudio during cleanup: {e}", exc_info=True)
        stt_logger.info("STT resources cleaned up.")
    
    def __del__(self):
        self.cleanup()