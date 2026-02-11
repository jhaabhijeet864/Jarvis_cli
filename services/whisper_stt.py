import whisper
import torch
import logging
import numpy as np
import io
import wave

# Set up logging
stt_logger = logging.getLogger('stt')
error_logger = logging.getLogger('errors')

class WhisperSpeechToText:
    """
    Handles transcription using a local Whisper model.
    """

    def __init__(self, settings, model_size: str = "base", device: str = "cpu"):
        self.settings = settings
        self.model_size = model_size
        self.device = device
        self.model = self._load_model()
        stt_logger.info(f"WhisperSpeechToText initialized with model '{model_size}' on device '{device}'.")
        
        # Verify CUDA availability
        if self.device == 'cuda':
            if torch.cuda.is_available():
                stt_logger.info("CUDA is available. Whisper will run on the GPU.")
            else:
                stt_logger.warning("CUDA is not available. Whisper will fall back to CPU.")
                self.device = 'cpu'
                self.model.to('cpu')

    def _load_model(self):
        """
        Loads the Whisper model.
        """
        try:
            stt_logger.info(f"Loading Whisper model '{self.model_size}'. This may take a while on the first run as the model is downloaded...")
            model = whisper.load_model(self.model_size, device=self.device)
            stt_logger.info("Whisper model loaded successfully.")
            return model
        except Exception as e:
            error_logger.critical(f"Failed to load Whisper model '{self.model_size}': {e}")
            # If a specific model fails, try to fall back to a smaller one, e.g., 'tiny'
            if self.model_size != 'tiny':
                stt_logger.warning("Falling back to 'tiny' model.")
                try:
                    return whisper.load_model('tiny', device=self.device)
                except Exception as fallback_e:
                    error_logger.critical(f"Failed to load fallback 'tiny' model: {fallback_e}")
                    raise
            raise

    def transcribe_audio(self, audio_bytes: bytes, sample_rate: int) -> str:
        """
        Transcribes audio data using the local Whisper model.

        Args:
            audio_bytes: The audio data in bytes.
            sample_rate: The sample rate of the audio.

        Returns:
            The transcribed text, or an empty string if transcription fails.
        """
        if not self.model:
            error_logger.error("Whisper model not loaded. Cannot transcribe.")
            return ""

        try:
            # --- Debugging: Save the audio buffer to a file ---
            if self.settings.get('stt.debug_save_audio', False):
                stt_logger.info(f"Received {len(audio_bytes)} bytes for transcription.")
                stt_logger.info("Saving audio buffer to debug_audio.wav")
                with wave.open("debug_audio.wav", "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_bytes)
                stt_logger.info("Debug audio file saved.")
            # --- End Debugging ---

            # Whisper expects a NumPy array of 16-bit signed integers for the audio.
            # The audio_bytes are raw bytes, so we need to convert them.
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            # Transcribe the audio
            stt_logger.debug(f"Transcribing audio with Whisper model '{self.model_size}'.")
            result = self.model.transcribe(audio_np, fp16=False)
            
            transcript = result.get('text', '').strip()
            stt_logger.debug(f"Whisper transcription: '{transcript}'")
            return transcript
        except Exception as e:
            error_logger.exception(f"Error during Whisper transcription: {e}")
            return ""

    def __del__(self):
        # Whisper models are large, so we should free up memory when the object is destroyed.
        if hasattr(self, 'model') and self.model:
            del self.model
            if self.device == 'cuda':
                torch.cuda.empty_cache()
            stt_logger.info("Whisper model resources cleaned up.")

