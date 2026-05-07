/**
 * FlowType — Settings Renderer
 * Handles Apple-style UI logic and IPC communication.
 */

// ------------------------------------------------------------------ //
//  State                                                               //
// ------------------------------------------------------------------ //

let currentSettings = {};
let pendingSettings = {};
let captureMode = false;
let capturedKeys = new Set();

// ------------------------------------------------------------------ //
//  Window Controls                                                     //
// ------------------------------------------------------------------ //

document.getElementById("close-btn").addEventListener("click", () => {
    window.flowtype.closeSettings();
});

document.getElementById("minimize-btn").addEventListener("click", () => {
    window.flowtype.minimizeSettings();
});

// ------------------------------------------------------------------ //
//  Status & UI Helpers                                                 //
// ------------------------------------------------------------------ //

function setStatus(text) {
    const label = document.getElementById("status-text");
    if (label) label.textContent = text;
}

// ------------------------------------------------------------------ //
//  Settings Sync                                                       //
// ------------------------------------------------------------------ //

function applySettings(settings) {
    currentSettings = { ...settings };
    pendingSettings = { ...settings };

    // Hotkey
    const hotkeyBtn = document.getElementById("hotkey-btn");
    hotkeyBtn.textContent = settings.hotkey || "ctrl+space";

    // Mode
    document.getElementById("mode-select").value = settings.mode || "toggle";

    // Feedback
    document.getElementById("feedback-toggle").checked = settings.audio_feedback !== false;

    // Paste Delay
    document.getElementById("paste-delay").value = settings.paste_delay_ms ?? 150;

    // Handle selects (Model and Device populated async)
    if (settings.model) {
        document.getElementById("model-select").value = settings.model;
    }
    if (settings.device_index !== null) {
        document.getElementById("device-select").value = String(settings.device_index);
    }

    setStatus("Ready");
}

// ------------------------------------------------------------------ //
//  Hotkey Capture                                                      //
// ------------------------------------------------------------------ //

const hotkeyBtn = document.getElementById("hotkey-btn");

hotkeyBtn.addEventListener("click", () => {
    if (captureMode) {
        endCapture(false);
    } else {
        startCapture();
    }
});

function startCapture() {
    captureMode = true;
    capturedKeys.clear();
    hotkeyBtn.textContent = "Waiting...";
    hotkeyBtn.classList.add("recording");
    
    document.addEventListener("keydown", onCaptureKeyDown);
    document.addEventListener("keyup", onCaptureKeyUp);
}

function endCapture(save = false) {
    captureMode = false;
    hotkeyBtn.classList.remove("recording");
    document.removeEventListener("keydown", onCaptureKeyDown);
    document.removeEventListener("keyup", onCaptureKeyUp);

    if (save) {
        const combo = buildComboString(capturedKeys);
        if (combo) {
            hotkeyBtn.textContent = combo;
            pendingSettings.hotkey = combo;
        }
    } else {
        hotkeyBtn.textContent = currentSettings.hotkey || "ctrl+space";
    }
    capturedKeys.clear();
}

function onCaptureKeyDown(e) {
    e.preventDefault();
    const key = normalizeKey(e);
    if (key) capturedKeys.add(key);
    hotkeyBtn.textContent = buildComboString(capturedKeys) || "...";
}

function onCaptureKeyUp(e) {
    e.preventDefault();
    if (capturedKeys.size > 0) {
        endCapture(true);
    }
}

function normalizeKey(e) {
    const modMap = { Control: "ctrl", Shift: "shift", Alt: "alt", Meta: "meta" };
    if (modMap[e.key]) return modMap[e.key];
    if (e.key === " ") return "space";
    return e.key.toLowerCase();
}

function buildComboString(keys) {
    const order = ["ctrl", "alt", "shift", "meta"];
    const mods = order.filter(m => keys.has(m));
    const regular = [...keys].filter(k => !order.includes(k));
    return [...mods, ...regular].join("+");
}

// ------------------------------------------------------------------ //
//  Population Helpers                                                  //
// ------------------------------------------------------------------ //

function populateModels(models) {
    const sel = document.getElementById("model-select");
    sel.innerHTML = "";
    models.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m.name;
        opt.textContent = `${m.name.charAt(0).toUpperCase() + m.name.slice(1)} (${m.size_mb}MB)`;
        sel.appendChild(opt);
    });
    if (currentSettings.model) sel.value = currentSettings.model;
}

function populateDevices({ devices }) {
    const sel = document.getElementById("device-select");
    sel.innerHTML = '<option value="">System Default</option>';
    devices.forEach(dev => {
        const opt = document.createElement("option");
        opt.value = String(dev.index);
        opt.textContent = dev.name;
        sel.appendChild(opt);
    });
    if (currentSettings.device_index !== null) {
        sel.value = String(currentSettings.device_index);
    }
}

// ------------------------------------------------------------------ //
//  Event Listeners                                                     //
// ------------------------------------------------------------------ //

document.getElementById("mode-select").addEventListener("change", (e) => {
    pendingSettings.mode = e.target.value;
});

document.getElementById("model-select").addEventListener("change", (e) => {
    pendingSettings.model = e.target.value;
});

document.getElementById("device-select").addEventListener("change", (e) => {
    const val = e.target.value;
    pendingSettings.device_index = val === "" ? null : parseInt(val, 10);
});

document.getElementById("feedback-toggle").addEventListener("change", (e) => {
    pendingSettings.audio_feedback = e.target.checked;
});

document.getElementById("paste-delay").addEventListener("change", (e) => {
    pendingSettings.paste_delay_ms = parseInt(e.target.value, 10);
});

document.getElementById("save-btn").addEventListener("click", () => {
    setStatus("Saving...");
    window.flowtype.saveSettings(pendingSettings);
});

// ------------------------------------------------------------------ //
//  IPC Listeners                                                       //
// ------------------------------------------------------------------ //

window.flowtype.on("settings_loaded", (settings) => {
    applySettings(settings);
});

window.flowtype.on("devices_loaded", (data) => {
    populateDevices(data);
});

window.flowtype.on("models_loaded", (models) => {
    populateModels(models);
});

window.flowtype.on("transcription_done", ({ text }) => {
    setStatus(`Transcribed: "${text.slice(0, 20)}..."`);
    setTimeout(() => setStatus("Ready"), 5000);
});

// ------------------------------------------------------------------ //
//  Initialize                                                          //
// ------------------------------------------------------------------ //

setStatus("Loading...");
window.flowtype.getSettings();
window.flowtype.getDevices();
window.flowtype.getModels();
