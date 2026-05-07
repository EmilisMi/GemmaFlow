/**
 * FlowType — Indicator Renderer
 * Handles state changes and real-time rolling waveform visualization.
 */

const bars = [];
const NUM_BARS = 24; // A few more bars for a smoother look
let history = new Array(NUM_BARS).fill(0);

// Initialize bar references
window.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.waveform');
    for (let i = 0; i < NUM_BARS; i++) {
        const bar = document.createElement('div');
        bar.className = 'bar';
        container.appendChild(bar);
        bars.push(bar);
    }
});

// Valid states: "recording" | "transcribing" | "idle"
function setState(state) {
    document.body.className = state;
    if (state !== 'recording') {
        resetBars();
    }
}

function resetBars() {
    history.fill(0);
    bars.forEach(bar => {
        bar.style.transform = 'scaleY(1)';
        bar.style.opacity = '0.4';
    });
}

// Listen for state updates from main process
window.flowtype.on("set_state", (state) => {
    setState(state);
});

// Listen for real-time audio levels from backend
window.flowtype.on("audio_level", (level) => {
    if (document.body.classList.contains('recording')) {
        // Shift history left and add new level to the right
        history.shift();
        history.push(level);
        updateBars();
    }
});

function updateBars() {
    // History contains values from 0.0 to 1.0
    bars.forEach((bar, i) => {
        const level = history[i];
        
        // Base scale + sensitivity
        // We add a little bit of "life" even to quiet bars
        const scale = 1 + (level * 12); 
        
        bar.style.transform = `scaleY(${Math.min(10, scale)})`;
        
        // Opacity reflects the intensity
        bar.style.opacity = 0.3 + (level * 0.7);
    });
}

// Start as idle
setState("idle");
