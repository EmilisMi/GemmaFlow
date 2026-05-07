/**
 * FlowType — Indicator Renderer
 * Listens for state changes from the main process and updates the dot.
 */

// Valid states: "recording" | "transcribing" | "idle"
function setState(state) {
  document.body.className = state;
}

// Listen for state updates from main process
window.flowtype.on("set_state", (state) => {
  setState(state);
});

// Start as idle
setState("idle");
