import json
from pathlib import Path
import logging

# Get loggers
main_logger = logging.getLogger('main')
error_logger = logging.getLogger('errors')

class Settings:
    """Centralized configuration management."""
    
    DEFAULT_SETTINGS = {
        'audio': {
            'vosk_model': 'models/vosk-model-en-us-0.22-lgraph',
            'sample_rate': 16000,
            'chunk_size': 4000,
        },
        'tts': {
            'rate': 180,
            'volume': 1.0,
            'voice': 'male',
        },
        'wake_word': {
            'enabled': True,
            'word': 'jarvis',
            'sensitivity': 0.5,
        },
        'hotkey': {
            'enabled': True,
            'key': 'f4',
        },
        'gui': {
            'width': 900,
            'height': 700,
            'fps': 60,
        },
        'llm': {
            'provider': 'google',  # google, openai, anthropic
            'model': 'gemini-pro',
            'temperature': 0.2,
        },
    }
    
    def __init__(self, config_file='config/settings.json'):
        self.config_file = Path(config_file)
        self.settings = self._load_settings()
        main_logger.info(f"Settings loaded from '{self.config_file}'.")

    def _load_settings(self):
        """Load settings from JSON file, falling back to defaults."""
        if self.config_file.exists():
            main_logger.info(f"Loading settings from existing file: {self.config_file}")
            try:
                with open(self.config_file, 'r') as f:
                    user_settings = json.load(f)
                # Deep merge user settings into defaults to ensure all keys are present
                settings = self.DEFAULT_SETTINGS.copy()
                for key, value in user_settings.items():
                    if isinstance(value, dict) and isinstance(settings.get(key), dict):
                        settings[key].update(value)
                    else:
                        settings[key] = value
                return settings
            except (json.JSONDecodeError, TypeError) as e:
                error_logger.error(f"Error loading '{self.config_file}': {e}. Using default settings.")
                return self.DEFAULT_SETTINGS.copy()
        else:
            main_logger.info(f"Settings file not found. Creating with default settings: {self.config_file}")
            self.save() # Save the default settings to create the file
            return self.DEFAULT_SETTINGS.copy()
    
    def save(self):
        """Save the current settings to the JSON file."""
        main_logger.info(f"Saving settings to '{self.config_file}'.")
        try:
            self.config_file.parent.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            error_logger.exception(f"Failed to save settings to '{self.config_file}'.")
    
    def get(self, key_path: str, default=None):
        """
        Get a nested setting using dot notation.
        Example: settings.get('audio.sample_rate')
        """
        keys = key_path.split('.')
        value = self.settings
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            main_logger.debug(f"Setting '{key_path}' not found, returning default value: {default}.")
            return default

    def set(self, key_path: str, value):
        """
        Set a nested setting using dot notation and save it.
        Example: settings.set('tts.rate', 200)
        """
        keys = key_path.split('.')
        d = self.settings
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value
        main_logger.info(f"Setting '{key_path}' updated to '{value}'.")
        self.save()
