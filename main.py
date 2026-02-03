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
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# =============================================================================
# Configuration
# =============================================================================

VOSK_MODEL_PATH = "models/vosk-model-small-en-us-0.15"
WAKE_WORD = "jarvis"
LISTEN_TIMEOUT = 5.0
TTS_RATE = 180
TTS_VOLUME = 1.0


# =============================================================================
# JarvisBot Class
# =============================================================================

class JarvisBot:
    """
    Main voice bot orchestrator.
    Coordinates STT, TTS, commands, and actions.
    Listens for a wake word and then a command.
    """

    def __init__(self):
        """Initialize all components."""
        print("[INIT] Initializing Jarvis...")

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
        print("[INIT] Jarvis initialized successfully!")

    def start(self):
        """Start the voice assistant's main command loop."""
        self._running = True
        self.stt.start_listening()

        print("\n[JARVIS] Online and ready!")
        self.tts.speak("Jarvis online.")
        print(f"[JARVIS] Listening for '{WAKE_WORD}' followed by a command...")
        
        try:
            self._command_loop()
        except KeyboardInterrupt:
            print("\n[JARVIS] Keyboard interrupt received.")
        finally:
            self.stop()

    def _command_loop(self):
        """Main loop: listen for wake word and then a command."""
        listening_for_command = False
        
        for phrase in self.stt.phrases():
            if not self._running:
                break

            print(f"[HEARD] '{phrase}'")

            if not listening_for_command:
                if WAKE_WORD.lower() in phrase.lower():
                    command_text = phrase.lower().replace(WAKE_WORD.lower(), "").strip()
                    
                    if command_text:
                        print(f"[JARVIS] Command heard with wake word: '{command_text}'")
                        self._process_command(command_text)
                    else:
                        print(f"[JARVIS] Activated, listening for command...")
                        self.tts.speak("Yes?")
                        listening_for_command = True
            else:
                command_text = phrase.lower()
                print(f"[JARVIS] Command heard: '{command_text}'")
                self._process_command(command_text)
                listening_for_command = False

    def _process_command(self, command_text: str):
        """Parse and execute a command."""
        if not command_text:
            return

        try:
            # Use handler's stop command check
            if self.is_stop_command(command_text):
                 print("[JARVIS] Stop command received.")
                 self.tts.speak("Goodbye, sir.")
                 self.stop()
                 return

            parsed = self.parser.parse(command_text)
            if not parsed:
                print(f"[JARVIS] Could not parse: '{command_text}'")
                self.tts.speak("I didn't understand that, sir.")
                return

            print(f"[JARVIS] Parsed: intent={parsed.intent}, target={parsed.target}, query={parsed.query}")

            kwargs = {}
            if parsed.target:
                kwargs['target'] = parsed.target
            if parsed.query:
                kwargs['query'] = parsed.query

            success, response = self.registry.dispatch_safe(parsed.intent, **kwargs)

            if success:
                print(f"[JARVIS] Response: {response}")
                self.tts.speak_async(response)
            else:
                print(f"[ERROR] Handler error: {response}")
                self.tts.speak(f"I encountered an error. {response}")

        except Exception as e:
            print(f"[ERROR] Processing error: {e}")
            self.tts.speak("I encountered an error, sir.")

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

        print("[JARVIS] Shutdown complete. Goodbye!")


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
    """Main entry point."""
    print_banner()

    # Check requirements
    print("[STARTUP] Checking requirements...")
    errors = check_requirements()

    if errors:
        print("\n[ERROR] Missing requirements:\n")
        for error in errors:
            print(f"  {error}")
        print("\nPlease fix the above issues and try again.")
        sys.exit(1)

    print("[STARTUP] All requirements OK!")

    # Create and start bot
    try:
        bot = JarvisBot()
        bot.start()
    except FileNotFoundError as e:
        print(f"\n[ERROR] File not found: {e}")
        print("Make sure the Vosk model is downloaded and extracted.")
        sys.exit(1)
    except ImportError as e:
        print(f"\n[ERROR] Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[JARVIS] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
