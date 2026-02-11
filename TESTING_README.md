# Testing Your Jarvis CLI Installation

This document provides a quick guide to testing your Jarvis CLI setup.

## 🚀 Quick Start

### Option 1: Quick Check (30 seconds)
```bash
python quick_check.py
```
This runs a fast sanity check on all critical components.

**Expected Output:**
```
Jarvis CLI - Quick System Check

✓ Logger Module
✓ Settings System
✓ Speech-to-Text
✓ Text-to-Speech
✓ Command System
✓ Action Modules
✓ LLM Service
✓ Response Templates

Results: 8/8 checks passed
✓ All systems operational!
```

---

### Option 2: Full Integration Tests (2-3 minutes)
```bash
python test_integration.py
```
This runs comprehensive tests validating settings and logging integration.

---

## 📋 What Gets Tested

### Quick Check Tests:
1. ✅ Logger module initializes
2. ✅ Settings system loads
3. ✅ STT module imports
4. ✅ TTS module imports
5. ✅ Command parsing works
6. ✅ Action modules load
7. ✅ LLM service imports
8. ✅ Response templates available

### Full Integration Tests:
1. ✅ Logger initialization (files, handlers)
2. ✅ Settings system (loading, persistence, dot notation)
3. ✅ Core modules integration (STT, TTS with logging)
4. ✅ Action modules integration (apps, browser, search, media)
5. ✅ Commands system (parser, registry, handlers)
6. ✅ LLM service integration (settings, logging, API key)
7. ✅ GUI integration (settings, logging)
8. ✅ Utils integration (responses)
9. ✅ End-to-end configuration flow

---

## 🐛 Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### "Vosk model not found"
Download from: https://alphacephei.com/vosk/models
Extract to: `models/vosk-model-en-us-0.22-lgraph/`

### Tests fail but you don't know why
```bash
# Get detailed information
python test_integration.py > test_results.txt 2>&1
cat test_results.txt
```

---

## 📚 Learn More

For detailed testing procedures, debugging tips, and best practices, see:
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing documentation

---

## ✅ Before Running Jarvis

Always run a quick check after:
- Installing dependencies
- Modifying configuration
- Pulling latest changes
- Updating Python version

```bash
python quick_check.py && python main.py
```

This ensures everything works before starting the application.
