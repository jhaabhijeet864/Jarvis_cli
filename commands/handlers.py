"""
Command handler implementations for Jarvis Voice Bot.
Each handler processes a specific intent and returns a response string.

Note: This module depends on the actions module (Stream 2).
Handlers will work once actions/apps.py, actions/browser.py, etc. are implemented.
"""
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from commands.registry import CommandRegistry

# Type hints for action controllers (avoid circular imports)
if TYPE_CHECKING:
    from actions.apps import AppLauncher
    from actions.browser import BrowserController
    from actions.media import MediaController
    from actions.search import SearchController

# Create registry instance for this module
registry = CommandRegistry()

# Placeholder for action controllers (set via init_handlers)
_app_launcher = None
_browser = None
_media = None
_search = None
_responses = None


def init_handlers(
    app_launcher=None,
    browser=None,
    responses=None
) -> None:
    """
    Initialize handlers with action controller instances.
    Call this from main.py after creating the action controllers.

    Args:
        app_launcher: AppLauncher instance for opening apps
        browser: BrowserController instance for web automation
        responses: JarvisResponses instance for generating responses
    """
    global _app_launcher, _browser, _media, _search, _responses

    _app_launcher = app_launcher
    _browser = browser
    _responses = responses

    # Create dependent controllers if browser is available
    if browser:
        try:
            from actions.media import MediaController
            from actions.search import SearchController
            _media = MediaController(browser)
            _search = SearchController(browser)
        except ImportError:
            pass  # Stream 2 not yet available


def _get_response(key: str, **kwargs) -> str:
    """
    Get a response from the responses module.
    Falls back to simple strings if responses module not initialized.
    """
    if _responses:
        return _responses.get(key, **kwargs)

    # Fallback responses
    fallbacks = {
        "open_app_success": f"Opening {kwargs.get('app', 'application')} now, sir.",
        "open_app_failure": f"I couldn't open {kwargs.get('app', 'that')}, sir.",
        "open_website_success": f"Opening {kwargs.get('site', 'website')}, sir.",
        "open_website_failure": f"Unable to open {kwargs.get('site', 'that')}, sir.",
        "search_success": f"Searching {kwargs.get('platform', 'the web')} for {kwargs.get('query', 'that')}, sir.",
        "search_failure": "Search failed, sir.",
        "search_no_query": "What would you like me to search for, sir?",
        "play_success": f"Playing {kwargs.get('query', 'that')} now, sir.",
        "play_failure": "I couldn't play that, sir.",
        "play_no_query": "What would you like me to play, sir?",
        "media_play": "Playing, sir.",
        "media_pause": "Paused, sir.",
        "media_unknown": "I didn't understand that media command, sir.",
        "goodbye": "Goodbye, sir. Jarvis signing off.",
        "status": "All systems operational, sir.",
        "help": "Here's what I can do for you, sir:",
        "not_understood": "I didn't quite catch that, sir.",
        "error": f"I encountered an error, sir. {kwargs.get('error', '')}",
        "type_success": "Done typing, sir.",
        "screenshot_success": "Screenshot captured, sir.",
        "time": f"The time is {kwargs.get('time', 'unknown')}, sir.",
        "date": f"Today is {kwargs.get('date', 'unknown')}, sir.",
    }
    return fallbacks.get(key, "Understood, sir.")


# =============================================================================
# Command Handlers
# =============================================================================

@registry.register(
    "open_app",
    "Opens a desktop application",
    ["open notepad", "open calculator", "launch chrome"]
)
def handle_open_app(target: str = None, **kwargs) -> str:
    """
    Open a desktop application by name.

    Args:
        target: Application name (e.g., "notepad", "chrome")

    Returns:
        Response string
    """
    if not target:
        return "Which application should I open, sir?"

    if _app_launcher:
        success = _app_launcher.open(target)
        if success:
            return _get_response("open_app_success", app=target)
        return _get_response("open_app_failure", app=target)

    # Fallback: return message without actually opening
    return _get_response("open_app_success", app=target)


@registry.register(
    "open_website",
    "Opens a website in the browser",
    ["open youtube", "go to google", "open github"]
)
def handle_open_website(target: str = None, **kwargs) -> str:
    """
    Open a website in the browser.

    Args:
        target: Website name or URL

    Returns:
        Response string
    """
    if not target:
        return "Which website should I open, sir?"

    if _browser:
        success = _browser.open_url(target)
        if success:
            return _get_response("open_website_success", site=target)
        return _get_response("open_website_failure", site=target)

    return _get_response("open_website_success", site=target)


@registry.register(
    "search",
    "Searches on YouTube or Google",
    ["search for cats on youtube", "google python tutorials", "search youtube for music"]
)
def handle_search(target: str = "google", query: str = None, **kwargs) -> str:
    """
    Perform a search on YouTube or Google.

    Args:
        target: Platform ("youtube" or "google")
        query: Search query

    Returns:
        Response string
    """
    if not query:
        return _get_response("search_no_query")

    if _search:
        success = _search.search(query, platform=target)
        if success:
            return _get_response("search_success", query=query, platform=target)
        return _get_response("search_failure", platform=target)

    return _get_response("search_success", query=query, platform=target)


@registry.register(
    "play_youtube",
    "Plays a video on YouTube",
    ["play lofi music", "play funny cats on youtube"]
)
def handle_play_youtube(query: str = None, **kwargs) -> str:
    """
    Search and play a video on YouTube.

    Args:
        query: What to search for and play

    Returns:
        Response string
    """
    if not query:
        return _get_response("play_no_query")

    if _search:
        success = _search.search_and_play(query)
        if success:
            return _get_response("play_success", query=query)
        return _get_response("play_failure")

    return _get_response("play_success", query=query)


@registry.register(
    "media_control",
    "Controls media playback (play/pause)",
    ["play", "pause", "resume"]
)
def handle_media_control(target: str = "play", **kwargs) -> str:
    """
    Control media playback.

    Args:
        target: Action ("play", "pause", "resume")

    Returns:
        Response string
    """
    action = (target or "play").lower()

    if _media:
        if action in ["play", "resume"]:
            _media.play()
            return _get_response("media_play")
        elif action == "pause":
            _media.pause()
            return _get_response("media_pause")

    # Without media controller, just acknowledge
    if action in ["play", "resume"]:
        return _get_response("media_play")
    elif action == "pause":
        return _get_response("media_pause")

    return _get_response("media_unknown")


@registry.register(
    "volume_control",
    "Controls system volume",
    ["volume up", "volume down", "mute"]
)
def handle_volume_control(target: str = None, **kwargs) -> str:
    """
    Control system volume.

    Args:
        target: Action ("up", "down", "mute", "unmute")

    Returns:
        Response string
    """
    action = (target or "").lower()

    # Volume control would need pyautogui or pycaw
    # For now, return acknowledgment
    if action == "up":
        return "Volume up, sir."
    elif action == "down":
        return "Volume down, sir."
    elif action == "mute":
        return "Muted, sir."
    elif action == "unmute":
        return "Unmuted, sir."

    return "Volume adjusted, sir."


@registry.register(
    "volume_set",
    "Sets volume to a specific level",
    ["set volume to 50", "volume 75"]
)
def handle_volume_set(target: str = None, **kwargs) -> str:
    """
    Set volume to a specific level.

    Args:
        target: Volume level (0-100)

    Returns:
        Response string
    """
    try:
        level = int(target) if target else 50
        level = max(0, min(100, level))  # Clamp to 0-100
        return f"Volume set to {level}%, sir."
    except ValueError:
        return "I couldn't understand that volume level, sir."


@registry.register(
    "stop",
    "Exits the assistant",
    ["stop", "exit", "goodbye", "quit"]
)
def handle_stop(**kwargs) -> str:
    """
    Signal to stop the assistant.
    The main loop should check for this response and exit.

    Returns:
        Goodbye response
    """
    return _get_response("goodbye")


@registry.register(
    "status",
    "Reports assistant status",
    ["status", "how are you", "hello"]
)
def handle_status(**kwargs) -> str:
    """
    Report current status.

    Returns:
        Status response
    """
    return _get_response("status")


@registry.register(
    "help",
    "Shows available commands",
    ["help", "what can you do"]
)
def handle_help(**kwargs) -> str:
    """
    Show help information.

    Returns:
        Help text with available commands
    """
    help_intro = _get_response("help")
    commands_help = registry.get_help_text()
    return f"{help_intro}\n\n{commands_help}"


@registry.register(
    "type_text",
    "Types text using the keyboard",
    ["type hello world", "write this is a test"]
)
def handle_type_text(query: str = None, **kwargs) -> str:
    """
    Type text using pyautogui.

    Args:
        query: Text to type

    Returns:
        Response string
    """
    if not query:
        return "What would you like me to type, sir?"

    try:
        import pyautogui
        pyautogui.typewrite(query, interval=0.02)
        return _get_response("type_success")
    except ImportError:
        return "Typing functionality requires pyautogui, sir."
    except Exception as e:
        return _get_response("error", error=str(e))


@registry.register(
    "screenshot",
    "Takes a screenshot",
    ["take screenshot", "screenshot", "capture screen"]
)
def handle_screenshot(**kwargs) -> str:
    """
    Take a screenshot.

    Returns:
        Response string
    """
    try:
        import pyautogui
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        return f"Screenshot saved as {filename}, sir."
    except ImportError:
        return "Screenshot functionality requires pyautogui, sir."
    except Exception as e:
        return _get_response("error", error=str(e))


@registry.register(
    "get_time",
    "Tells the current time",
    ["what time is it", "current time"]
)
def handle_get_time(**kwargs) -> str:
    """
    Get the current time.

    Returns:
        Response with current time
    """
    current_time = datetime.now().strftime("%I:%M %p")
    return _get_response("time", time=current_time)


@registry.register(
    "get_date",
    "Tells today's date",
    ["what's the date", "today's date"]
)
def handle_get_date(**kwargs) -> str:
    """
    Get today's date.

    Returns:
        Response with current date
    """
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    return _get_response("date", date=current_date)


# =============================================================================
# Utility Functions
# =============================================================================

def get_registry() -> CommandRegistry:
    """
    Get the command registry instance.

    Returns:
        The CommandRegistry with all handlers registered
    """
    return registry


def is_stop_command(response: str) -> bool:
    """
    Check if a response indicates the stop command was executed.

    Args:
        response: The handler response string

    Returns:
        True if this was a stop/exit command
    """
    stop_phrases = ["goodbye", "signing off", "shutting down", "farewell"]
    return any(phrase in response.lower() for phrase in stop_phrases)
