// Settings page - prompt editor with password protection
const SETTINGS_PASSWORD_HASH = '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'; // sha256 of 'admin'

// Simple SHA256 hash function
async function sha256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Check if authenticated
function isAuthenticated() {
    const authTime = localStorage.getItem('zorgnieuws_auth_time');
    if (!authTime) return false;
    // Session expires after 1 hour
    const elapsed = Date.now() - parseInt(authTime);
    return elapsed < 3600000;
}

// Show login form or content
async function initSettings() {
    const loginSection = document.getElementById('login-section');
    const settingsSection = document.getElementById('settings-section');

    if (isAuthenticated()) {
        loginSection.style.display = 'none';
        settingsSection.style.display = 'block';
        loadPrompt();
    } else {
        loginSection.style.display = 'block';
        settingsSection.style.display = 'none';
    }
}

// Handle login
async function handleLogin(event) {
    event.preventDefault();
    const password = document.getElementById('password').value;
    const hash = await sha256(password);

    if (hash === SETTINGS_PASSWORD_HASH) {
        localStorage.setItem('zorgnieuws_auth_time', Date.now().toString());
        document.getElementById('login-error').style.display = 'none';
        initSettings();
    } else {
        document.getElementById('login-error').style.display = 'block';
    }
}

// Load prompt from localStorage or default
function loadPrompt() {
    const savedPrompt = localStorage.getItem('zorgnieuws_prompt');
    const promptArea = document.getElementById('prompt-editor');

    if (savedPrompt) {
        promptArea.value = savedPrompt;
    }
    // Default prompt is already in the textarea from HTML
}

// Save prompt
function savePrompt() {
    const promptArea = document.getElementById('prompt-editor');
    localStorage.setItem('zorgnieuws_prompt', promptArea.value);

    const status = document.getElementById('save-status');
    status.textContent = 'Prompt opgeslagen! Let op: de scoring moet opnieuw gedraaid worden om wijzigingen toe te passen.';
    status.className = 'status success';
    status.style.display = 'block';

    setTimeout(() => {
        status.style.display = 'none';
    }, 5000);
}

// Reset to default
function resetPrompt() {
    if (confirm('Weet je zeker dat je de prompt wilt resetten naar de standaard?')) {
        localStorage.removeItem('zorgnieuws_prompt');
        location.reload();
    }
}

// Logout
function logout() {
    localStorage.removeItem('zorgnieuws_auth_time');
    location.reload();
}

// Initialize on load
document.addEventListener('DOMContentLoaded', initSettings);
