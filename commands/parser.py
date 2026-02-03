"""
Natural language command parsing for Jarvis Voice Bot.
Extracts intent and parameters from spoken commands using regex patterns.
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedCommand:
    """Represents a parsed voice command."""
    intent: str                          # e.g., "open_app", "search", "play"
    target: Optional[str] = None         # e.g., "notepad", "youtube"
    query: Optional[str] = None          # e.g., search terms
    raw_text: str = ""                   # Original spoken text
    confidence: float = 1.0              # Parse confidence (for future use)


class CommandParser:
    """
    Parses natural language into structured commands.
    Uses pattern matching for v1 (can be upgraded to NLU later).

    Usage:
        parser = CommandParser()
        result = parser.parse("open notepad")
        # result.intent = "open_app", result.target = "notepad"
    """

    def __init__(self):
        """Initialize the parser with command patterns."""
        # Each pattern: (compiled_regex, intent, group_mapping)
        # group_mapping: dict mapping group names to result fields
        self._patterns = self._build_patterns()

    def _build_patterns(self) -> list:
        """Build and compile all command patterns."""
        patterns = []

        # === Open Applications ===
        # "open notepad", "open calculator", "open chrome", "launch notepad"
        patterns.append((
            re.compile(
                r"(?:open|launch|start|run)\s+"
                r"(notepad|calculator|calc|chrome|browser|explorer|file\s*explorer|"
                r"word|excel|powerpoint|vscode|code|terminal|cmd|powershell)",
                re.IGNORECASE
            ),
            "open_app",
            {"target": 1}
        ))

        # === Open Websites ===
        # "open youtube", "go to google", "navigate to github"
        patterns.append((
            re.compile(
                r"(?:open|go\s+to|navigate\s+to|visit)\s+"
                r"(youtube|google|gmail|github|twitter|facebook|reddit|"
                r"linkedin|stackoverflow|stack\s*overflow|amazon|netflix|spotify)",
                re.IGNORECASE
            ),
            "open_website",
            {"target": 1}
        ))

        # === Search Commands ===
        # "search for cats on youtube", "search youtube for cats"
        patterns.append((
            re.compile(
                r"search\s+(?:for\s+)?(.+?)\s+on\s+(youtube|google)",
                re.IGNORECASE
            ),
            "search",
            {"query": 1, "target": 2}
        ))

        # "search youtube for cats", "search google for python"
        patterns.append((
            re.compile(
                r"search\s+(youtube|google)\s+for\s+(.+)",
                re.IGNORECASE
            ),
            "search",
            {"target": 1, "query": 2}
        ))

        # "youtube search cats", "google search python tutorials"
        patterns.append((
            re.compile(
                r"(youtube|google)\s+search\s+(?:for\s+)?(.+)",
                re.IGNORECASE
            ),
            "search",
            {"target": 1, "query": 2}
        ))

        # "google quantum computing", "youtube lofi music" (implicit search)
        patterns.append((
            re.compile(
                r"^(google|youtube)\s+(.+)",
                re.IGNORECASE
            ),
            "search",
            {"target": 1, "query": 2}
        ))

        # === Play on YouTube ===
        # "play lofi music on youtube", "play funny cats on youtube"
        patterns.append((
            re.compile(
                r"play\s+(.+?)\s+on\s+youtube",
                re.IGNORECASE
            ),
            "play_youtube",
            {"query": 1}
        ))

        # "play lofi music" (assumes YouTube)
        patterns.append((
            re.compile(
                r"play\s+(.+?)(?:\s+on\s+youtube)?$",
                re.IGNORECASE
            ),
            "play_youtube",
            {"query": 1}
        ))

        # === Media Control ===
        # "play", "pause", "resume", "stop video", "pause the video"
        patterns.append((
            re.compile(
                r"^(play|pause|resume)\s*(?:the\s+)?(?:video|music|song)?$",
                re.IGNORECASE
            ),
            "media_control",
            {"target": 1}
        ))

        # === Volume Control ===
        # "volume up", "volume down", "mute", "unmute"
        patterns.append((
            re.compile(
                r"(?:volume\s+)?(up|down|mute|unmute)",
                re.IGNORECASE
            ),
            "volume_control",
            {"target": 1}
        ))

        # "set volume to 50", "volume 75"
        patterns.append((
            re.compile(
                r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)",
                re.IGNORECASE
            ),
            "volume_set",
            {"target": 1}
        ))

        # === Stop/Exit Commands ===
        # "stop", "exit", "quit", "shutdown", "goodbye"
        patterns.append((
            re.compile(
                r"^(stop|exit|quit|shutdown|goodbye|bye|good\s*bye|terminate|close\s+jarvis)$",
                re.IGNORECASE
            ),
            "stop",
            {"target": 1}
        ))

        # === Status/Help Commands ===
        # "status", "how are you", "are you there"
        patterns.append((
            re.compile(
                r"^(status|how\s+are\s+you|are\s+you\s+there|you\s+there|hello|hi)$",
                re.IGNORECASE
            ),
            "status",
            {}
        ))

        # "help", "what can you do"
        patterns.append((
            re.compile(
                r"^(help|what\s+can\s+you\s+do|commands|show\s+commands)$",
                re.IGNORECASE
            ),
            "help",
            {}
        ))

        # === Type/Write Commands ===
        # "type hello world", "write hello"
        patterns.append((
            re.compile(
                r"(?:type|write)\s+(.+)",
                re.IGNORECASE
            ),
            "type_text",
            {"query": 1}
        ))

        # === Screenshot ===
        # "take screenshot", "screenshot", "capture screen"
        patterns.append((
            re.compile(
                r"(?:take\s+)?(?:a\s+)?screenshot|capture\s+screen",
                re.IGNORECASE
            ),
            "screenshot",
            {}
        ))

        # === Time/Date ===
        # "what time is it", "what's the time", "current time"
        patterns.append((
            re.compile(
                r"(?:what(?:'s|\s+is)\s+the\s+)?(?:current\s+)?time",
                re.IGNORECASE
            ),
            "get_time",
            {}
        ))

        # "what's the date", "today's date"
        patterns.append((
            re.compile(
                r"(?:what(?:'s|\s+is)\s+)?(?:the\s+|today(?:'s)?\s+)?date",
                re.IGNORECASE
            ),
            "get_date",
            {}
        ))

        return patterns

    def parse(self, text: str) -> Optional[ParsedCommand]:
        """
        Parse spoken text into a command.

        Args:
            text: The recognized speech text

        Returns:
            ParsedCommand if matched, None if no match
        """
        if not text:
            return None

        text = text.strip()

        for pattern, intent, group_mapping in self._patterns:
            match = pattern.search(text)
            if match:
                cmd = ParsedCommand(intent=intent, raw_text=text)

                # Extract groups based on mapping
                for field, group_num in group_mapping.items():
                    value = match.group(group_num)
                    if value:
                        value = self._normalize_value(value.strip(), field)
                        setattr(cmd, field, value)

                return cmd

        return None

    def _normalize_value(self, value: str, field: str) -> str:
        """
        Normalize extracted values.

        Args:
            value: The raw extracted value
            field: The field name (target, query, etc.)

        Returns:
            Normalized value
        """
        value = value.lower().strip()

        # Normalize app names
        if field == "target":
            aliases = {
                "calc": "calculator",
                "browser": "chrome",
                "file explorer": "explorer",
                "code": "vscode",
                "stack overflow": "stackoverflow",
            }
            value = aliases.get(value, value)

        return value

    def add_pattern(self, pattern: str, intent: str, group_mapping: dict) -> None:
        """
        Add a custom pattern at runtime.

        Args:
            pattern: Regex pattern string
            intent: Intent name for this pattern
            group_mapping: Dict mapping field names to group numbers
        """
        compiled = re.compile(pattern, re.IGNORECASE)
        self._patterns.append((compiled, intent, group_mapping))

    def get_supported_intents(self) -> list[str]:
        """Get list of all supported intent types."""
        return list(set(intent for _, intent, _ in self._patterns))


# Convenience function for quick parsing
def parse_command(text: str) -> Optional[ParsedCommand]:
    """
    Quick parse function using default parser.

    Args:
        text: The text to parse

    Returns:
        ParsedCommand or None
    """
    parser = CommandParser()
    return parser.parse(text)
