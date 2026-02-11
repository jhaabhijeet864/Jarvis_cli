import json
import queue
import threading
import logging
import time
from typing import Optional, Callable
from pathlib import Path

import json
import queue
import threading
import logging
import time
import io
from typing import Optional
from pathlib import Path

from config.settings import Settings
from services.whisper_stt import WhisperSpeechToText

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
    Speech-to-Text engine using Vosk for offline wake word detection and
    Whisper for local, high-accuracy command transcription.
    
    Streams audio from the microphone and provides text transcription.
    """
    
    # Audio settings
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 4000
    FORMAT = pyaudio.paInt16 if pyaudio else None
    CHANNELS = 1
    
    def __init__(self, settings: Settings, model_path: str, comm_queue: queue.Queue):
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
        
        self.settings = settings
        self.comm_queue = comm_queue

        stt_logger.info(f"Loading Vosk model from: {model_path}")
        self._model = Model(str(model_path)) # This model will be used for the wake word recognizer
        self._vosk_wake_word_recognizer = KaldiRecognizer(self._model, self.SAMPLE_RATE)
        
        self._audio = pyaudio.PyAudio()
        self._stream: Optional[pyaudio.Stream] = None
        
        self._listening = False
        self._audio_queue = queue.Queue() # Queue for raw audio chunks
        self._listen_thread: Optional[threading.Thread] = None

        self._wake_word_detected = False
        self._whisper_stt_buffer = io.BytesIO()
        self._whisper_stt_client: Optional[WhisperSpeechToText] = None

        if self.settings.get('whisper_stt'):
            stt_logger.info("Initializing Whisper Speech-to-Text client.")
            try:
                self._whisper_stt_client = WhisperSpeechToText(
                    model_size=self.settings.get('whisper_stt.model_size', 'base'),
                    device=self.settings.get('whisper_stt.device', 'cpu')
                )
            except Exception as e:
                error_logger.error(f"Failed to initialize Whisper Speech-to-Text client: {e}")
                self._whisper_stt_client = None
        else:
            stt_logger.info("Whisper Speech-to-Text is not configured.")

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
                error_logger.error(f"Audio stream read error: {e}. Stopping listener.")
                self._listening = False
            except Exception:
                error_logger.exception("Unexpected error in audio listen loop.")
                break
    
    def phrases(self):
        """
        Yields completed phrases from the continuous audio stream.
        This is a generator function that implements hybrid STT.
        """
        if not self._listening:
            try:
                self.start_listening()
            except IOError:
                stt_logger.error("Cannot start listening, microphone might not be available. Exiting phrase generator.")
                return

        wake_word = self.settings.get('wake_word.word', 'jarvis').lower()
        
        whisper_audio_chunks = []
        whisper_buffering_start_time = 0
        WHISPER_BUFFER_DURATION = 3 # seconds

        while self._listening:
            try:
                data = self._audio_queue.get(timeout=0.5)

                if self._wake_word_detected:
                    whisper_audio_chunks.append(data)
                    if (time.time() - whisper_buffering_start_time > WHISPER_BUFFER_DURATION):
                        stt_logger.debug(f"Whisper buffer duration of {WHISPER_BUFFER_DURATION}s exceeded.")
                        if self._whisper_stt_client and whisper_audio_chunks:
                            audio_content = b"".join(whisper_audio_chunks)
                            stt_logger.info("Sending buffered audio to Whisper for transcription.")
                            self.comm_queue.put({"state": "THINKING"}) # Inform GUI we are processing
                            transcript = self._whisper_stt_client.transcribe_audio(
                                audio_bytes=audio_content,
                                sample_rate=self.SAMPLE_RATE
                            )
                            if transcript:
                                stt_logger.info(f"Whisper recognized: '{transcript}'")
                                yield transcript
                        self._wake_word_detected = False
                        whisper_audio_chunks = []
                        whisper_buffering_start_time = 0
                    continue
                
                if self._vosk_wake_word_recognizer.AcceptWaveform(data):
                    vosk_result = json.loads(self._vosk_wake_word_recognizer.Result())
                    vosk_text = vosk_result.get('text', '').strip().lower()
                    
                    if vosk_text and wake_word in vosk_text:
                        stt_logger.info(f"Wake word '{wake_word}' detected by Vosk.")
                        self.comm_queue.put({"state": "LISTENING"}) # Inform GUI we are listening for a command
                        self._wake_word_detected = True
                        whisper_audio_chunks = [data]
                        whisper_buffering_start_time = time.time()
                else:
                    partial_result = json.loads(self._vosk_wake_word_recognizer.PartialResult())
                    if partial_result.get('partial', ''):
                        stt_logger.debug(f"Vosk partial: '{partial_result['partial']}'")

            except queue.Empty:
                continue
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
        
        self._model = None
        self._vosk_wake_word_recognizer = None

        if self._whisper_stt_client:
            del self._whisper_stt_client

        stt_logger.info("STT resources cleaned up.")
    
    def __del__(self):
        self.cleanup()