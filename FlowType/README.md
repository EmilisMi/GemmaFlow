# ◉ FlowType

**FlowType** is a premium, offline-first voice dictation application for Windows. It combines the ease of a floating "Dynamic Island" style UI with the power of **Faster-Whisper** for high-speed, local transcription.

![FlowType Indicator](https://raw.githubusercontent.com/username/GemmaFlow/main/assets/indicator_preview.png) *(Placeholder: Replace with actual screenshot)*

## ✨ Features

- **Local & Private:** Everything runs on your machine. No data leaves your computer.
- **Dynamic Island UI:** A beautiful, non-obtrusive floating pill that reacts to your voice.
- **Global Hotkey:** Toggle dictation from any application with a customizable shortcut (default `F2`).
- **High Performance:** Powered by `faster-whisper` for near-instant transcription.
- **Apple-Inspired Design:** Clean, minimal, and premium aesthetic in both light and dark modes.

## 🛠 Tech Stack

- **Frontend:** Electron, Vanilla JS, HTML/CSS
- **Backend:** Python 3.10+
- **Inference Engine:** [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2)
- **Audio Logic:** SoundDevice & NumPy

## 🚀 Getting Started

### Prerequisites

- **Python 3.10 or 3.11** (recommended for compatibility)
- **Node.js 18+**
- **Git**

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/username/FlowType.git
   cd FlowType
   ```

2. **Setup the Backend:**
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   cd ..
   ```

3. **Setup the Frontend:**
   ```powershell
   cd frontend
   npm install
   cd ..
   ```

## 💻 Development

To run the application in development mode with hot-reloading and console logging:

```powershell
.\scripts\run_dev.ps1
```

## 📦 Building the Standalone EXE

To package FlowType into a single Windows installer:

1. **Open PowerShell as Administrator** (Required for symlink creation during bundling).
2. **Run the build script:**
   ```powershell
   .\scripts\build_win.ps1
   ```
3. The final installer will be located in the `dist/` directory.

## ⚙️ Configuration

Settings are stored locally in `settings.json`. You can customize:
- **Hotkey:** The global shortcut to trigger recording.
- **Model:** Choose between `tiny`, `base`, `small`, etc. (Trade-off between speed and accuracy).
- **Device:** Select your preferred microphone input.
- **Paste Delay:** Adjust the timing of text injection.

## 📄 License

MIT License - feel free to use and modify for your own projects!
