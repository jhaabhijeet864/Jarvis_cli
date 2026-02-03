# services/llm_api.py
"""
This module provides an interface to a Large Language Model (LLM)
for code generation, using the Google Generative AI API.
"""

import google.generativeai as genai
from google.generativeai.types import generation_types

class CodeGenerator:
    """
    A robust client for the Google Generative AI API to generate code.
    """

    def __init__(self, api_key: str):
        """
        Initializes the CodeGenerator.

        Args:
            api_key: The Google AI API key.
        
        Raises:
            ValueError: If the API key is missing or invalid.
        """
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Google API key is not configured. Please set it in config.py.")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            print("[LLM] CodeGenerator initialized successfully with Gemini-Pro.")
        except Exception as e:
            print(f"[LLM] Error initializing Google Generative AI: {e}")
            raise ValueError("Failed to configure Google Generative AI. Check API key and network.")

    def generate_code(self, user_prompt: str) -> str:
        """
        Generates code based on a user's prompt.

        Args:
            user_prompt: The natural language prompt from the user.

        Returns:
            A string containing the generated code, or an error message.
        """
        if not user_prompt:
            return "Error: No prompt provided for code generation."

        # Construct a more robust prompt for the LLM
        full_prompt = (
            "You are an expert programmer. Your task is to generate a clean, "
            "efficient, and well-documented code snippet based on the user's request. "
            "Only return the code, without any extra explanations or pleasantries.\n\n"
            f"User Request: \"{user_prompt}\""
        )
        
        print(f"[LLM] Sending prompt to Gemini-Pro: '{user_prompt}'")
        
        try:
            # Set generation config for safety and predictability
            generation_config = genai.types.GenerationConfig(
                candidate_count=1,
                temperature=0.2 # Lower temperature for more predictable code
            )
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # Check for safety blocks or empty responses
            if not response.parts:
                finish_reason = response.prompt_feedback.block_reason.name if response.prompt_feedback else "Unknown"
                error_message = f"I couldn't generate code for that. The request may have been blocked for safety reasons: {finish_reason}"
                print(f"[LLM] API call failed or was blocked: {error_message}")
                return error_message

            generated_code = response.text

            # Clean up the response to only include the code block
            # Models often wrap the code in ```python ... ```
            if '```' in generated_code:
                parts = generated_code.split('```')
                if len(parts) > 1:
                    # Take the content of the first code block
                    generated_code = parts[1]
                    # The first line might be the language name, so we can optionally strip it
                    if generated_code.lower().lstrip().startswith(('python', 'javascript', 'html', 'css')):
                        lines = generated_code.split('\n')
                        generated_code = '\n'.join(lines[1:])

            return generated_code.strip()

        except generation_types.StopCandidateException as e:
            print(f"[LLM] API call was stopped: {e}")
            return f"I couldn't generate code for that. The request may have been blocked for safety reasons: {e}"
        except Exception as e:
            print(f"[LLM] An unexpected error occurred during API call: {e}")
            return "Sorry, I encountered an error while trying to generate code."
