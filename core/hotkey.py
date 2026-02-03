"""
Global Hotkey Listener Module using pynput.
Listens for F4 key globally to trigger voice commands.
"""

import threading
from typing import Optional, Callable

try:
    from pynput import keyboard
except ImportError:
    keyboard = None


class HotkeyListener:
    """
    Global hotkey listener using pynput.
    
    Listens for a configurable hotkey (default: F4) and triggers a callback.
    """
    
    def __init__(self, hotkey: keyboard.Key = None):
        """
        Initialize the hotkey listener.
        
        Args:
            hotkey: The key to listen for (default: F4)
        """
        if not keyboard:
            raise ImportError("pynput is not installed. Run: pip install pynput")
        
        self._hotkey = hotkey or keyboard.Key.f4
        self._listener: Optional[keyboard.Listener] = None
        self._running = False
        self._on_hotkey: Optional[Callable[[], None]] = None
        self._on_release: Optional[Callable[[], None]] = None
        self._pressed = False
    
    @property
    def on_hotkey(self) -> Optional[Callable[[], None]]:
        """Get the hotkey press callback."""
        return self._on_hotkey
    
    @on_hotkey.setter
    def on_hotkey(self, callback: Callable[[], None]):
        """
        Set the callback for when hotkey is pressed.
        
        Args:
            callback: Function to call when hotkey is pressed
        """
        self._on_hotkey = callback
    
    @property
    def on_release(self) -> Optional[Callable[[], None]]:
        """Get the hotkey release callback."""
        return self._on_release
    
    @on_release.setter
    def on_release(self, callback: Callable[[], None]):
        """
        Set the callback for when hotkey is released.
        
        Args:
            callback: Function to call when hotkey is released
        """
        self._on_release = callback
    
    def _on_press(self, key) -> None:
        """Internal handler for key press events."""
        try:
            if key == self._hotkey and not self._pressed:
                self._pressed = True
                if self._on_hotkey:
                    # Run callback in separate thread to not block listener
                    threading.Thread(target=self._on_hotkey, daemon=True).start()
        except Exception:
            pass
    
    def _on_key_release(self, key) -> None:
        """Internal handler for key release events."""
        try:
            if key == self._hotkey and self._pressed:
                self._pressed = False
                if self._on_release:
                    threading.Thread(target=self._on_release, daemon=True).start()
        except Exception:
            pass
    
    def start(self) -> None:
        """Start listening for the hotkey."""
        if self._running:
            return
        
        self._running = True
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_key_release
        )
        self._listener.start()
    
    def stop(self) -> None:
        """Stop listening for the hotkey."""
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
    
    def is_running(self) -> bool:
        """Check if the listener is active."""
        return self._running
    
    def is_pressed(self) -> bool:
        """Check if the hotkey is currently pressed."""
        return self._pressed
    
    def set_hotkey(self, key: keyboard.Key) -> None:
        """
        Change the hotkey.
        
        Args:
            key: The new key to listen for
        """
        was_running = self._running
        if was_running:
            self.stop()
        
        self._hotkey = key
        
        if was_running:
            self.start()
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


class MultiHotkeyListener:
    """
    Listener for multiple hotkeys with different callbacks.
    """
    
    def __init__(self):
        """Initialize the multi-hotkey listener."""
        if not keyboard:
            raise ImportError("pynput is not installed. Run: pip install pynput")
        
        self._hotkeys: dict = {}  # key -> callback
        self._listener: Optional[keyboard.Listener] = None
        self._running = False
    
    def register(self, key: keyboard.Key, callback: Callable[[], None]) -> None:
        """
        Register a hotkey with its callback.
        
        Args:
            key: The key to listen for
            callback: Function to call when key is pressed
        """
        self._hotkeys[key] = callback
    
    def unregister(self, key: keyboard.Key) -> None:
        """
        Unregister a hotkey.
        
        Args:
            key: The key to stop listening for
        """
        self._hotkeys.pop(key, None)
    
    def _on_press(self, key) -> None:
        """Internal handler for key press events."""
        callback = self._hotkeys.get(key)
        if callback:
            threading.Thread(target=callback, daemon=True).start()
    
    def start(self) -> None:
        """Start listening for all registered hotkeys."""
        if self._running:
            return
        
        self._running = True
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()
    
    def stop(self) -> None:
        """Stop listening."""
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None


# Quick test when run directly
if __name__ == "__main__":
    print("Hotkey Listener Test")
    print("Press F4 to test, Ctrl+C to exit")
    print("-" * 40)
    
    def on_f4_press():
        print("F4 pressed!")
    
    def on_f4_release():
        print("F4 released!")
    
    listener = HotkeyListener()
    listener.on_hotkey = on_f4_press
    listener.on_release = on_f4_release
    listener.start()
    
    try:
        input("Press F4, then Enter to exit...\n")
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        print("Stopped.")
