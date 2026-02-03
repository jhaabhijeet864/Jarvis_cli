"""
Command registry for Jarvis Voice Bot.
Provides decorator-based command registration and routing.
"""
from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class CommandHandler:
    """Wrapper for command handler with metadata."""
    func: Callable
    description: str
    examples: List[str] = field(default_factory=list)
    enabled: bool = True


class CommandRegistry:
    """
    Central registry for all command handlers.
    Enables easy extension with new commands.

    Usage:
        registry = CommandRegistry()

        @registry.register("open_app", "Opens a desktop application")
        def handle_open_app(target: str, **kwargs):
            # Open the app
            return "App opened"

        # Later, dispatch commands
        result = registry.dispatch("open_app", target="notepad")
    """

    def __init__(self):
        """Initialize empty registry."""
        self._handlers: Dict[str, CommandHandler] = {}

    def register(
        self,
        intent: str,
        description: str = "",
        examples: List[str] = None
    ) -> Callable:
        """
        Decorator to register a command handler.

        Args:
            intent: The intent name to handle (e.g., "open_app")
            description: Human-readable description of what this command does
            examples: Example phrases that trigger this command

        Returns:
            Decorator function

        Example:
            @registry.register("open_app", "Opens desktop apps", ["open notepad"])
            def handle_open_app(target, **kwargs):
                ...
        """
        def decorator(func: Callable) -> Callable:
            self._handlers[intent] = CommandHandler(
                func=func,
                description=description,
                examples=examples or [],
                enabled=True
            )
            return func
        return decorator

    def register_handler(
        self,
        intent: str,
        handler: Callable,
        description: str = "",
        examples: List[str] = None
    ) -> None:
        """
        Register a handler function directly (non-decorator style).

        Args:
            intent: The intent name
            handler: The handler function
            description: Description of the command
            examples: Example trigger phrases
        """
        self._handlers[intent] = CommandHandler(
            func=handler,
            description=description,
            examples=examples or [],
            enabled=True
        )

    def dispatch(self, intent: str, **kwargs) -> Any:
        """
        Dispatch a command to its registered handler.

        Args:
            intent: The intent to handle
            **kwargs: Arguments to pass to the handler

        Returns:
            Handler result

        Raises:
            KeyError: If no handler is registered for the intent
            Exception: If the handler raises an exception
        """
        if intent not in self._handlers:
            raise KeyError(f"No handler registered for intent: {intent}")

        handler = self._handlers[intent]

        if not handler.enabled:
            raise RuntimeError(f"Handler for '{intent}' is disabled")

        return handler.func(**kwargs)

    def dispatch_safe(self, intent: str, **kwargs) -> tuple[bool, Any]:
        """
        Dispatch a command with error handling.

        Args:
            intent: The intent to handle
            **kwargs: Arguments to pass to the handler

        Returns:
            Tuple of (success: bool, result_or_error: Any)
        """
        try:
            result = self.dispatch(intent, **kwargs)
            return (True, result)
        except KeyError as e:
            return (False, f"Unknown command: {intent}")
        except Exception as e:
            return (False, f"Error executing command: {str(e)}")

    def has_handler(self, intent: str) -> bool:
        """
        Check if a handler exists for the intent.

        Args:
            intent: The intent to check

        Returns:
            True if handler exists and is enabled
        """
        return intent in self._handlers and self._handlers[intent].enabled

    def get_handler(self, intent: str) -> Optional[CommandHandler]:
        """
        Get the handler for an intent.

        Args:
            intent: The intent name

        Returns:
            CommandHandler or None if not found
        """
        return self._handlers.get(intent)

    def enable_handler(self, intent: str) -> None:
        """Enable a handler by intent name."""
        if intent in self._handlers:
            self._handlers[intent].enabled = True

    def disable_handler(self, intent: str) -> None:
        """Disable a handler by intent name."""
        if intent in self._handlers:
            self._handlers[intent].enabled = False

    def remove_handler(self, intent: str) -> bool:
        """
        Remove a handler from the registry.

        Args:
            intent: The intent to remove

        Returns:
            True if removed, False if not found
        """
        if intent in self._handlers:
            del self._handlers[intent]
            return True
        return False

    def get_all_intents(self) -> List[str]:
        """Get list of all registered intent names."""
        return list(self._handlers.keys())

    def get_all_handlers(self) -> Dict[str, CommandHandler]:
        """Get all registered handlers."""
        return self._handlers.copy()

    def get_enabled_handlers(self) -> Dict[str, CommandHandler]:
        """Get only enabled handlers."""
        return {k: v for k, v in self._handlers.items() if v.enabled}

    def get_help_text(self) -> str:
        """
        Generate help text listing all commands.

        Returns:
            Formatted help string
        """
        lines = ["Available commands:", ""]

        for intent, handler in sorted(self._handlers.items()):
            if not handler.enabled:
                continue

            status = "" if handler.enabled else " [DISABLED]"
            lines.append(f"  {intent}{status}")
            if handler.description:
                lines.append(f"    {handler.description}")
            if handler.examples:
                lines.append("    Examples:")
                for example in handler.examples[:3]:  # Show max 3 examples
                    lines.append(f"      - \"{example}\"")
            lines.append("")

        return "\n".join(lines)

    def get_command_list(self) -> List[dict]:
        """
        Get commands as a list of dictionaries.
        Useful for generating UI or API responses.

        Returns:
            List of command info dicts
        """
        return [
            {
                "intent": intent,
                "description": handler.description,
                "examples": handler.examples,
                "enabled": handler.enabled
            }
            for intent, handler in self._handlers.items()
        ]

    def __len__(self) -> int:
        """Return number of registered handlers."""
        return len(self._handlers)

    def __contains__(self, intent: str) -> bool:
        """Check if intent is registered."""
        return intent in self._handlers


# Global registry instance (can be imported and used directly)
registry = CommandRegistry()
