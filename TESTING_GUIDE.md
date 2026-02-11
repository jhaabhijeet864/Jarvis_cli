# 🧪 Jarvis CLI Testing Guide

## Overview
This guide teaches you how to test the Jarvis CLI project to ensure all modules work correctly with the integrated settings and logging systems.

---

## 📚 Testing Levels

### 1. **Integration Testing** (What we're doing now)
Tests how different modules work together:
- Does the settings system load correctly?
- Can all modules access logging?
- Do settings propagate to all components?

### 2. **Unit Testing** (Module-specific)
Tests individual functions in isolation:
- Does `CommandParser.parse()` work correctly?
- Does `Settings.get()` return the right values?

### 3. **System Testing** (End-to-end)
Tests the entire application as a user would:
- Can Jarvis start and recognize speech?
- Do voice commands execute properly?

---

## 🚀 Quick Start: Running Integration Tests

### Step 1: Run the Test Suite

```bash
python test_integration.py
```

**What it does:**
- ✅ Checks if logging system initialized correctly
- ✅ Validates settings system works
- ✅ Tests all modules can import and use logging
- ✅ Verifies LLM service integrates with settings
- ✅ Tests configuration persistence

### Step 2: Interpret the Results

**Output Format:**
```
✓ PASS Test name - Everything works!
✗ FAIL Test name - Something broke
⚠ WARN Test name - Not critical but needs attention
```

**Color Coding:**
- 🟢 Green = Passed
- 🔴 Red = Failed
- 🟡 Yellow = Warning

---

## 📊 What Each Test Checks

### Test 1: Logger Initialization
**Purpose:** Ensures the logging system is set up correctly

**What it checks:**
- ✓ `logs/` directory exists
- ✓ Log files created: `main.log`, `stt.log`, `commands.log`, `llm.log`, `errors.log`
- ✓ Each logger has handlers configured

**How to debug failures:**
```python
# Check if logger module imported correctly
from utils.logger import JarvisLogger

# Check if logs directory exists
import os
print(os.path.exists('logs'))

# Check logger configuration
import logging
logger = logging.getLogger('main')
print(f"Handlers: {logger.handlers}")
```

---

### Test 2: Settings System
**Purpose:** Validates the configuration management system

**What it checks:**
- ✓ Settings class can be instantiated
- ✓ All required sections exist: `audio`, `tts`, `wake_word`, `hotkey`, `gui`, `llm`
- ✓ Dot notation works: `settings.get('tts.rate')`
- ✓ Settings file created at `config/settings.json`
- ✓ JSON is valid

**How to debug failures:**
```python
from config.settings import Settings

# Test basic functionality
settings = Settings()
print(settings.get('tts.rate'))  # Should print 180

# Check what's in settings
print(settings.settings)

# Verify file exists
import json
with open('config/settings.json') as f:
    data = json.load(f)
    print(json.dumps(data, indent=2))
```

---

### Test 3: Core Modules Integration
**Purpose:** Ensures STT and TTS modules use logging

**What it checks:**
- ✓ Modules can be imported
- ✓ Logging is integrated (logger handlers exist)

**How to debug failures:**
```python
# Test STT import
try:
    from core.stt import SpeechToText
    print("✓ STT imported")
except Exception as e:
    print(f"✗ STT import failed: {e}")

# Check if STT uses logging
import logging
stt_logger = logging.getLogger('stt')
print(f"STT logger handlers: {stt_logger.handlers}")
```

---

### Test 4: Actions Modules Integration
**Purpose:** Verifies action modules (apps, browser, search, media) use logging

**What it checks:**
- ✓ All action modules can be imported
- ✓ Each module uses `logging.getLogger()`

**How to debug failures:**
```python
# Test each module
from actions.apps import AppLauncher
from actions.browser import BrowserController
from actions.search import SearchController
from actions.media import MediaController

print("✓ All action modules imported")
```

---

### Test 5: Commands System Integration
**Purpose:** Tests command parsing and handler registration

**What it checks:**
- ✓ CommandParser can parse various commands
- ✓ Command registry has handlers registered
- ✓ Sample commands parse correctly

**How to debug failures:**
```python
from commands.parser import CommandParser
from commands.handlers import registry

# Test parsing
parser = CommandParser()
result = parser.parse("open notepad")
print(f"Intent: {result.intent}, Target: {result.target}")

# Check registry
print(f"Registered handlers: {len(registry)}")
print(f"Handler list: {registry.get_all_intents()}")
```

---

### Test 6: Services Integration (LLM)
**Purpose:** Ensures LLM service integrates with settings and logging

**What it checks:**
- ✓ CodeGenerator can be imported
- ✓ API key is configured (or warning shown)
- ✓ LLM reads settings for model and temperature
- ✓ LLM uses logging

**How to debug failures:**
```python
from services.llm_api import CodeGenerator
from config.settings import Settings
import config

# Check API key
print(f"API Key configured: {config.GOOGLE_API_KEY != 'YOUR_API_KEY_HERE'}")

# Check settings
settings = Settings()
print(f"LLM Model: {settings.get('llm.model')}")
print(f"LLM Temperature: {settings.get('llm.temperature')}")

# Check logging
import logging
llm_logger = logging.getLogger('llm')
print(f"LLM logger handlers: {llm_logger.handlers}")
```

---

### Test 7: GUI Integration
**Purpose:** Verifies GUI uses settings and logging

**What it checks:**
- ✓ Pygame is installed
- ✓ GUI source code uses `settings.get()`
- ✓ GUI source code uses logging

**How to debug failures:**
```python
# Check if pygame installed
try:
    import pygame
    print("✓ Pygame installed")
except ImportError:
    print("✗ Pygame not installed - run: pip install pygame")

# Check GUI source for settings usage
with open('gui.py', 'r') as f:
    content = f.read()
    print(f"Uses settings: {'settings.get' in content}")
    print(f"Uses logging: {'logging.getLogger' in content}")
```

---

### Test 8: Utils Integration
**Purpose:** Tests utility modules like response templates

**What it checks:**
- ✓ JarvisResponses can be imported
- ✓ Response templates return valid text

**How to debug failures:**
```python
from utils.responses import JarvisResponses

responses = JarvisResponses()
print(responses.get('greeting'))
print(responses.get('open_app_success', app='notepad'))
```

---

### Test 9: End-to-End Configuration Flow
**Purpose:** Tests that settings can be modified and persist

**What it checks:**
- ✓ Settings can be written
- ✓ Settings can be read back
- ✓ Changes persist across Settings instances

**How to debug failures:**
```python
from config.settings import Settings

# Write a setting
settings1 = Settings()
settings1.set('tts.rate', 200)

# Read it back with a new instance
settings2 = Settings()
rate = settings2.get('tts.rate')
print(f"Rate after reload: {rate}")  # Should be 200
```

---

## 🔧 Manual Testing Procedures

### Testing Settings Changes

**1. Modify a setting:**
```bash
# Edit config/settings.json
{
  "tts": {
    "rate": 200,  # Change from 180 to 200
    "volume": 0.8
  }
}
```

**2. Run Jarvis and verify:**
- Start the application
- Check if TTS speaks faster (rate increased)
- Check `logs/main.log` for confirmation

**3. Test expected behavior:**
```bash
# Should see in logs:
"Loading Text-to-Speech with rate=200"
```

---

### Testing Logging Output

**1. Run Jarvis normally:**
```bash
python main.py
```

**2. Check log files:**
```bash
# View main application logs
cat logs/main.log

# View speech recognition logs
cat logs/stt.log

# View command processing logs
cat logs/commands.log

# View LLM logs (if code generation used)
cat logs/llm.log

# View errors (should be empty if all is well)
cat logs/errors.log
```

**3. What to look for:**
- ✓ Clear, structured log entries
- ✓ Timestamps on each entry
- ✓ Appropriate log levels (INFO, WARNING, ERROR)
- ✓ No stack traces in logs (unless actual errors occurred)

---

### Testing Module Imports

**Create a quick test script:**

```python
# quick_test.py
print("Testing imports...")

try:
    from config.settings import Settings
    print("✓ Settings")
except Exception as e:
    print(f"✗ Settings: {e}")

try:
    from utils.logger import JarvisLogger
    print("✓ Logger")
except Exception as e:
    print(f"✗ Logger: {e}")

try:
    from core.stt import SpeechToText
    print("✓ STT")
except Exception as e:
    print(f"✗ STT: {e}")

try:
    from core.tts import TextToSpeech
    print("✓ TTS")
except Exception as e:
    print(f"✗ TTS: {e}")

try:
    from services.llm_api import CodeGenerator
    print("✓ LLM")
except Exception as e:
    print(f"✗ LLM: {e}")

print("\nAll critical imports successful!" if all else "Some imports failed!")
```

Run it:
```bash
python quick_test.py
```

---

## 🐛 Common Issues and Solutions

### Issue 1: "Module not found" errors

**Problem:**
```
ImportError: No module named 'vosk'
```

**Solution:**
```bash
pip install -r requirements.txt
```

---

### Issue 2: Settings file not loading

**Problem:**
```
FileNotFoundError: config/settings.json not found
```

**Solution:**
```python
# Settings will auto-create the file on first run
from config.settings import Settings
settings = Settings()  # This creates the file
settings.save()
```

---

### Issue 3: Logs not being written

**Problem:**
- Log files exist but are empty

**Solution:**
```python
# Ensure logger is initialized before importing other modules
from utils.logger import JarvisLogger  # Must be first
import logging

# Then use loggers
logger = logging.getLogger('main')
logger.info("Test message")
```

---

### Issue 4: Vosk model not found

**Problem:**
```
FileNotFoundError: Vosk model not found at: models/vosk-model-en-us-0.22-lgraph
```

**Solution:**
Download the model:
1. Go to: https://alphacephei.com/vosk/models
2. Download: `vosk-model-en-us-0.22-lgraph.zip`
3. Extract to: `models/vosk-model-en-us-0.22-lgraph/`

Or update settings to use smaller model:
```json
{
  "audio": {
    "vosk_model": "models/vosk-model-small-en-us-0.15"
  }
}
```

---

## ✅ Testing Checklist

Before considering your integration complete, verify:

### Settings System
- [ ] `config/settings.json` exists
- [ ] Settings can be modified via `settings.set()`
- [ ] Changes persist after program restart
- [ ] All modules read from settings, not hardcoded values

### Logging System
- [ ] `logs/` directory exists
- [ ] All 5 log files created
- [ ] Log entries have timestamps
- [ ] No `print()` statements in production code
- [ ] Errors logged to `errors.log`

### Module Integration
- [ ] All modules import without errors
- [ ] Each module uses `logging.getLogger()`
- [ ] Settings passed to modules that need them
- [ ] No hardcoded configuration values

### Functionality
- [ ] TTS rate can be changed via settings
- [ ] Wake word can be changed via settings
- [ ] GUI dimensions configurable
- [ ] LLM model and temperature configurable

---

## 📈 Advanced Testing: Performance Monitoring

### Monitor Log File Growth
```bash
# Watch logs in real-time
tail -f logs/main.log

# Check log file sizes
ls -lh logs/
```

### Memory Usage
```python
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

---

## 🎓 Best Practices You've Learned

1. **Centralized Configuration**: All settings in one place
2. **Structured Logging**: Debugging is much easier
3. **Separation of Concerns**: Settings, logging, and business logic separated
4. **Testability**: Integration tests validate everything works together
5. **Maintainability**: Changes to config don't require code changes

---

## 🚀 Next Steps After Testing

Once all tests pass:

1. **Write unit tests** for critical functions
2. **Add continuous integration** (GitHub Actions)
3. **Document configuration options** for users
4. **Create user guide** for customization
5. **Set up automated testing** on every commit

---

## 📝 Testing Reports

After running tests, you can generate a report:

```bash
# Run tests and save output
python test_integration.py > test_report.txt 2>&1

# View the report
cat test_report.txt
```

---

## 🤝 Getting Help

If tests fail and you can't debug:

1. Check the specific test section in this guide
2. Review the error message carefully
3. Check if dependencies are installed
4. Verify file paths are correct
5. Ensure Python version is 3.9+

---

**Happy Testing! 🧪✨**
