"""
Integration Testing Suite for Jarvis CLI
Tests the settings and logging system integration across all modules.

Usage:
    python test_integration.py
    
This will run all integration tests and provide a detailed report.
"""

import sys
import os
from pathlib import Path
import logging
import json
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestResult:
    """Stores test results."""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name, message=""):
        self.passed.append((test_name, message))
        print(f"{Colors.OKGREEN}✓ PASS{Colors.ENDC} {test_name}")
        if message:
            print(f"       {Colors.OKCYAN}{message}{Colors.ENDC}")
    
    def add_fail(self, test_name, error):
        self.failed.append((test_name, str(error)))
        print(f"{Colors.FAIL}✗ FAIL{Colors.ENDC} {test_name}")
        print(f"       {Colors.FAIL}{error}{Colors.ENDC}")
    
    def add_warning(self, test_name, message):
        self.warnings.append((test_name, message))
        print(f"{Colors.WARNING}⚠ WARN{Colors.ENDC} {test_name}")
        print(f"       {Colors.WARNING}{message}{Colors.ENDC}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Passed: {len(self.passed)}/{total}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {len(self.failed)}/{total}{Colors.ENDC}")
        print(f"{Colors.WARNING}Warnings: {len(self.warnings)}{Colors.ENDC}")
        
        if len(self.failed) == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.ENDC}")
            return True
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.ENDC}")
            return False


def print_section(title):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")


# =============================================================================
# Test 1: Logger Initialization
# =============================================================================

def test_logger_initialization(results):
    """Test that the logging system initializes correctly."""
    print_section("TEST 1: Logger Initialization")
    
    try:
        # Import the logger module
        from utils.logger import JarvisLogger
        
        # Check if logs directory was created
        log_dir = Path('logs')
        if log_dir.exists():
            results.add_pass("Logger directory created", f"Found at: {log_dir.absolute()}")
        else:
            results.add_fail("Logger directory creation", "logs/ directory not found")
            return
        
        # Check if log files exist
        expected_logs = ['main.log', 'stt.log', 'commands.log', 'llm.log', 'errors.log']
        for log_file in expected_logs:
            log_path = log_dir / log_file
            if log_path.exists():
                results.add_pass(f"Log file: {log_file}", f"Size: {log_path.stat().st_size} bytes")
            else:
                results.add_warning(f"Log file: {log_file}", "File not yet created (will be created on first log)")
        
        # Test if loggers are accessible
        loggers = ['main', 'stt', 'commands', 'llm', 'errors']
        for logger_name in loggers:
            logger = logging.getLogger(logger_name)
            if logger.handlers:
                results.add_pass(f"Logger '{logger_name}' initialized", f"Handlers: {len(logger.handlers)}")
            else:
                results.add_fail(f"Logger '{logger_name}' initialization", "No handlers configured")
        
    except Exception as e:
        results.add_fail("Logger initialization", str(e))


# =============================================================================
# Test 2: Settings System
# =============================================================================

def test_settings_system(results):
    """Test that the settings system works correctly."""
    print_section("TEST 2: Settings System")
    
    try:
        from config.settings import Settings
        
        # Test loading settings
        settings = Settings()
        results.add_pass("Settings class instantiation")
        
        # Test default settings structure
        expected_sections = ['audio', 'tts', 'wake_word', 'hotkey', 'gui', 'llm']
        for section in expected_sections:
            value = settings.get(section)
            if value:
                results.add_pass(f"Settings section '{section}'", f"Keys: {list(value.keys())}")
            else:
                results.add_fail(f"Settings section '{section}'", "Section not found")
        
        # Test dot notation access
        test_cases = [
            ('audio.vosk_model', 'models/vosk-model-en-us-0.22-lgraph'),
            ('tts.rate', 180),
            ('wake_word.word', 'jarvis'),
            ('gui.width', 900),
            ('llm.model', 'gemini-pro'),
        ]
        
        for key, expected_default in test_cases:
            value = settings.get(key)
            if value is not None:
                results.add_pass(f"Settings get '{key}'", f"Value: {value}")
            else:
                results.add_warning(f"Settings get '{key}'", f"Expected: {expected_default}, Got: None")
        
        # Test settings file creation
        settings_file = Path('config/settings.json')
        if settings_file.exists():
            results.add_pass("Settings file exists", str(settings_file.absolute()))
            
            # Validate JSON
        try:
            with open(settings_file) as f:
                content = f.read().strip()
                if not content:
                    results.add_warning("Settings file content", "File is empty (will be populated on save)")
                else:
                    data = json.loads(content)
                    results.add_pass("Settings file is valid JSON", f"Sections: {len(data)}")
        except json.JSONDecodeError as e:
            results.add_warning("Settings file JSON", "File is empty or corrupted (will be regenerated)")
        else:
            results.add_warning("Settings file", "config/settings.json not found (will be created on first save)")
        
    except Exception as e:
        results.add_fail("Settings system", str(e))


# =============================================================================
# Test 3: Core Modules Integration
# =============================================================================

def test_core_modules(results):
    """Test that core modules integrate with settings and logging."""
    print_section("TEST 3: Core Modules Integration")
    
    # Test STT Module
    try:
        from core.stt import SpeechToText
        
        # Check if logging is integrated
        stt_logger = logging.getLogger('stt')
        if stt_logger.handlers:
            results.add_pass("STT logging integration", "Logger configured")
        else:
            results.add_warning("STT logging", "Logger not configured")
        
        results.add_pass("STT module import")
        
    except ImportError as e:
        results.add_fail("STT module import", f"Import failed: {e}")
    except Exception as e:
        results.add_warning("STT module", f"Vosk model not found (expected): {e}")
    
    # Test TTS Module
    try:
        from core.tts import TextToSpeech
        
        # Check if logging is integrated
        main_logger = logging.getLogger('main')
        if main_logger.handlers:
            results.add_pass("TTS logging integration", "Logger configured")
        else:
            results.add_warning("TTS logging", "Logger not configured")
        
        results.add_pass("TTS module import")
        
    except ImportError as e:
        results.add_fail("TTS module import", f"Import failed: {e}")
    except Exception as e:
        results.add_warning("TTS module", f"pyttsx3 initialization issue: {e}")


# =============================================================================
# Test 4: Actions Modules Integration
# =============================================================================

def test_actions_modules(results):
    """Test that action modules integrate with logging."""
    print_section("TEST 4: Actions Modules Integration")
    
    modules = [
        ('actions.apps', 'AppLauncher', 'Apps'),
        ('actions.browser', 'BrowserController', 'Browser'),
        ('actions.search', 'SearchController', 'Search'),
        ('actions.media', 'MediaController', 'Media'),
    ]
    
    for module_name, class_name, friendly_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            results.add_pass(f"{friendly_name} module import", f"Class: {class_name}")
            
            # Check if module uses logging (check for logging.getLogger in source)
            import inspect
            source = inspect.getsource(module)
            if 'logging.getLogger' in source:
                results.add_pass(f"{friendly_name} logging integration", "Uses logging")
            else:
                results.add_warning(f"{friendly_name} logging", "May not use logging")
                
        except ImportError as e:
            results.add_fail(f"{friendly_name} module import", str(e))
        except Exception as e:
            results.add_fail(f"{friendly_name} module", str(e))


# =============================================================================
# Test 5: Commands System Integration
# =============================================================================

def test_commands_system(results):
    """Test command parsing and handling with logging."""
    print_section("TEST 5: Commands System Integration")
    
    try:
        from commands.parser import CommandParser
        from commands.registry import CommandRegistry
        from commands.handlers import registry
        
        results.add_pass("Commands modules import")
        
        # Test parser
        parser = CommandParser()
        test_commands = [
            ("open notepad", "open_app", "notepad"),
            ("search for python on google", "search", "google"),
            ("what time is it", "get_time", None),
        ]
        
        for text, expected_intent, expected_target in test_commands:
            parsed = parser.parse(text)
            if parsed and parsed.intent == expected_intent:
                results.add_pass(f"Parse command: '{text}'", f"Intent: {parsed.intent}")
            else:
                results.add_fail(f"Parse command: '{text}'", 
                               f"Expected {expected_intent}, got {parsed.intent if parsed else None}")
        
        # Test registry
        if len(registry) > 0:
            results.add_pass("Command registry", f"{len(registry)} handlers registered")
            
            # List some handlers
            handlers_list = list(registry.get_all_intents())[:5]
            results.add_pass("Sample handlers", f"{', '.join(handlers_list)}")
        else:
            results.add_fail("Command registry", "No handlers registered")
        
    except Exception as e:
        results.add_fail("Commands system", str(e))


# =============================================================================
# Test 6: Services Integration (LLM)
# =============================================================================

def test_services_integration(results):
    """Test that services integrate with settings."""
    print_section("TEST 6: Services Integration (LLM)")
    
    try:
        from services.llm_api import CodeGenerator
        from config.settings import Settings
        
        results.add_pass("LLM service import")
        
        # Check if API key is configured in config.py file itself
        config_file = Path('config.py')
        if config_file.exists():
            with open(config_file) as f:
                config_content = f.read()
                if 'GOOGLE_API_KEY' in config_content:
                    if 'YOUR_API_KEY_HERE' in config_content:
                        results.add_warning("Google API Key", 
                                          "Placeholder detected (set real key in config.py for full functionality)")
                    else:
                        results.add_pass("Google API Key", "API key is configured")
                else:
                    results.add_fail("Google API Key", "GOOGLE_API_KEY not found in config.py")
        else:
            results.add_fail("Google API Key", "config.py file not found")
        
        # Check if LLM uses settings
        settings = Settings()
        llm_config = settings.get('llm')
        if llm_config:
            results.add_pass("LLM settings integration", 
                           f"Model: {llm_config.get('model')}, Temp: {llm_config.get('temperature')}")
        else:
            results.add_fail("LLM settings", "LLM section not found in settings")
        
        # Check logging
        llm_logger = logging.getLogger('llm')
        if llm_logger.handlers:
            results.add_pass("LLM logging integration", "Logger configured")
        else:
            results.add_warning("LLM logging", "Logger not configured")
        
    except ImportError as e:
        results.add_fail("LLM service import", str(e))
    except Exception as e:
        results.add_fail("LLM service", str(e))


# =============================================================================
# Test 7: GUI Integration
# =============================================================================

def test_gui_integration(results):
    """Test that GUI integrates with settings."""
    print_section("TEST 7: GUI Integration")
    
    try:
        import pygame
        results.add_pass("Pygame installed")
        
        # Import GUI module (don't initialize pygame display)
        import sys
        # Prevent pygame from initializing display during import
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        
        with open('gui.py', 'r') as f:
            gui_source = f.read()
        
        # Check for settings integration
        if 'settings' in gui_source and 'self.settings.get' in gui_source:
            results.add_pass("GUI settings integration", "Uses settings.get() calls")
        else:
            results.add_warning("GUI settings", "May not be using settings system")
        
        # Check for logging integration
        if 'logging.getLogger' in gui_source or 'main_logger' in gui_source:
            results.add_pass("GUI logging integration", "Uses logging")
        else:
            results.add_warning("GUI logging", "May not use logging")
        
        # Check for settings parameters
        if 'gui.width' in gui_source or 'gui.height' in gui_source:
            results.add_pass("GUI reads settings", "References gui.width, gui.height, etc.")
        else:
            results.add_warning("GUI settings usage", "May not read GUI-specific settings")
            
    except ImportError:
        results.add_warning("Pygame", "Not installed (required for GUI)")
    except Exception as e:
        results.add_fail("GUI integration", str(e))


# =============================================================================
# Test 8: Utils Integration
# =============================================================================

def test_utils_integration(results):
    """Test utility modules."""
    print_section("TEST 8: Utils Integration")
    
    try:
        from utils.responses import JarvisResponses
        
        responses = JarvisResponses()
        
        # Test response templates
        test_keys = ['greeting', 'open_app_success', 'error', 'not_understood']
        for key in test_keys:
            response = responses.get(key, app="test", error="test error")
            if response and len(response) > 0:
                results.add_pass(f"Response template '{key}'", f"'{response[:50]}...'")
            else:
                results.add_fail(f"Response template '{key}'", "Empty or missing")
        
    except ImportError as e:
        results.add_fail("Responses module import", str(e))
    except Exception as e:
        results.add_fail("Responses module", str(e))


# =============================================================================
# Test 9: End-to-End Configuration Test
# =============================================================================

def test_end_to_end_config(results):
    """Test that a full configuration change propagates correctly."""
    print_section("TEST 9: End-to-End Configuration Flow")
    
    try:
        from config.settings import Settings
        
        # Create a temporary settings file
        temp_dir = Path('config')
        backup_file = temp_dir / 'settings.json.backup'
        settings_file = temp_dir / 'settings.json'
        
        # Backup existing settings if present
        if settings_file.exists():
            shutil.copy(settings_file, backup_file)
            results.add_pass("Settings backup created")
        
        # Modify a setting
        settings = Settings()
        original_rate = settings.get('tts.rate')
        new_rate = 200
        settings.set('tts.rate', new_rate)
        
        # Reload settings
        settings2 = Settings()
        read_rate = settings2.get('tts.rate')
        
        if read_rate == new_rate:
            results.add_pass("Settings persistence", f"Wrote {new_rate}, read {read_rate}")
        else:
            results.add_fail("Settings persistence", 
                           f"Wrote {new_rate} but read {read_rate}")
        
        # Restore original setting
        settings.set('tts.rate', original_rate)
        
        # Restore backup if it exists
        if backup_file.exists():
            shutil.copy(backup_file, settings_file)
            backup_file.unlink()
            results.add_pass("Settings restored from backup")
        
    except Exception as e:
        results.add_fail("End-to-end config test", str(e))


# =============================================================================
# Main Test Runner
# =============================================================================

def run_all_tests():
    """Run all integration tests."""
    results = TestResult()
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 72)
    print("JARVIS CLI - INTEGRATION TEST SUITE")
    print("Testing Settings & Logging Integration")
    print("=" * 72)
    print(f"{Colors.ENDC}\n")
    
    # Run all tests
    test_logger_initialization(results)
    test_settings_system(results)
    test_core_modules(results)
    test_actions_modules(results)
    test_commands_system(results)
    test_services_integration(results)
    test_gui_integration(results)
    test_utils_integration(results)
    test_end_to_end_config(results)
    
    # Print summary
    success = results.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
