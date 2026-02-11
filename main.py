"""
Jarvis Voice Bot - Main Entry Point
A Jarvis-style voice assistant for Windows.

Usage:
    python main.py

Controls:
    - Say "Jarvis" to activate (wake word)
    - Press F4 for push-to-talk
    - Say "stop" or "exit" to quit
"""
import sys
import time
import threading
import queue
import logging
from pathlib import Path

# Initialize logger
from utils.logger import JarvisLogger
main_logger = logging.getLogger('main')
error_logger = logging.getLogger('errors')
stt_logger = logging.getLogger('stt')
cmd_logger = logging.getLogger('commands')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Initialize settings first
from config.settings import Settings
settings = Settings()

# Import the new Gemini Client
from services.llm_api import GeminiClient


# =============================================================================
# JarvisBot Class
# =============================================================================

class JarvisBot(threading.Thread):
    """
    The backend voice processing engine.
    Listens for a wake word, transcribes the following command using Gemini,
    gets a conversational response from Gemini, and speaks the response.
    """

    def __init__(self, comm_queue: queue.Queue):
        """Initialize all components."""
        super().__init__(daemon=True)
        main_logger.info("Initializing Jarvis Backend...")
        
        self.comm_queue = comm_queue
        self.wake_word = settings.get('wake_word.word', 'jarvis')

        # Voice I/O
        main_logger.info("Loading Speech-to-Text Engine...")
        from core.stt import SpeechToText
        self.stt = SpeechToText(
            settings=settings,
            model_path=settings.get('audio.vosk_model'),
            comm_queue=self.comm_queue
        )

        main_logger.info("Loading Text-to-Speech (pyttsx3)...")
        from core.tts import TextToSpeech
        self.tts = TextToSpeech(
            rate=settings.get('tts.rate'),
            volume=settings.get('tts.volume')
        )

        # Gemini Client for responses
        main_logger.info("Initializing Gemini Client for responses...")
        self.gemini_client = GeminiClient()

        # State
        self._running = False
        main_logger.info("Jarvis Backend initialized successfully!")

    def run(self):
        """The main command loop of the bot."""
        self._running = True
        self.stt.start_listening()
        
        # Announce startup
        self._speak("I am online and ready to assist.")
        main_logger.info(f"Listening for '{self.wake_word}' followed by a command...")
        self.comm_queue.put({"state": "IDLE"})


        for phrase in self.stt.phrases():
            if not self._running:
                break

            stt_logger.info(f"Heard: '{phrase}'")
            self.comm_queue.put({"state": "THINKING"})

            # Check for stop command locally
            if phrase.lower().strip() in ["stop", "exit", "goodbye", "shutdown"]:
                self._speak("Goodbye, sir.")
                # self.stop() is not enough, we need to break the loop in the GUI
                self.comm_queue.put({"state": "SHUTDOWN"})
                break 

            # Get conversational response from Gemini
            response = self.gemini_client.generate_response(phrase)
            self._speak(response)

    def _speak(self, text: str):
        """Send speak command to the queue and execute TTS."""
        if not text:
            # If the response is empty, just go back to idle
            self.comm_queue.put({"state": "IDLE"})
            return
            
        main_logger.info(f"Speaking: '{text}'")
        self.comm_queue.put({"state": "SPEAKING", "text": text})
        self.tts.speak(text)
        # After speaking, go back to idle and listen for wake word
        main_logger.info(f"Listening for '{self.wake_word}' followed by a command...")
        self.comm_queue.put({"state": "IDLE"})

    def stop(self):
        """Stop the voice assistant and clean up."""
        if not self._running:
            return
            
        main_logger.info("Shutting down Jarvis...")
        self._running = False
        
        # Important: Stop STT to unblock the `phrases` generator
        self.stt.stop_listening()
        main_logger.info("Speech recognition stopped.")
        
        main_logger.info("Shutdown complete.")


# =============================================================================
# Entry Point
# =============================================================================

def print_banner():
    """Print the startup banner."""
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║         ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗           ║
    ║         ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝           ║
    ║         ██║███████║██████╔╝██║   ██║██║███████╗           ║
    ║    ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║           ║
    ║    ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║           ║
    ║     ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝           ║
    ║                                                           ║
    ║              Voice Assistant for Windows                  ║
    ║                                                           ║
    ╠═══════════════════════════════════════════════════════════╣
    ║                                                           ║
    ║   Wake Word: "{settings.get('wake_word.word', 'jarvis')}"                                   ║
    ║   Say 'stop' or 'exit' to quit.                           ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)


def check_requirements():
    """Check if all required modules and files exist."""
    errors = []

    # Check Vosk model
    model_path = Path(settings.get('audio.vosk_model'))
    if not model_path.exists():
        errors.append(f"Vosk model not found at: {model_path.absolute()}")
        errors.append("  Please download a model from https://alphacephei.com/vosk/models")
        errors.append(f"  and place it at the path specified in config/settings.json ('{model_path}')")

    return errors


def main():
    """Main entry point for the GUI-based voice assistant."""
    # Check requirements first
    print_banner()
    main_logger.info("Checking requirements...")
    errors = check_requirements()
    if errors:
        error_logger.critical("Missing critical requirements:")
        for error in errors:
            error_logger.critical(f"- {error}")
        print("\nPlease fix the above issues and try again.")
        sys.exit(1)
    main_logger.info("All requirements OK!")

    # Create a queue for communication between GUI and Bot
    comm_queue = queue.Queue()

    # Start the backend bot thread
    bot = JarvisBot(comm_queue)
    bot.start()

    # Start the GUI
    from gui import Visualizer
    visualizer = Visualizer(comm_queue, settings)
    
    try:
        visualizer.run() # This will block until the GUI is closed
    except KeyboardInterrupt:
        main_logger.info("GUI interrupted by user (Ctrl+C).")
    finally:
        # After GUI closes or on interrupt, stop the bot thread
        bot.stop()
        main_logger.info("Application has been shut down.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_logger.critical("A fatal error occurred in the main application.", exc_info=True)
        sys.exit(1)