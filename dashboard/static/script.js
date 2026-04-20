const socket = io();

// UI Elements
const chatLog = document.getElementById('chat-log');
const statusText = document.getElementById('cyra-status');
const pulseIndicator = document.getElementById('pulse-indicator');
const currentText = document.getElementById('current-text');
const groqBar = document.getElementById('groq-bar');
const groqVal = document.getElementById('groq-val');
const elevenBar = document.getElementById('eleven-bar');
const elevenVal = document.getElementById('eleven-val');
const visionVal = document.getElementById('vision-val');
const sttVal = document.getElementById('stt-val');

// Socket Listeners
socket.on('status_update', (data) => {
    statusText.innerText = data.status + (data.status === 'Listening' ? '...' : '~');
    pulseIndicator.className = `status-pulse ${data.status.toLowerCase()}`;
});

socket.on('new_message', (data) => {
    const bubble = document.createElement('div');
    bubble.className = `bubble ${data.role}`;
    bubble.innerText = data.text;
    
    chatLog.appendChild(bubble);
    chatLog.scrollTop = chatLog.scrollHeight;

    if (data.role === 'cyra') {
        currentText.innerText = data.text;
    }
});

socket.on('stats_update', (data) => {
    // Limits
    const GROQ_LIMIT = 500000;
    const ELEVEN_LIMIT = 10000;

    // Update Bars & Percentages
    const groqPerc = Math.min(100, (data.groq_tokens / GROQ_LIMIT) * 100);
    groqBar.style.width = `${groqPerc}%`;
    groqVal.innerText = `${Math.round(groqPerc)}%`;

    const elevenPerc = Math.min(100, (data.elevenlabs_chars / ELEVEN_LIMIT) * 100);
    elevenBar.style.width = `${elevenPerc}%`;
    elevenVal.innerText = `${Math.round(elevenPerc)}%`;

    // Update Counters
    visionVal.innerText = data.vision_requests;
    sttVal.innerText = data.stt_requests;
});

// Auto-clear subtitles after 8s
let subtitleTimeout;
socket.on('new_message', (data) => {
    if (data.role === 'cyra') {
        clearTimeout(subtitleTimeout);
        subtitleTimeout = setTimeout(() => {
            currentText.innerText = "";
        }, 8000);
    }
});
