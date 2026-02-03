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
    Coordinates STT, TTS, commands, and actions from all three streams.
    """

    def __init__(self):
        """Initialize all components from the three streams."""
        print("[INIT] Initializing Jarvis...")

        # Stream 1: Voice I/O
        print("[INIT] Loading Speech-to-Text (Vosk)...")
        from core.stt import SpeechToText
        self.stt = SpeechToText(VOSK_MODEL_PATH)

        print("[INIT] Loading Text-to-Speech (pyttsx3)...")
        from core.tts import TextToSpeech
        self.tts = TextToSpeech(rate=TTS_RATE, volume=TTS_VOLUME)

        print("[INIT] Setting up hotkey listener (F4)...")
        from core.hotkey import HotkeyListener
        self.hotkey = HotkeyListener()

        # Stream 2: Actions
        print("[INIT] Initializing App Launcher...")
        from actions.apps import AppLauncher
        self.app_launcher = AppLauncher()

        print("[INIT] Initializing Browser Controller...")
        from actions.browser import BrowserController
        self.browser = BrowserController()

        # Stream 3: Commands
        print("[INIT] Initializing Command Handlers...")
        from commands.parser import CommandParser
        from commands.handlers import init_handlers, registry, is_stop_command

        self.parser = CommandParser()
        self.registry = registry
        self.is_stop_command = is_stop_command

        # Connect handlers to action controllers
        init_handlers(
            app_launcher=self.app_launcher,
            browser=self.browser,
            responses=None  # Uses built-in fallback responses
        )

        # State
        self._running = False
        self._processing = False
        self._lock = threading.Lock()

        print("[INIT] Jarvis initialized successfully!")

    def start(self):
        """Start the voice assistant."""
        self._running = True

        # Set up hotkey callback
        self.hotkey.on_hotkey = self._on_hotkey_pressed
        self.hotkey.start()

        # Start speech recognition
        self.stt.start_listening()

        # Announce startup
        print("\n[JARVIS] Online and ready!")
        self.tts.speak("Jarvis online, sir. Ready for your commands.")

        # Main loop - listen for wake word
        print(f"[JARVIS] Listening for wake word '{WAKE_WORD}' or F4 hotkey...")
        self._main_loop()

    def _main_loop(self):
        """Main loop: listen for wake word or hotkey activation."""
        while self._running:
            try:
                # Check for wake word (non-blocking with short timeout)
                if self.stt.check_for_wake_word(WAKE_WORD, timeout=0.3):
                    self._process_activation()

                # Small sleep to prevent CPU spinning
                time.sleep(0.1)

            except KeyboardInterrupt:
                print("\n[JARVIS] Keyboard interrupt received")
                self.stop()
                break
            except Exception as e:
                print(f"[ERROR] Main loop error: {e}")
                time.sleep(0.5)

    def _on_hotkey_pressed(self):
        """Callback when F4 hotkey is pressed."""
        print("\n[HOTKEY] F4 pressed!")
        self._process_activation()

    def _process_activation(self):
        """Handle activation (wake word detected or hotkey pressed)."""
        # Prevent concurrent processing
        with self._lock:
            if self._processing:
                return
            self._processing = True

        try:
            # Acknowledge activation
            print("[JARVIS] Activated - listening for command...")
            self.tts.speak("Yes sir?")

            # Listen for command
            print(f"[JARVIS] Listening for {LISTEN_TIMEOUT} seconds...")
            command_text = self.stt.get_text(timeout=LISTEN_TIMEOUT)

            if not command_text:
                print("[JARVIS] No command heard (timeout)")
                self.tts.speak("I didn't hear a command, sir.")
                return

            print(f"[JARVIS] Heard: '{command_text}'")

            # Parse command
            parsed = self.parser.parse(command_text)

            if not parsed:
                print(f"[JARVIS] Could not parse: '{command_text}'")
                self.tts.speak("I didn't understand that, sir.")
                return

            print(f"[JARVIS] Parsed: intent={parsed.intent}, target={parsed.target}, query={parsed.query}")

            # Build kwargs for dispatch
            kwargs = {}
            if parsed.target:
                kwargs['target'] = parsed.target
            if parsed.query:
                kwargs['query'] = parsed.query

            # Dispatch to handler
            success, response = self.registry.dispatch_safe(parsed.intent, **kwargs)

            if success:
                print(f"[JARVIS] Response: {response}")
                self.tts.speak(response)

                # Check for stop command
                if self.is_stop_command(response):
                    self.stop()
            else:
                print(f"[ERROR] Handler error: {response}")
                self.tts.speak(f"I encountered an error, sir. {response}")

        except Exception as e:
            print(f"[ERROR] Processing error: {e}")
            self.tts.speak("I encountered an error, sir.")

        finally:
            self._processing = False

    def stop(self):
        """Stop the voice assistant and clean up."""
        print("\n[JARVIS] Shutting down...")
        self._running = False

        # Stop hotkey listener
        try:
            self.hotkey.stop()
            print("[CLEANUP] Hotkey listener stopped")
        except Exception as e:
            print(f"[CLEANUP] Hotkey stop error: {e}")

        # Stop speech recognition
        try:
            self.stt.cleanup()
            print("[CLEANUP] Speech recognition stopped")
        except Exception as e:
            print(f"[CLEANUP] STT cleanup error: {e}")

        # Close browser if open
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
    ║   Wake Word: "Jarvis"     |     Hotkey: F4                ║
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
