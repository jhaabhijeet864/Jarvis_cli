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
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# =============================================================================
# Configuration
# =============================================================================

VOSK_MODEL_PATH = "models/vosk-model-en-us-0.22-lgraph"
WAKE_WORD = "jarvis"
LISTEN_TIMEOUT = 5.0
TTS_RATE = 180
TTS_VOLUME = 1.0


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
        print("[INIT] Initializing Jarvis Backend...")
        
        self.comm_queue = comm_queue

        # Voice I/O
        print("[INIT] Loading Speech-to-Text (Vosk)...")
        from core.stt import SpeechToText
        self.stt = SpeechToText(VOSK_MODEL_PATH)

        print("[INIT] Loading Text-to-Speech (pyttsx3)...")
        from core.tts import TextToSpeech
        self.tts = TextToSpeech(rate=TTS_RATE, volume=TTS_VOLUME)

        # Actions
        print("[INIT] Initializing App Launcher...")
        from actions.apps import AppLauncher
        self.app_launcher = AppLauncher()

        print("[INIT] Initializing Browser Controller...")
        from actions.browser import BrowserController
        self.browser = BrowserController()

        # Commands
        print("[INIT] Initializing Command Handlers...")
        from commands.parser import CommandParser
        from commands.handlers import init_handlers, registry, is_stop_command

        self.parser = CommandParser()
        self.registry = registry
        self.is_stop_command = is_stop_command

        init_handlers(
            app_launcher=self.app_launcher,
            browser=self.browser,
            responses=None
        )

        # State
        self._running = False
        print("[INIT] Jarvis Backend initialized successfully!")

    def run(self):
        """The main command loop of the bot."""
        self._running = True
        self.stt.start_listening()
        
        # Announce startup via queue
        self._speak("Jarvis online.")
        print(f"[JARVIS] Listening for '{WAKE_WORD}' followed by a command...")

        listening_for_command = False
        
        for phrase in self.stt.phrases():
            if not self._running:
                break

            print(f"[HEARD] '{phrase}'")

            if not listening_for_command:
                if WAKE_WORD.lower() in phrase.lower():
                    command_text = phrase.lower().replace(WAKE_WORD.lower(), "").strip()
                    
                    if command_text:
                        self._process_command(command_text)
                    else:
                        self.comm_queue.put({"state": "LISTENING"})
                        self._speak("Yes?")
                        listening_for_command = True
            else:
                self._process_command(phrase.lower())
                listening_for_command = False
                # Go back to idle state after processing
                self.comm_queue.put({"state": "IDLE"})

    def _speak(self, text: str):
        """Send speak command to the queue and execute TTS."""
        if not text:
            return
        self.comm_queue.put({"state": "SPEAKING", "text": text})
        self.tts.speak(text) # Still run TTS from the backend thread

    def _process_command(self, command_text: str):
        """Parse and execute a command."""
        if not command_text:
            self.comm_queue.put({"state": "IDLE"})
            return

        try:
            if self.is_stop_command(command_text):
                 self._speak("Goodbye, sir.")
                 self.stop()
                 return

            parsed = self.parser.parse(command_text)
            if not parsed:
                self._speak("I didn't understand that, sir.")
                return

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
                    self._speak(response)
            elif success:
                # For all other successful commands, just speak the response
                self._speak(response)
            else:
                # For all other failed commands, speak the error
                self._speak(f"I encountered an error. {response}")

        except Exception as e:
            print(f"[ERROR] Processing error: {e}")
            self._speak("I encountered an error, sir.")

    def stop(self):
        """Stop the voice assistant and clean up."""
        if not self._running:
            return
            
        print("\n[JARVIS] Shutting down...")
        self._running = False
        
        self.stt.stop_listening()
        print("[CLEANUP] Speech recognition stopped.")
        
        try:
            self.browser.close()
            print("[CLEANUP] Browser closed")
        except Exception as e:
            print(f"[CLEANUP] Browser close error: {e}")

        print("[JARVIS] Shutdown complete.")


# =============================================================================
# Entry Point
# =============================================================================

def print_banner():
    """Print the startup banner."""
    print("""
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
    ║   Wake Word: "Jarvis"                                   ║
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
    model_path = Path(VOSK_MODEL_PATH)
    if not model_path.exists():
        errors.append(f"Vosk model not found at: {model_path.absolute()}")
        errors.append("  Download from: https://alphacephei.com/vosk/models")
        errors.append("  Get: vosk-model-small-en-us-0.15 (~40MB)")

    # Check core modules
    try:
        from core.stt import SpeechToText
    except ImportError as e:
        errors.append(f"Stream 1 (core/stt.py) import error: {e}")

    try:
        from core.tts import TextToSpeech
    except ImportError as e:
        errors.append(f"Stream 1 (core/tts.py) import error: {e}")

    try:
        from core.hotkey import HotkeyListener
    except ImportError as e:
        errors.append(f"Stream 1 (core/hotkey.py) import error: {e}")

    # Check action modules
    try:
        from actions.apps import AppLauncher
    except ImportError as e:
        errors.append(f"Stream 2 (actions/apps.py) import error: {e}")

    try:
        from actions.browser import BrowserController
    except ImportError as e:
        errors.append(f"Stream 2 (actions/browser.py) import error: {e}")

    # Check command modules
    try:
        from commands.parser import CommandParser
    except ImportError as e:
        errors.append(f"Stream 3 (commands/parser.py) import error: {e}")

    try:
        from commands.handlers import registry
    except ImportError as e:
        errors.append(f"Stream 3 (commands/handlers.py) import error: {e}")

    return errors


def main():
    """Main entry point for the GUI-based voice assistant."""
    # Check requirements first
    print_banner()
    print("[STARTUP] Checking requirements...")
    errors = check_requirements()
    if errors:
        print("\n[ERROR] Missing requirements:\n")
        for error in errors:
            print(f"  {error}")
        print("\nPlease fix the above issues and try again.")
        print("You may need to run: pip install -r requirements.txt")
        sys.exit(1)
    print("[STARTUP] All requirements OK!")

    # Create a queue for communication between GUI and Bot
    comm_queue = queue.Queue()

    # Start the backend bot thread
    bot = JarvisBot(comm_queue)
    bot.start()

    # Start the GUI
    from gui import Visualizer
    visualizer = Visualizer(comm_queue)
    visualizer.run() # This will block until the GUI is closed

    # After GUI closes, stop the bot thread
    bot.stop()


if __name__ == "__main__":
    main()
