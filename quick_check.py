"""
Quick System Check for Jarvis CLI
A fast sanity check to ensure critical components work.

Usage:
    python quick_check.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Color helpers
class C:
    G = '\033[92m'  # Green
    R = '\033[91m'  # Red
    Y = '\033[93m'  # Yellow
    E = '\033[0m'   # End
    B = '\033[1m'   # Bold


def check(name, test_func):
    """Run a test and print result."""
    try:
        test_func()
        print(f"{C.G}✓{C.E} {name}")
        return True
    except Exception as e:
        print(f"{C.R}✗{C.E} {name}: {str(e)[:60]}")
        return False


print(f"\n{C.B}Jarvis CLI - Quick System Check{C.E}\n")

passed = 0
total = 0

# Test 1: Logger
def test_logger():
    from utils.logger import JarvisLogger
    import logging
    logger = logging.getLogger('main')
    assert len(logger.handlers) > 0, "No handlers"
    
total += 1
if check("Logger Module", test_logger):
    passed += 1

# Test 2: Settings
def test_settings():
    from config.settings import Settings
    s = Settings()
    rate = s.get('tts.rate')
    assert rate is not None, "Can't read setting"
    
total += 1
if check("Settings System", test_settings):
    passed += 1

# Test 3: STT
def test_stt():
    from core.stt import SpeechToText
    
total += 1
if check("Speech-to-Text", test_stt):
    passed += 1

# Test 4: TTS
def test_tts():
    from core.tts import TextToSpeech
    
total += 1
if check("Text-to-Speech", test_tts):
    passed += 1

# Test 5: Commands
def test_commands():
    from commands.parser import CommandParser
    from commands.handlers import registry
    parser = CommandParser()
    result = parser.parse("open notepad")
    assert result.intent == "open_app", "Parser failed"
    assert len(registry) > 0, "No handlers"
    
total += 1
if check("Command System", test_commands):
    passed += 1

# Test 6: Actions
def test_actions():
    from actions.apps import AppLauncher
    from actions.browser import BrowserController
    
total += 1
if check("Action Modules", test_actions):
    passed += 1

# Test 7: LLM
def test_llm():
    from services.llm_api import CodeGenerator
    import config
    # Just check import, not functionality (needs API key)
    
total += 1
if check("LLM Service", test_llm):
    passed += 1

# Test 8: Responses
def test_responses():
    from utils.responses import JarvisResponses
    r = JarvisResponses()
    text = r.get('greeting')
    assert len(text) > 0, "No response"
    
total += 1
if check("Response Templates", test_responses):
    passed += 1

# Summary
print(f"\n{C.B}Results: {passed}/{total} checks passed{C.E}")

if passed == total:
    print(f"{C.G}{C.B}✓ All systems operational!{C.E}\n")
    sys.exit(0)
else:
    print(f"{C.R}{C.B}✗ Some checks failed. Run 'python test_integration.py' for details.{C.E}\n")
    sys.exit(1)
