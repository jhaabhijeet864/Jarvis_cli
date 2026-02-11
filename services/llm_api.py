# services/llm_api.py
"""
This module provides a client to interact with the Google Gemini API
for both speech-to-text transcription and text generation.
"""

import logging
import google.generativeai as genai
from google.generativeai.types import generation_types

# Import settings and config
from config.settings import Settings
import config

# Get loggers
llm_logger = logging.getLogger('llm')
error_logger = logging.getLogger('errors')

class GeminiClient:
    """
    A client for the Google Generative AI API (Gemini) that handles both
    audio transcription and text generation.
    """

    def __init__(self):
        """
        Initializes the GeminiClient using settings from the configuration system.
        """
        self.settings = Settings()
        
        api_key = config.GOOGLE_API_KEY
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            error_logger.error("Google API key is not configured in config.py.")
            # Don't raise an exception here, but log it. The methods will fail gracefully.
            self.model = None
            return
        
        # Use a model that supports both audio and text, like gemini-1.5-flash
        self.model_name = "gemini-1.5-flash" 
        self.temperature = self.settings.get('llm.temperature', 0.7) # Use a more creative temp for chat
        
        llm_logger.info(f"Initializing GeminiClient with model='{self.model_name}', temperature={self.temperature}")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
            llm_logger.info(f"GeminiClient initialized successfully with {self.model_name}.")
        except Exception as e:
            error_logger.exception(f"Error initializing Google Generative AI: {e}")
            self.model = None

    def transcribe_audio(self, audio_bytes: bytes, sample_rate: int) -> str:
        """
        Transcribes audio data using the Gemini API.

        Args:
            audio_bytes: The audio data in bytes.
            sample_rate: The sample rate of the audio (not directly used by Gemini API call,
                         but good practice to have).

        Returns:
            The transcribed text, or an empty string if transcription fails.
        """
        if not self.model:
            error_logger.error("Gemini model not initialized. Cannot transcribe.")
            return ""
        
        llm_logger.info(f"Sending {len(audio_bytes)} bytes of audio for transcription...")
        
        try:
            # The gemini-1.5-flash model can take audio data directly.
            # We provide a simple prompt to guide it towards transcription.
            response = self.model.generate_content(
                ["Transcribe the following audio:", {"mime_type": "audio/wav", "data": audio_bytes}]
            )
            
            transcript = response.text.strip()
            llm_logger.info(f"Gemini transcription successful: '{transcript}'")
            return transcript
            
        except Exception as e:
            error_logger.exception(f"An unexpected error occurred during Gemini transcription: {e}")
            return ""

    def generate_response(self, user_prompt: str) -> str:
        """
        Generates a conversational response based on a user's prompt.

        Args:
            user_prompt: The natural language prompt from the user.

        Returns:
            A string containing the generated response, or an error message.
        """
        if not self.model:
            error_logger.error("Gemini model not initialized. Cannot generate response.")
            return "Sorry, my connection to the AI is not configured."

        if not user_prompt:
            return "I didn't catch that. Could you please repeat?"

        llm_logger.info(f"Sending prompt to {self.model_name} for conversational response: '{user_prompt[:80]}...'")
        
        try:
            generation_config = genai.types.GenerationConfig(
                candidate_count=1,
                temperature=self.temperature
            )
            
            response = self.model.generate_content(
                user_prompt,
                generation_config=generation_config
            )
            
            if not response.parts:
                finish_reason = response.prompt_feedback.block_reason.name if response.prompt_feedback else "Unknown"
                error_message = f"My apologies, I could not generate a response. The request may have been blocked for safety reasons: {finish_reason}"
                llm_logger.warning(f"API call failed or was blocked: {error_message}")
                return error_message

            return response.text.strip()

        except Exception as e:
            error_logger.exception(f"An unexpected error occurred during API call: {e}")
            return "I'm sorry, I seem to be having trouble connecting to my AI core."