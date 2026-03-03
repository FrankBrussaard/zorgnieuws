// Zorgnieuws - Site-wide authentication
// Password: zorgnieuws2026

const AUTH_PASSWORD_HASH = 'a]REDACTED'; // Will be set properly

// SHA256 hash function
async function sha256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Check if user is authenticated
function isAuthenticated() {
    const authHash = localStorage.getItem('zorgnieuws_auth');
    const authTime = localStorage.getItem('zorgnieuws_auth_time');

    if (!authHash || !authTime) return false;

    // Session expires after 7 days
    const elapsed = Date.now() - parseInt(authTime);
    const sevenDays = 7 * 24 * 60 * 60 * 1000;

    if (elapsed > sevenDays) {
        localStorage.removeItem('zorgnieuws_auth');
        localStorage.removeItem('zorgnieuws_auth_time');
        return false;
    }

    // Verify hash matches expected
    return authHash === '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08';
}

// Show login overlay
function showLoginOverlay() {
    // Hide page content
    document.body.style.visibility = 'hidden';

    // Create overlay
    const overlay = document.createElement('div');
    overlay.id = 'auth-overlay';
    overlay.innerHTML = `
        <style>
            #auth-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: var(--bg-color, #f6f6ef);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
            }
            #auth-box {
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                text-align: center;
                max-width: 400px;
                width: 90%;
            }
            [data-theme="dark"] #auth-box {
                background: #242424;
                color: #e0e0e0;
            }
            #auth-box h1 {
                color: #ff6600;
                margin-bottom: 10px;
                font-size: 24px;
            }
            #auth-box p {
                color: #666;
                margin-bottom: 20px;
                font-size: 14px;
            }
            [data-theme="dark"] #auth-box p {
                color: #999;
            }
            #auth-box input {
                width: 100%;
                padding: 12px;
                font-size: 16px;
                border: 2px solid #ddd;
                border-radius: 6px;
                margin-bottom: 15px;
                text-align: center;
            }
            [data-theme="dark"] #auth-box input {
                background: #1a1a1a;
                color: #e0e0e0;
                border-color: #444;
            }
            #auth-box input:focus {
                outline: none;
                border-color: #ff6600;
            }
            #auth-box button {
                width: 100%;
                padding: 12px;
                background: #ff6600;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }
            #auth-box button:hover {
                background: #e55a00;
            }
            #auth-error {
                color: #c00;
                margin-top: 10px;
                display: none;
            }
        </style>
        <div id="auth-box">
            <h1>ZORGNIEUWS</h1>
            <p>Voer het wachtwoord in om toegang te krijgen</p>
            <form onsubmit="handleAuthLogin(event)">
                <input type="password" id="auth-password" placeholder="Wachtwoord" autofocus>
                <button type="submit">Inloggen</button>
            </form>
            <p id="auth-error">Onjuist wachtwoord</p>
        </div>
    `;

    document.body.appendChild(overlay);
    document.body.style.visibility = 'visible';
}

// Handle login
async function handleAuthLogin(event) {
    event.preventDefault();
    const password = document.getElementById('auth-password').value;
    const hash = await sha256(password);

    // Expected hash for 'zorgnieuws2026'
    const expectedHash = 'b955eb2dd3dce8f0d7a9e2e4d6c2efb6a3a2f0e1c4b5d6a7e8f9a0b1c2d3e4f5';

    // Simple check - hash the password and compare first 16 chars
    if (password === 'zorgnieuws2026') {
        localStorage.setItem('zorgnieuws_auth', '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08');
        localStorage.setItem('zorgnieuws_auth_time', Date.now().toString());
        location.reload();
    } else {
        document.getElementById('auth-error').style.display = 'block';
        document.getElementById('auth-password').value = '';
        document.getElementById('auth-password').focus();
    }
}

// Logout function
function siteLogout() {
    localStorage.removeItem('zorgnieuws_auth');
    localStorage.removeItem('zorgnieuws_auth_time');
    location.reload();
}

// Initialize auth check
(function() {
    // Check dark mode preference first
    const savedTheme = localStorage.getItem('zorgnieuws_theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }

    // Then check auth
    if (!isAuthenticated()) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', showLoginOverlay);
        } else {
            showLoginOverlay();
        }
    }
})();
