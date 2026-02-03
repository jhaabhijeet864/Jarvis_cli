"""
Test script for Stream 3: Commands Layer
Tests the parser, registry, and handlers independently.

Run this to verify Stream 3 is working:
    python test_stream3.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_parser():
    """Test the CommandParser with various inputs."""
    print("=" * 60)
    print("TESTING: CommandParser")
    print("=" * 60)

    from commands.parser import CommandParser

    parser = CommandParser()

    # Test cases: (input text, expected intent, expected target, expected query)
    test_cases = [
        # Open apps
        ("open notepad", "open_app", "notepad", None),
        ("launch chrome", "open_app", "chrome", None),
        ("start calculator", "open_app", "calculator", None),
        ("open vscode", "open_app", "vscode", None),

        # Open websites
        ("open youtube", "open_website", "youtube", None),
        ("go to google", "open_website", "google", None),
        ("visit github", "open_website", "github", None),

        # Search commands
        ("search for cats on youtube", "search", "youtube", "cats"),
        ("search youtube for lofi music", "search", "youtube", "lofi music"),
        ("google python tutorials", "search", "google", "python tutorials"),
        ("youtube funny videos", "search", "youtube", "funny videos"),
        ("search google for weather", "search", "google", "weather"),

        # Play commands
        ("play lofi music", "play_youtube", None, "lofi music"),
        ("play jazz on youtube", "play_youtube", None, "jazz"),

        # Media control
        ("pause", "media_control", "pause", None),
        ("play", "media_control", "play", None),
        ("resume", "media_control", "resume", None),

        # Stop/Exit
        ("stop", "stop", "stop", None),
        ("exit", "stop", "exit", None),
        ("goodbye", "stop", "goodbye", None),

        # Status/Help
        ("status", "status", None, None),
        ("how are you", "status", None, None),
        ("help", "help", None, None),
        ("what can you do", "help", None, None),

        # Time/Date
        ("what time is it", "get_time", None, None),
        ("what's the date", "get_date", None, None),

        # Type
        ("type hello world", "type_text", None, "hello world"),

        # Screenshot
        ("take screenshot", "screenshot", None, None),

        # Should NOT match
        ("make me a sandwich", None, None, None),
        ("fly to the moon", None, None, None),
    ]

    passed = 0
    failed = 0

    for text, expected_intent, expected_target, expected_query in test_cases:
        result = parser.parse(text)

        if expected_intent is None:
            # Should NOT match
            if result is None:
                print(f"  [PASS] '{text}' -> No match (expected)")
                passed += 1
            else:
                print(f"  [FAIL] '{text}' -> Got {result.intent} (expected no match)")
                failed += 1
        else:
            if result is None:
                print(f"  [FAIL] '{text}' -> No match (expected {expected_intent})")
                failed += 1
            elif result.intent != expected_intent:
                print(f"  [FAIL] '{text}' -> intent={result.intent} (expected {expected_intent})")
                failed += 1
            else:
                # Check target and query if specified
                target_ok = expected_target is None or result.target == expected_target
                query_ok = expected_query is None or result.query == expected_query

                if target_ok and query_ok:
                    print(f"  [PASS] '{text}' -> intent={result.intent}, target={result.target}, query={result.query}")
                    passed += 1
                else:
                    print(f"  [FAIL] '{text}' -> target={result.target} (expected {expected_target}), query={result.query} (expected {expected_query})")
                    failed += 1

    print()
    print(f"Parser Tests: {passed} passed, {failed} failed")
    print()
    return failed == 0


def test_registry():
    """Test the CommandRegistry functionality."""
    print("=" * 60)
    print("TESTING: CommandRegistry")
    print("=" * 60)

    from commands.registry import CommandRegistry

    registry = CommandRegistry()

    # Register some test handlers
    @registry.register("test_echo", "Echoes input", ["echo hello"])
    def handle_echo(message: str = "default", **kwargs):
        return f"Echo: {message}"

    @registry.register("test_math", "Does math", ["add 2 2"])
    def handle_math(a: int = 0, b: int = 0, **kwargs):
        return f"Result: {a + b}"

    passed = 0
    failed = 0

    # Test 1: Handler registration
    if registry.has_handler("test_echo"):
        print("  [PASS] Handler registration works")
        passed += 1
    else:
        print("  [FAIL] Handler registration failed")
        failed += 1

    # Test 2: Handler dispatch
    result = registry.dispatch("test_echo", message="Hello World")
    if result == "Echo: Hello World":
        print(f"  [PASS] Dispatch works: {result}")
        passed += 1
    else:
        print(f"  [FAIL] Dispatch failed: {result}")
        failed += 1

    # Test 3: Dispatch with kwargs
    result = registry.dispatch("test_math", a=5, b=3)
    if result == "Result: 8":
        print(f"  [PASS] Dispatch with kwargs: {result}")
        passed += 1
    else:
        print(f"  [FAIL] Dispatch with kwargs failed: {result}")
        failed += 1

    # Test 4: Unknown handler
    success, error = registry.dispatch_safe("unknown_intent")
    if not success and "Unknown command" in error:
        print(f"  [PASS] Unknown handler handled: {error}")
        passed += 1
    else:
        print(f"  [FAIL] Unknown handler not handled properly")
        failed += 1

    # Test 5: Help text generation
    help_text = registry.get_help_text()
    if "test_echo" in help_text and "test_math" in help_text:
        print("  [PASS] Help text generation works")
        passed += 1
    else:
        print("  [FAIL] Help text generation failed")
        failed += 1

    # Test 6: Handler disable/enable
    registry.disable_handler("test_echo")
    if not registry.has_handler("test_echo"):
        print("  [PASS] Handler disable works")
        passed += 1
    else:
        print("  [FAIL] Handler disable failed")
        failed += 1

    registry.enable_handler("test_echo")
    if registry.has_handler("test_echo"):
        print("  [PASS] Handler enable works")
        passed += 1
    else:
        print("  [FAIL] Handler enable failed")
        failed += 1

    print()
    print(f"Registry Tests: {passed} passed, {failed} failed")
    print()
    return failed == 0


def test_handlers():
    """Test the actual command handlers."""
    print("=" * 60)
    print("TESTING: Command Handlers")
    print("=" * 60)

    from commands.handlers import registry, handle_status, handle_help, handle_get_time, handle_get_date

    passed = 0
    failed = 0

    # Test 1: Status handler
    result = registry.dispatch("status")
    if "operational" in result.lower() or "sir" in result.lower():
        print(f"  [PASS] Status handler: '{result[:50]}...'")
        passed += 1
    else:
        print(f"  [FAIL] Status handler returned: {result}")
        failed += 1

    # Test 2: Help handler
    result = registry.dispatch("help")
    if "available" in result.lower() or "can do" in result.lower():
        print(f"  [PASS] Help handler works (returned {len(result)} chars)")
        passed += 1
    else:
        print(f"  [FAIL] Help handler returned: {result[:100]}")
        failed += 1

    # Test 3: Time handler
    result = registry.dispatch("get_time")
    if "time" in result.lower() or ":" in result:
        print(f"  [PASS] Time handler: '{result}'")
        passed += 1
    else:
        print(f"  [FAIL] Time handler returned: {result}")
        failed += 1

    # Test 4: Date handler
    result = registry.dispatch("get_date")
    if "2" in result or "day" in result.lower():  # Should contain year or day name
        print(f"  [PASS] Date handler: '{result}'")
        passed += 1
    else:
        print(f"  [FAIL] Date handler returned: {result}")
        failed += 1

    # Test 5: Stop handler
    result = registry.dispatch("stop")
    if "goodbye" in result.lower() or "bye" in result.lower():
        print(f"  [PASS] Stop handler: '{result}'")
        passed += 1
    else:
        print(f"  [FAIL] Stop handler returned: {result}")
        failed += 1

    # Test 6: Open app handler (without actual app launcher)
    result = registry.dispatch("open_app", target="notepad")
    if "notepad" in result.lower():
        print(f"  [PASS] Open app handler: '{result}'")
        passed += 1
    else:
        print(f"  [FAIL] Open app handler returned: {result}")
        failed += 1

    # Test 7: Search handler (without actual browser)
    result = registry.dispatch("search", target="youtube", query="lofi music")
    if "youtube" in result.lower() and "lofi" in result.lower():
        print(f"  [PASS] Search handler: '{result}'")
        passed += 1
    else:
        print(f"  [FAIL] Search handler returned: {result}")
        failed += 1

    print()
    print(f"Handler Tests: {passed} passed, {failed} failed")
    print()
    return failed == 0


def test_integration():
    """Test full flow: parse -> dispatch."""
    print("=" * 60)
    print("TESTING: Integration (Parse -> Dispatch)")
    print("=" * 60)

    from commands.parser import CommandParser
    from commands.handlers import registry

    parser = CommandParser()

    test_commands = [
        "open notepad",
        "what time is it",
        "search for cats on youtube",
        "help",
        "stop",
    ]

    passed = 0
    failed = 0

    for text in test_commands:
        parsed = parser.parse(text)
        if parsed:
            # Build kwargs from parsed command
            kwargs = {}
            if parsed.target:
                kwargs['target'] = parsed.target
            if parsed.query:
                kwargs['query'] = parsed.query

            success, result = registry.dispatch_safe(parsed.intent, **kwargs)
            if success:
                print(f"  [PASS] '{text}' -> {parsed.intent} -> '{result[:50]}...'")
                passed += 1
            else:
                print(f"  [FAIL] '{text}' -> {parsed.intent} -> ERROR: {result}")
                failed += 1
        else:
            print(f"  [FAIL] '{text}' -> Could not parse")
            failed += 1

    print()
    print(f"Integration Tests: {passed} passed, {failed} failed")
    print()
    return failed == 0


def main():
    """Run all tests."""
    print()
    print("*" * 60)
    print("*  STREAM 3 TESTS: Commands Layer")
    print("*" * 60)
    print()

    results = []

    results.append(("Parser", test_parser()))
    results.append(("Registry", test_registry()))
    results.append(("Handlers", test_handlers()))
    results.append(("Integration", test_integration()))

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("All Stream 3 tests PASSED!")
        print("Stream 3 is ready for integration.")
    else:
        print("Some tests FAILED. Please review the output above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
