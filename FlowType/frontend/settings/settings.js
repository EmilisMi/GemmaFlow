/**
 * FlowType — Settings Renderer
 * Handles all settings UI interactions and IPC communication.
 */

// ------------------------------------------------------------------ //
//  State                                                               //
// ------------------------------------------------------------------ //

let currentSettings = {};
let pendingSettings = {};
let captureMode = false;
let capturedKeys = new Set();

// ------------------------------------------------------------------ //
//  Navigation                                                          //
// ------------------------------------------------------------------ //

document.querySelectorAll(".nav-item").forEach((btn) => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.section;
    document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".section").forEach((s) => s.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`section-${target}`).classList.add("active");
  });
});

// ------------------------------------------------------------------ //
//  Title bar                                                           //
// ------------------------------------------------------------------ //

document.getElementById("btn-close").addEventListener("click", () => {
  window.flowtype.closeSettings();
});

document.getElementById("btn-minimize").addEventListener("click", () => {
  window.flowtype.minimizeSettings();
});

// ------------------------------------------------------------------ //
//  Status indicator                                                    //
// ------------------------------------------------------------------ //

function setStatus(state, text) {
  const dot = document.getElementById("status-dot");
  const label = document.getElementById("status-text");
  dot.className = "status-dot " + state;
  label.textContent = text;
}

// ------------------------------------------------------------------ //
//  Settings load / render                                              //
// ------------------------------------------------------------------ //

function applySettings(settings) {
  currentSettings = { ...settings };
  pendingSettings = { ...settings };

  // Device select
  const deviceSel = document.getElementById("device-select");
  if (settings.device_index !== null && settings.device_index !== undefined) {
    deviceSel.value = String(settings.device_index);
  } else {
    deviceSel.value = "";
  }

  // Mode radios
  document.querySelectorAll("input[name='mode']").forEach((r) => {
    r.checked = r.value === settings.mode;
  });

  // Hotkey
  document.getElementById("hotkey-keys").textContent = settings.hotkey || "ctrl+space";

  // Language
  const langSel = document.getElementById("lang-select");
  langSel.value = settings.language || "";

  // Toggles
  document.getElementById("toggle-startup").checked = !!settings.launch_at_startup;
  document.getElementById("toggle-sounds").checked = settings.audio_feedback !== false;

  // Paste delay
  const delaySlider = document.getElementById("paste-delay");
  const delay = settings.paste_delay_ms ?? 150;
  delaySlider.value = delay;
  document.getElementById("paste-delay-label").textContent = `${delay}ms`;

  hideSaveBar();
  setStatus("ready", "Ready");
}

function markDirty() {
  showSaveBar();
}

// ------------------------------------------------------------------ //
//  Devices                                                             //
// ------------------------------------------------------------------ //

function populateDevices({ devices, default_index }) {
  const sel = document.getElementById("device-select");
  sel.innerHTML = "";

  const defaultOpt = document.createElement("option");
  defaultOpt.value = "";
  defaultOpt.textContent = "System Default";
  sel.appendChild(defaultOpt);

  devices.forEach((dev) => {
    const opt = document.createElement("option");
    opt.value = String(dev.index);
    opt.textContent = dev.name + (dev.is_default ? " (default)" : "");
    sel.appendChild(opt);
  });

  // Restore saved value
  const saved = currentSettings.device_index;
  sel.value = saved !== null && saved !== undefined ? String(saved) : "";
}

document.getElementById("btn-refresh-devices").addEventListener("click", () => {
  window.flowtype.getDevices();
});

document.getElementById("device-select").addEventListener("change", (e) => {
  const val = e.target.value;
  pendingSettings.device_index = val === "" ? null : parseInt(val, 10);
  markDirty();
});

// ------------------------------------------------------------------ //
//  Mode radios                                                         //
// ------------------------------------------------------------------ //

document.querySelectorAll("input[name='mode']").forEach((r) => {
  r.addEventListener("change", (e) => {
    pendingSettings.mode = e.target.value;
    markDirty();
  });
});

// ------------------------------------------------------------------ //
//  Hotkey capture                                                      //
// ------------------------------------------------------------------ //

const captureOverlay = document.getElementById("capture-overlay");
const captureKeysEl = document.getElementById("capture-keys");
let capturedCombo = "";

document.getElementById("btn-record-hotkey").addEventListener("click", startCapture);
document.getElementById("btn-cancel-capture").addEventListener("click", endCapture);

function startCapture() {
  captureMode = true;
  capturedKeys.clear();
  capturedCombo = "";
  captureKeysEl.textContent = "Waiting…";
  captureOverlay.classList.remove("hidden");
  document.addEventListener("keydown", onCaptureKeyDown);
  document.addEventListener("keyup", onCaptureKeyUp);
}

function endCapture(saveIt = false) {
  captureMode = false;
  captureOverlay.classList.add("hidden");
  document.removeEventListener("keydown", onCaptureKeyDown);
  document.removeEventListener("keyup", onCaptureKeyUp);

  if (saveIt && capturedCombo) {
    document.getElementById("hotkey-keys").textContent = capturedCombo;
    pendingSettings.hotkey = capturedCombo;
    markDirty();
  }
  capturedKeys.clear();
  capturedCombo = "";
}

function onCaptureKeyDown(e) {
  e.preventDefault();
  const key = normalizeKey(e);
  if (key) capturedKeys.add(key);
  captureKeysEl.textContent = buildComboString(capturedKeys) || "…";
}

function onCaptureKeyUp(e) {
  e.preventDefault();
  // When user releases, we lock in the combo
  const combo = buildComboString(capturedKeys);
  if (combo && capturedKeys.size > 0) {
    capturedCombo = combo;
    endCapture(true);
  }
}

function normalizeKey(e) {
  const modMap = {
    Control: "ctrl", Shift: "shift", Alt: "alt", Meta: "meta",
  };
  if (modMap[e.key]) return modMap[e.key];
  if (e.key === " ") return "space";
  return e.key.toLowerCase();
}

function buildComboString(keys) {
  const order = ["ctrl", "alt", "shift", "meta"];
  const mods = order.filter((m) => keys.has(m));
  const regular = [...keys].filter((k) => !order.includes(k));
  return [...mods, ...regular].join("+");
}

// ------------------------------------------------------------------ //
//  Models                                                              //
// ------------------------------------------------------------------ //

function renderModels(models) {
  const container = document.getElementById("model-cards");
  container.innerHTML = "";

  models.forEach((model) => {
    const card = document.createElement("div");
    card.className = "model-card" + (model.name === currentSettings.model ? " selected" : "");
    card.dataset.model = model.name;
    card.innerHTML = `
      <div class="model-left">
        <div class="model-name">${capitalize(model.name)}</div>
        <div class="model-desc">${model.description}</div>
      </div>
      <div class="model-right">
        <div class="model-size">${model.size_mb} MB</div>
        <div class="model-badge ${model.cached ? 'cached' : 'missing'}">
          ${model.cached ? '✓ Cached' : '↓ Download'}
        </div>
      </div>
    `;
    card.addEventListener("click", () => {
      document.querySelectorAll(".model-card").forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      pendingSettings.model = model.name;
      markDirty();
    });
    container.appendChild(card);
  });
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ------------------------------------------------------------------ //
/*  Language                                                            */
// ------------------------------------------------------------------ //

document.getElementById("lang-select").addEventListener("change", (e) => {
  pendingSettings.language = e.target.value || null;
  markDirty();
});

// ------------------------------------------------------------------ //
/*  General toggles                                                     */
// ------------------------------------------------------------------ //

document.getElementById("toggle-startup").addEventListener("change", (e) => {
  pendingSettings.launch_at_startup = e.target.checked;
  markDirty();
});

document.getElementById("toggle-sounds").addEventListener("change", (e) => {
  pendingSettings.audio_feedback = e.target.checked;
  markDirty();
});

document.getElementById("paste-delay").addEventListener("input", (e) => {
  const val = parseInt(e.target.value, 10);
  document.getElementById("paste-delay-label").textContent = `${val}ms`;
  pendingSettings.paste_delay_ms = val;
  markDirty();
});

// ------------------------------------------------------------------ //
/*  Save bar                                                            */
// ------------------------------------------------------------------ //

function showSaveBar() {
  document.getElementById("save-bar").classList.add("visible");
}

function hideSaveBar() {
  document.getElementById("save-bar").classList.remove("visible");
}

document.getElementById("btn-save").addEventListener("click", () => {
  window.flowtype.saveSettings(pendingSettings);
  hideSaveBar();
  setStatus("ready", "Saved");
  setTimeout(() => setStatus("ready", "Ready"), 2000);
});

document.getElementById("btn-discard").addEventListener("click", () => {
  applySettings(currentSettings);
  hideSaveBar();
});

// ------------------------------------------------------------------ //
/*  IPC listeners from main                                             */
// ------------------------------------------------------------------ //

window.flowtype.on("settings_loaded", (settings) => {
  applySettings(settings);
});

window.flowtype.on("devices_loaded", (data) => {
  populateDevices(data);
});

window.flowtype.on("models_loaded", (models) => {
  renderModels(models);
});

window.flowtype.on("transcription_done", ({ text }) => {
  setStatus("ready", `Done: "${text.slice(0, 32)}${text.length > 32 ? "…" : ""}"`);
  setTimeout(() => setStatus("ready", "Ready"), 4000);
});

// ------------------------------------------------------------------ //
/*  Init                                                                */
// ------------------------------------------------------------------ //

setStatus("ready", "Loading…");
window.flowtype.getSettings();
window.flowtype.getDevices();
window.flowtype.getModels();
