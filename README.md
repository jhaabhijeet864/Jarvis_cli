# Voice Bot - Stream 1: Voice I/O Layer

Jarvis-style voice assistant for Windows.

## Quick Setup

### 1. Create Virtual Environment (recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Download Vosk Model
Download the small English model (~40MB):
```powershell
# PowerShell script to download and extract
$modelUrl = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
$zipPath = "models/vosk-model.zip"
$extractPath = "models"

# Create models folder
New-Item -ItemType Directory -Force -Path models

# Download
Invoke-WebRequest -Uri $modelUrl -OutFile $zipPath

# Extract
Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force

# Cleanup
Remove-Item $zipPath
```

Or manually:
1. Go to https://alphacephei.com/vosk/models
2. Download `vosk-model-small-en-us-0.15.zip`
3. Extract to `models/vosk-model-small-en-us-0.15/`

### 4. Run Tests
```powershell
python test_stream1.py
```

## Project Structure

```
Voice_Bot/
├── core/
│   ├── __init__.py
│   ├── tts.py          # Text-to-Speech (pyttsx3/SAPI5)
│   ├── stt.py          # Speech-to-Text (Vosk)
│   └── hotkey.py       # Global hotkey listener (pynput)
├── models/
│   └── vosk-model-small-en-us-0.15/  # Vosk model (download separately)
├── requirements.txt
├── test_stream1.py     # Stream 1 tests
└── README.md
```

## Modules

### TTS (Text-to-Speech)
```python
from core.tts import TextToSpeech

tts = TextToSpeech(rate=180, volume=1.0)
tts.speak("Hello sir, systems online")      # Blocking
tts.speak_async("Background speech")        # Non-blocking
tts.stop()                                  # Stop speech
```

### STT (Speech-to-Text)
```python
from core.stt import SpeechToText

stt = SpeechToText("models/vosk-model-small-en-us-0.15")
stt.start_listening()
text = stt.get_text(timeout=5)              # Listen for 5 seconds
print(f"You said: {text}")
stt.cleanup()
```

### Hotkey Listener
```python
from core.hotkey import HotkeyListener

def on_press():
    print("F4 pressed!")

hotkey = HotkeyListener()
hotkey.on_hotkey = on_press
hotkey.start()
# ... 
hotkey.stop()
```

## Troubleshooting

### PyAudio Installation Issues
If `pip install pyaudio` fails, install using:
```powershell
pip install pipwin
pipwin install pyaudio
```

### No Sound Output
- Check Windows sound settings
- Try different voices: `tts.list_voices()` and `tts.set_voice(voice_id)`

### Microphone Not Working
- Check microphone permissions in Windows Settings
- Ensure no other app is using the microphone

## Next Streams

- **Stream 2**: Command Router & Intent Parser
- **Stream 3**: Action Handlers (browser, apps, typing)
- **Stream 4**: Main Loop & Integration
