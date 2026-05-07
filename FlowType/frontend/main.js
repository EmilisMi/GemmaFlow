/**
 * FlowType — Electron Main Process
 *
 * Responsibilities:
 *  - Spawn the Python backend subprocess
 *  - Manage the floating indicator BrowserWindow
 *  - Manage the settings BrowserWindow
 *  - Create the system tray
 *  - Route IPC between renderer and Python via stdin/stdout
 */

const { app, BrowserWindow, Tray, Menu, ipcMain, screen, nativeImage } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const readline = require("readline");
const fs = require("fs");

// ------------------------------------------------------------------ //
//  Constants                                                           //
// ------------------------------------------------------------------ //

const isDev = process.argv.includes("--dev");
const PROJECT_ROOT = path.join(__dirname, "..");
const CONFIG_PATH = path.join(PROJECT_ROOT, "config", "settings.json");

// Python backend
const PYTHON_SCRIPT = path.join(PROJECT_ROOT, "backend", "main.py");
// In packaged app, use bundled Python executable
const PYTHON_EXE = process.env.PYTHON_PATH || "python";

// ------------------------------------------------------------------ //
//  State                                                               //
// ------------------------------------------------------------------ //

let tray = null;
let indicatorWin = null;
let settingsWin = null;
let pythonProcess = null;
let isRecording = false;
let appReady = false;

// ------------------------------------------------------------------ //
//  Python Backend                                                      //
// ------------------------------------------------------------------ //

function startPythonBackend() {
  console.log(`[main] Spawning Python: ${PYTHON_EXE} ${PYTHON_SCRIPT}`);

  pythonProcess = spawn(PYTHON_EXE, [PYTHON_SCRIPT], {
    cwd: path.join(PROJECT_ROOT, "backend"),
    env: { ...process.env },
    stdio: ["pipe", "pipe", "pipe"],
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`[python] ${data.toString().trim()}`);
  });

  pythonProcess.on("exit", (code) => {
    console.log(`[main] Python exited with code ${code}`);
    if (appReady) {
      // Attempt restart after a brief delay
      setTimeout(startPythonBackend, 2000);
    }
  });

  // Read JSON-Lines from Python stdout
  const rl = readline.createInterface({ input: pythonProcess.stdout });
  rl.on("line", (line) => {
    try {
      const msg = JSON.parse(line);
      handlePythonEvent(msg);
    } catch (e) {
      console.error(`[main] Bad JSON from Python: ${line}`);
    }
  });
}

function sendToPython(cmd, data = {}) {
  if (!pythonProcess || pythonProcess.exitCode !== null) return;
  const msg = JSON.stringify({ cmd, data }) + "\n";
  pythonProcess.stdin.write(msg);
}

// ------------------------------------------------------------------ //
//  Python Event Handler                                                //
// ------------------------------------------------------------------ //

function handlePythonEvent(msg) {
  const { event, ...payload } = msg;
  console.log(`[python→] ${event}`, payload);

  switch (event) {
    case "ready":
      updateTrayMenu(false);
      break;

    case "recording_started":
      isRecording = true;
      showIndicator();
      updateTrayMenu(true);
      break;

    case "recording_stopped":
      updateIndicator("transcribing");
      break;

    case "transcription_started":
      updateIndicator("transcribing");
      break;

    case "transcription_done":
      isRecording = false;
      hideIndicator();
      updateTrayMenu(false);
      // Forward to settings window if open
      if (settingsWin && !settingsWin.isDestroyed()) {
        settingsWin.webContents.send("transcription_done", payload);
      }
      break;

    case "error":
      isRecording = false;
      hideIndicator();
      updateTrayMenu(false);
      console.error(`[python] Error: ${payload.message}`);
      break;

    case "settings":
    case "settings_saved":
      if (settingsWin && !settingsWin.isDestroyed()) {
        settingsWin.webContents.send("settings_loaded", payload.settings);
      }
      break;

    case "devices":
      if (settingsWin && !settingsWin.isDestroyed()) {
        settingsWin.webContents.send("devices_loaded", payload);
      }
      break;

    case "models":
      if (settingsWin && !settingsWin.isDestroyed()) {
        settingsWin.webContents.send("models_loaded", payload.models);
      }
      break;

    case "shutdown":
      app.quit();
      break;
  }
}

// ------------------------------------------------------------------ //
//  Floating Indicator Window                                           //
// ------------------------------------------------------------------ //

function createIndicatorWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  const winWidth = 240; // Wider for waveform
  const winHeight = 80;

  indicatorWin = new BrowserWindow({
    width: winWidth,
    height: winHeight,
    x: Math.floor((width - winWidth) / 2),
    y: height - winHeight - 40, // Slightly closer to bottom
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    focusable: false,          // CRITICAL: never steals focus
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Force top-most level
  indicatorWin.setAlwaysOnTop(true, 'screen-saver');
  indicatorWin.setVisibleOnAllWorkspaces(true);
  
  // Make it click-through so it doesn't block the screen
  indicatorWin.setIgnoreMouseEvents(true);

  indicatorWin.loadFile(path.join(__dirname, "indicator", "indicator.html"));

  // Note: Removed saved position logic to keep it centered as requested
}

function showIndicator() {
  if (!indicatorWin || indicatorWin.isDestroyed()) return;
  indicatorWin.showInactive();
  indicatorWin.webContents.send("set_state", "recording");
}

function updateIndicator(state) {
  if (!indicatorWin || indicatorWin.isDestroyed() || !indicatorWin.isVisible()) return;
  indicatorWin.webContents.send("set_state", state);
}

function hideIndicator() {
  if (!indicatorWin || indicatorWin.isDestroyed()) return;
  indicatorWin.webContents.send("set_state", "idle");
  setTimeout(() => {
    if (indicatorWin && !indicatorWin.isDestroyed()) {
      indicatorWin.hide();
    }
  }, 400); // brief fade-out delay
}

function loadIndicatorPosition() {
  try {
    const cfg = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
    const pos = cfg.indicator_position;
    if (pos && pos.x !== null && pos.y !== null) return pos;
  } catch (_) {}
  return null;
}

function saveIndicatorPosition(x, y) {
  try {
    const cfg = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
    cfg.indicator_position = { x, y };
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(cfg, null, 2));
  } catch (_) {}
}

// ------------------------------------------------------------------ //
//  Settings Window                                                     //
// ------------------------------------------------------------------ //

function openSettingsWindow() {
  if (settingsWin && !settingsWin.isDestroyed()) {
    settingsWin.focus();
    return;
  }

  settingsWin = new BrowserWindow({
    width: 560,
    height: 620,
    minWidth: 480,
    minHeight: 540,
    title: "FlowType Settings",
    frame: false,
    transparent: false,
    resizable: true,
    skipTaskbar: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  settingsWin.loadFile(path.join(__dirname, "settings", "settings.html"));

  settingsWin.on("closed", () => {
    settingsWin = null;
  });

  if (isDev) {
    settingsWin.webContents.openDevTools({ mode: "detach" });
  }

  // Once loaded, request fresh data from Python
  settingsWin.webContents.on("did-finish-load", () => {
    sendToPython("get_settings");
    sendToPython("get_devices");
    sendToPython("get_models");
  });
}

// ------------------------------------------------------------------ //
//  System Tray                                                         //
// ------------------------------------------------------------------ //

function createTray() {
  const iconPath = path.join(__dirname, "assets", "icons", "tray-idle.png");
  const icon = nativeImage.createFromPath(iconPath);
  tray = new Tray(icon.resize({ width: 16, height: 16 }));
  tray.setToolTip("FlowType — Voice Dictation");
  updateTrayMenu(false);

  tray.on("double-click", openSettingsWindow);
}

function updateTrayMenu(recording) {
  const menu = Menu.buildFromTemplate([
    {
      label: recording ? "⏹  Stop Recording" : "⏺  Start Recording",
      click: () => {
        if (recording) {
          sendToPython("stop_recording");
        } else {
          sendToPython("start_recording");
        }
      },
    },
    { type: "separator" },
    {
      label: "⚙  Settings",
      click: openSettingsWindow,
    },
    { type: "separator" },
    {
      label: "Quit FlowType",
      click: () => {
        sendToPython("quit");
        setTimeout(() => app.quit(), 500);
      },
    },
  ]);

  tray.setContextMenu(menu);

  // Update tray icon to reflect recording state
  const iconName = recording ? "tray-active.png" : "tray-idle.png";
  const iconPath = path.join(__dirname, "assets", "icons", iconName);
  if (fs.existsSync(iconPath)) {
    tray.setImage(
      nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 })
    );
  }
}

// ------------------------------------------------------------------ //
//  IPC from Renderer (Settings UI)                                    //
// ------------------------------------------------------------------ //

ipcMain.on("save_settings", (_, settings) => {
  sendToPython("save_settings", settings);
});

ipcMain.on("get_settings", () => {
  sendToPython("get_settings");
});

ipcMain.on("get_devices", () => {
  sendToPython("get_devices");
});

ipcMain.on("get_models", () => {
  sendToPython("get_models");
});

ipcMain.on("close_settings", () => {
  if (settingsWin && !settingsWin.isDestroyed()) settingsWin.close();
});

ipcMain.on("minimize_settings", () => {
  if (settingsWin && !settingsWin.isDestroyed()) settingsWin.minimize();
});

ipcMain.on("start_recording", () => sendToPython("start_recording"));
ipcMain.on("stop_recording", () => sendToPython("stop_recording"));

// ------------------------------------------------------------------ //
//  App Lifecycle                                                       //
// ------------------------------------------------------------------ //

app.whenReady().then(() => {
  // Hide from dock on macOS
  if (process.platform === "darwin") app.dock?.hide();

  // Ensure config dir exists
  const configDir = path.join(PROJECT_ROOT, "config");
  if (!fs.existsSync(configDir)) fs.mkdirSync(configDir, { recursive: true });

  startPythonBackend();
  createIndicatorWindow();
  createTray();

  appReady = true;
});

app.on("window-all-closed", (e) => {
  // Prevent quit when all windows closed — stay in tray
  e.preventDefault();
});

app.on("before-quit", () => {
  appReady = false;
  if (pythonProcess) {
    sendToPython("quit");
    setTimeout(() => pythonProcess.kill(), 1000);
  }
});
