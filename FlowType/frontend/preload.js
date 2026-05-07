/**
 * FlowType — Preload Script
 * Exposes a safe, minimal API to renderer processes via contextBridge.
 */

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("flowtype", {
  // Settings window → main
  saveSettings: (settings) => ipcRenderer.send("save_settings", settings),
  getSettings: () => ipcRenderer.send("get_settings"),
  getDevices: () => ipcRenderer.send("get_devices"),
  getModels: () => ipcRenderer.send("get_models"),
  closeSettings: () => ipcRenderer.send("close_settings"),
  minimizeSettings: () => ipcRenderer.send("minimize_settings"),
  startRecording: () => ipcRenderer.send("start_recording"),
  stopRecording: () => ipcRenderer.send("stop_recording"),

  // Main → renderer listeners
  on: (channel, callback) => {
    const allowed = [
      "set_state",
      "settings_loaded",
      "devices_loaded",
      "models_loaded",
      "transcription_done",
      "audio_level",
    ];
    if (allowed.includes(channel)) {
      ipcRenderer.on(channel, (_, ...args) => callback(...args));
    }
  },

  off: (channel, callback) => {
    ipcRenderer.removeListener(channel, callback);
  },
});
