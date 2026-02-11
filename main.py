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


# =============================================================================
# JarvisBot Class
# =============================================================================

class JarvisBot(threading.Thread):
    """
    The backend voice processing engine.
    Runs in a separate thread and communicates with the GUI via a queue.
    """

    def __init__(self, comm_queue: queue.Queue):
        """Initialize all components."""
        super().__init__(daemon=True)
        main_logger.info("Initializing Jarvis Backend...")
        
        self.comm_queue = comm_queue
        self.wake_word = settings.get('wake_word.word', 'jarvis')

        # Voice I/O
        main_logger.info("Loading Speech-to-Text (Vosk)...")
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

        # Actions
        main_logger.info("Initializing App Launcher...")
        from actions.apps import AppLauncher
        self.app_launcher = AppLauncher()

        main_logger.info("Initializing Browser Controller...")
        from actions.browser import BrowserController
        self.browser = BrowserController()

        # Commands
        main_logger.info("Initializing Command Handlers...")
        from commands.parser import CommandParser
        from commands.handlers import init_handlers, registry, is_stop_command
        from utils.responses import JarvisResponses

        self.parser = CommandParser()
        self.registry = registry
        self.is_stop_command = is_stop_command
        self.responses = JarvisResponses()

        init_handlers(
            app_launcher=self.app_launcher,
            browser=self.browser,
            responses=self.responses
        )

        # State
        self._running = False
        main_logger.info("Jarvis Backend initialized successfully!")

    def run(self):
        """The main command loop of the bot."""
        self._running = True
        self.stt.start_listening()
        
        # Announce startup via queue
        self._speak(self.responses.get('greeting'))
        main_logger.info(f"Listening for '{self.wake_word}' followed by a command...")

        for phrase in self.stt.phrases():
            if not self._running:
                break

            stt_logger.info(f"Heard: '{phrase}'")

            # The STT engine now only yields transcribed commands after wake word
            # and buffering. So, we can directly process the phrase as a command.
            self.comm_queue.put({"state": "THINKING"})
            self._process_command(phrase.lower())

    def _speak(self, text: str):
        """Send speak command to the queue and execute TTS."""
        if not text:
            return
        main_logger.info(f"Speaking: '{text}'")
        self.comm_queue.put({"state": "SPEAKING", "text": text})
        self.tts.speak(text) # Still run TTS from the backend thread
        # After speaking, it's good practice to ensure the state returns to IDLE
        # if no other action is pending.
        self.comm_queue.put({"state": "IDLE"})

    def _process_command(self, command_text: str):
        """Parse and execute a command."""
        if not command_text:
            self.comm_queue.put({"state": "IDLE"})
            return

        cmd_logger.info(f"Processing command: '{command_text}'")
        try:
            if self.is_stop_command(command_text):
                 self._speak(self.responses.get('goodbye', goodbye="Goodbye, sir."))
                 self.stop()
                 return

            parsed = self.parser.parse(command_text)
            if not parsed:
                cmd_logger.warning(f"Could not parse command: '{command_text}'")
                self._speak(self.responses.get('not_understood'))
                return

            cmd_logger.info(f"Parsed command: Intent='{parsed.intent}', Target='{parsed.target}', Query='{parsed.query}'")
            kwargs = {}
            if parsed.target:
                kwargs['target'] = parsed.target
            if parsed.query:
                kwargs['query'] = parsed.query

            # Dispatch to the appropriate handler
            success, response = self.registry.dispatch_safe(parsed.intent, **kwargs)

            # Handle the response based on the intent
            if parsed.intent == "generate_code":
                if success:
                    self._speak("Here is the code I generated for you.")
                    # Send the code to the GUI for display
                    self.comm_queue.put({"state": "DISPLAY_CODE", "code": response})
                else:
                    # If code generation failed, the response is an error message to speak
                    error_logger.error(f"Code generation failed: {response}")
                    self._speak(response)
            elif success:
                # For all other successful commands, just speak the response
                self._speak(response)
            else:
                # For all other failed commands, speak the error
                error_logger.error(f"Command '{parsed.intent}' failed: {response}")
                self._speak(self.responses.get('error', error=response))

        except Exception as e:
            error_logger.exception(f"An unexpected error occurred while processing command: '{command_text}'")
            self._speak(self.responses.get('error', error="An internal error occurred."))

    def stop(self):
        """Stop the voice assistant and clean up."""
        if not self._running:
            return
            
        main_logger.info("Shutting down Jarvis...")
        self._running = False
        
        self.stt.stop_listening()
        main_logger.info("Speech recognition stopped.")
        
        try:
            self.browser.close()
            main_logger.info("Browser closed.")
        except Exception as e:
            error_logger.warning(f"Error closing browser during shutdown: {e}")

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
    ║                                                           ║
    ║   Commands:                                               ║
    ║     • "Open Notepad"      - Open applications             ║
    ║     • "Open YouTube"      - Open websites                 ║
    ║     • "Search for X"      - Search Google/YouTube         ║
    ║     • "Play X on YouTube" - Search and play               ║
    ║     • "Pause" / "Play"    - Media control                 ║
    ║     • "What time is it?"  - Get current time              ║
    ║     • "Stop" / "Exit"     - Shutdown Jarvis               ║
    ║                                                           ║
    ║   Press Ctrl+C to force quit                              ║
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

    # Check core modules
    try:
        from core.stt import SpeechToText
    except ImportError as e:
        errors.append(f"Core module import error: {e}")

    # Check action modules
    try:
        from actions.apps import AppLauncher
    except ImportError as e:
        errors.append(f"Actions module import error: {e}")

    # Check command modules
    try:
        from commands.parser import CommandParser
    except ImportError as e:
        errors.append(f"Commands module import error: {e}")

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
        print("You may need to run: pip install -r requirements.txt")
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
