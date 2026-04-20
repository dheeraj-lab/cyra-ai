const socket = io();

// UI Elements
const chatLog = document.getElementById('chat-log');
const statusText = document.getElementById('cyra-status');
const currentText = document.getElementById('current-text');
const groqBar = document.getElementById('groq-bar');
const groqVal = document.getElementById('groq-val');
const elevenBar = document.getElementById('eleven-bar');
const elevenVal = document.getElementById('eleven-val');
const visionVal = document.getElementById('vision-val');
const sttVal = document.getElementById('stt-val');

// Socket Listeners
socket.on('status_update', (data) => {
    statusText.innerText = data.status;
    statusText.className = `status ${data.status.toLowerCase()}`;
});

socket.on('new_message', (data) => {
    const entry = document.createElement('div');
    entry.className = `log-entry ${data.role}`;
    entry.innerHTML = `<strong>${data.role === 'user' ? 'You' : 'Cyra'}:</strong> ${data.text}`;
    
    chatLog.appendChild(entry);
    chatLog.scrollTop = chatLog.scrollHeight;

    if (data.role === 'cyra') {
        currentText.innerText = data.text;
    }
});

socket.on('stats_update', (data) => {
    // Limits
    const GROQ_LIMIT = 500000;
    const ELEVEN_LIMIT = 10000;

    // Update Bars
    const groqPerc = (data.groq_tokens / GROQ_LIMIT) * 100;
    groqBar.style.width = `${Math.min(100, groqPerc)}%`;
    groqVal.innerText = `${data.groq_tokens.toLocaleString()} / 500k`;

    const elevenPerc = (data.elevenlabs_chars / ELEVEN_LIMIT) * 100;
    elevenBar.style.width = `${Math.min(100, elevenPerc)}%`;
    elevenVal.innerText = `${data.elevenlabs_chars.toLocaleString()} / 10k`;

    // Update Counters
    visionVal.innerText = data.vision_requests;
    sttVal.innerText = data.stt_requests;
});

// Auto-clear subtitles after 10s
let subtitleTimeout;
socket.on('new_message', (data) => {
    if (data.role === 'cyra') {
        clearTimeout(subtitleTimeout);
        subtitleTimeout = setTimeout(() => {
            currentText.innerText = "";
        }, 10000);
    }
});
