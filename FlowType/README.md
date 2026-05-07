# FlowType

**Offline, local-first voice-to-text dictation for Windows.**

Press a global hotkey from any app → speak → transcribed text appears in your focused window. No cloud. No accounts. No telemetry.

---

## Features

| | |
|---|---|
| 🎙 Global hotkey | Works system-wide from any application |
| ⚡ Toggle + Push-to-talk | Two recording modes |
| 🧠 Local AI | faster-whisper runs fully on-device |
| 🔴 Floating indicator | Minimal always-on-top recording dot |
| 📋 Auto-paste | Text injected directly into focused window |
| 🔕 Offline-first | Zero network traffic |
| 🖥 System tray | Minimal background footprint |

---

## Requirements

- **Windows 10/11** (primary target)
- **Python 3.10+** — [python.org](https://python.org)
- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **~500 MB disk** for the `base` Whisper model

---

## Installation

```powershell
# 1. Clone the repository
git clone https://github.com/yourname/FlowType.git
cd FlowType

# 2. Run one-command setup (creates venv, installs all deps)
.\scripts\setup.ps1
```

The setup script will:
- Verify Python 3.10+ is installed
- Create `backend/.venv` and install Python packages
- Run `npm install` in `frontend/`
- Generate tray icon PNGs

---

## Running (Development)

```powershell
.\scripts\run_dev.ps1
```

The app starts minimized to the system tray. Look for the ◉ icon.

**Default hotkey:** `Ctrl+Space` (toggle mode)

---

## Usage

1. Click into any text field (browser, editor, Notepad, chat app…)
2. Press `Ctrl+Space` — the red dot appears
3. Speak naturally
4. Press `Ctrl+Space` again — transcription runs
5. Text is pasted into your cursor position

---

## Settings

Right-click the tray icon → **Settings**, or double-click the tray icon.

| Setting | Description |
|---------|-------------|
| **Microphone** | Select input device or use system default |
| **Mode** | Toggle (press/press) or Push-to-Talk (hold/release) |
| **Hotkey** | Click "Change" and press any key combination |
| **Model** | `tiny` (fast), `base` (balanced), `small` (accurate) |
| **Language** | Auto-detect or lock to a specific language |
| **Paste delay** | Increase if text pastes into wrong window |
| **Audio feedback** | Subtle start/stop/done sounds |
| **Launch at startup** | Auto-start with Windows |

---

## Project Structure

```
FlowType/
├── backend/                # Python process (audio, AI, hotkeys, paste)
│   ├── main.py             # IPC entry point
│   ├── audio/              # Mic recording + device enumeration
│   ├── transcription/      # faster-whisper engine + model manager
│   ├── hotkeys/            # Global hotkey manager
│   ├── paste/              # Clipboard + Ctrl+V injector
│   ├── audio_feedback/     # Programmatic sound generation
│   └── config/             # JSON settings manager
│
├── frontend/               # Electron app
│   ├── main.js             # Main process + Python subprocess management
│   ├── preload.js          # Secure context bridge
│   ├── indicator/          # Floating animated recording dot
│   └── settings/           # Settings UI (HTML + CSS + JS)
│
├── config/
│   └── settings.json       # User configuration (auto-created)
│
└── scripts/
    ├── setup.ps1           # One-command install
    └── run_dev.ps1         # Dev launcher
```

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  Electron Main Process (Node.js)                     │
│  ┌─────────────────┐  ┌──────────────────────────┐  │
│  │ Indicator Window│  │   Settings Window         │  │
│  │ (frameless,     │  │   (560×620, full UI)      │  │
│  │  always-on-top) │  └──────────────────────────┘  │
│  └─────────────────┘                                 │
│            │  IPC (ipcMain/ipcRenderer)              │
│  ┌─────────┴──────────────────────────────────────┐  │
│  │         System Tray + Window Manager           │  │
│  └──────────────┬─────────────────────────────────┘  │
│                 │  stdin/stdout JSON-Lines            │
└─────────────────┼────────────────────────────────────┘
                  │
┌─────────────────┴────────────────────────────────────┐
│  Python Backend Process                              │
│  ┌────────────┐ ┌───────────┐ ┌──────────────────┐  │
│  │ Hotkey Mgr │ │ Recorder  │ │ Whisper Engine   │  │
│  │ (keyboard) │ │(sounddev.)│ │ (faster-whisper) │  │
│  └────────────┘ └───────────┘ └──────────────────┘  │
│  ┌────────────┐ ┌───────────┐ ┌──────────────────┐  │
│  │ Paste Inj. │ │  Sounds   │ │ Config Manager   │  │
│  │(pyperclip) │ │ (numpy)   │ │ (JSON)           │  │
│  └────────────┘ └───────────┘ └──────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## IPC Protocol (Python ↔ Electron)

JSON-Lines over stdin/stdout.

**Commands (Electron → Python):**
```json
{"cmd": "start_recording"}
{"cmd": "stop_recording"}
{"cmd": "get_devices"}
{"cmd": "get_settings"}
{"cmd": "save_settings", "data": {...}}
{"cmd": "get_models"}
{"cmd": "quit"}
```

**Events (Python → Electron):**
```json
{"event": "ready", "settings": {...}}
{"event": "recording_started"}
{"event": "recording_stopped"}
{"event": "transcription_started"}
{"event": "transcription_done", "text": "Hello world"}
{"event": "error", "message": "..."}
{"event": "devices", "devices": [...], "default_index": 0}
{"event": "models", "models": [...]}
```

---

## Models

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny`  | 75 MB  | ~0.3s | Basic |
| `base`  | 145 MB | ~0.6s | Good (**recommended**) |
| `small` | 465 MB | ~1.5s | High |

Models are downloaded on first use to `models/` inside the project directory.

---

## Performance

- **Idle CPU:** <1% (Electron + Python sleeping in IPC loop)
- **Recording:** Negligible (sounddevice streams directly to buffer)
- **Transcription latency:** ~0.5–1.5s depending on model and speech length
- **RAM:** ~150–300 MB with `base` model loaded

---

## Future Roadmap

- [ ] Local LLM cleanup/rewrite with Gemma
- [ ] Streaming dictation (word-by-word output)
- [ ] Voice commands ("delete last sentence", "new paragraph")
- [ ] Multi-language per-session switching
- [ ] History panel with past transcriptions
- [ ] Custom vocabulary / prompt injection
- [ ] macOS and Linux support

---

## License

MIT
