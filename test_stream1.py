"""
Stream 1 Test: Voice I/O Layer
Tests TTS, STT, and Hotkey modules independently.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from colorama import init, Fore, Style
init()  # Initialize colorama for Windows

def print_header(text: str):
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f" {text}")
    print(f"{'='*50}{Style.RESET_ALL}\n")

def print_success(text: str):
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_error(text: str):
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def print_info(text: str):
    print(f"{Fore.YELLOW}→ {text}{Style.RESET_ALL}")


def test_tts():
    """Test Text-to-Speech module."""
    print_header("TEST 1: Text-to-Speech (TTS)")
    
    try:
        from core.tts import TextToSpeech
        
        print_info("Initializing TTS engine...")
        tts = TextToSpeech(rate=180, volume=1.0)
        print_success("TTS engine initialized")
        
        # List voices
        print_info("Available voices:")
        for vid, name in tts.list_voices():
            print(f"   - {name}")
        
        # Test sync speech
        print_info("Testing synchronous speech...")
        tts.speak("Hello sir, Text to Speech systems are online and operational.")
        print_success("Synchronous speech complete")
        
        # Test async speech
        print_info("Testing asynchronous speech...")
        thread = tts.speak_async("This is an asynchronous test.")
        print_info("Speech running in background...")
        if thread:
            thread.join()
        print_success("Asynchronous speech complete")
        
        return True
        
    except Exception as e:
        print_error(f"TTS test failed: {e}")
        return False


def test_stt():
    """Test Speech-to-Text module."""
    print_header("TEST 2: Speech-to-Text (STT)")
    
    model_path = "models/vosk-model-small-en-us-0.15"
    
    try:
        from core.stt import SpeechToText
        
        # Check if model exists
        if not Path(model_path).exists():
            print_error(f"Vosk model not found at: {model_path}")
            print_info("Download the model from: https://alphacephei.com/vosk/models")
            print_info("Extract to: models/vosk-model-small-en-us-0.15/")
            return False
        
        print_info(f"Loading Vosk model from: {model_path}")
        stt = SpeechToText(model_path)
        print_success("Vosk model loaded")
        
        print_info("Starting audio stream...")
        stt.start_listening()
        print_success("Audio stream started")
        
        print_info("Say something (5 second timeout)...")
        print(f"{Fore.MAGENTA}   Listening...{Style.RESET_ALL}")
        
        text = stt.get_text(timeout=5)
        
        if text:
            print_success(f"Recognized: \"{text}\"")
        else:
            print_info("No speech detected (this is okay for automated tests)")
        
        print_info("Cleaning up...")
        stt.cleanup()
        print_success("STT cleanup complete")
        
        return True
        
    except FileNotFoundError as e:
        print_error(f"Model not found: {e}")
        return False
    except Exception as e:
        print_error(f"STT test failed: {e}")
        return False


def test_hotkey():
    """Test Hotkey Listener module."""
    print_header("TEST 3: Hotkey Listener")
    
    try:
        from core.hotkey import HotkeyListener
        
        print_info("Initializing hotkey listener...")
        
        press_count = [0]
        
        def on_press():
            press_count[0] += 1
            print_success(f"F4 pressed! (count: {press_count[0]})")
        
        def on_release():
            print_info("F4 released")
        
        hotkey = HotkeyListener()
        hotkey.on_hotkey = on_press
        hotkey.on_release = on_release
        
        print_success("Hotkey listener initialized")
        
        print_info("Starting listener...")
        hotkey.start()
        print_success("Hotkey listener started")
        
        print(f"\n{Fore.YELLOW}Press F4 a few times to test, then press Enter to continue...{Style.RESET_ALL}")
        input()
        
        print_info("Stopping listener...")
        hotkey.stop()
        print_success(f"Hotkey listener stopped. Total F4 presses: {press_count[0]}")
        
        return True
        
    except Exception as e:
        print_error(f"Hotkey test failed: {e}")
        return False


def test_integration():
    """Test all modules working together."""
    print_header("TEST 4: Integration Test")
    
    model_path = "models/vosk-model-small-en-us-0.15"
    
    try:
        from core.tts import TextToSpeech
        from core.stt import SpeechToText
        from core.hotkey import HotkeyListener
        
        # Check model
        if not Path(model_path).exists():
            print_info("Skipping integration test (Vosk model not found)")
            return True
        
        print_info("Initializing all modules...")
        
        tts = TextToSpeech()
        stt = SpeechToText(model_path)
        hotkey = HotkeyListener()
        
        print_success("All modules initialized")
        
        # Setup hotkey to trigger listening
        listening = [False]
        
        def on_hotkey():
            if not listening[0]:
                listening[0] = True
                print_info("Listening for command...")
                tts.speak_async("Yes sir?")
        
        hotkey.on_hotkey = on_hotkey
        hotkey.start()
        stt.start_listening()
        
        print(f"\n{Fore.CYAN}Integration test ready!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press F4 to activate, speak a command, press Enter to exit.{Style.RESET_ALL}\n")
        
        # Simple loop
        try:
            while True:
                if listening[0]:
                    text = stt.get_text(timeout=3)
                    if text:
                        print_success(f"Command: \"{text}\"")
                        tts.speak(f"I heard: {text}")
                    listening[0] = False
                
                # Check for Enter key (non-blocking would be better)
                import msvcrt
                if msvcrt.kbhit():
                    if msvcrt.getch() == b'\r':
                        break
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        
        # Cleanup
        hotkey.stop()
        stt.cleanup()
        print_success("Integration test complete")
        
        return True
        
    except Exception as e:
        print_error(f"Integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print(f"\n{Fore.CYAN}{'#'*50}")
    print(f"#  VOICE BOT - STREAM 1 TESTS")
    print(f"#  Voice I/O Layer")
    print(f"{'#'*50}{Style.RESET_ALL}")
    
    results = {}
    
    # Test TTS
    results['TTS'] = test_tts()
    
    # Test STT
    results['STT'] = test_stt()
    
    # Test Hotkey
    results['Hotkey'] = test_hotkey()
    
    # Integration (optional)
    print(f"\n{Fore.YELLOW}Run integration test? (y/n): {Style.RESET_ALL}", end="")
    choice = input().strip().lower()
    if choice == 'y':
        results['Integration'] = test_integration()
    
    # Summary
    print_header("TEST SUMMARY")
    
    all_passed = True
    for name, passed in results.items():
        if passed:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
            all_passed = False
    
    print()
    if all_passed:
        print(f"{Fore.GREEN}All tests passed! Stream 1 is ready.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Some tests failed. Check the errors above.{Style.RESET_ALL}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
