
// Přihlášený uživatel — přístupné ze všech modulů (reset.js, game.js)
let currentUser = null;


// ─── Validace názvu pizzerie ──────────────────────────────────────────────────

function validatePizzeriaName(name) {
    if (!name) return { valid: true };
    if (/^\d+$/.test(name)) {
        return { valid: false, message: 'Název pizzerie nemůže obsahovat jen čísla.' };
    }
    return { valid: true };
}


// ─── Přepínání auth tabů ──────────────────────────────────────────────────────

function switchAuthTab(tab) {
    const isLogin = tab === 'login';
    el.tabLogin.classList.toggle('active', isLogin);
    el.tabRegister.classList.toggle('active', !isLogin);
    el.authSubmitBtn.textContent = isLogin ? 'Přihlásit se →' : 'Registrovat se →';
    clearAuthError();
}


// ─── Chybové hlášky ───────────────────────────────────────────────────────────

function clearAuthError() {
    el.authError.textContent = '';
}

function showAuthError(msg) {
    el.authError.textContent = msg;
}


// ─── Odeslání auth formuláře ──────────────────────────────────────────────────

async function submitAuth() {
    const nickname = el.authNickname.value.trim();
    const password = el.authPassword.value;
    const isLogin  = el.tabLogin.classList.contains('active');

    if (!nickname || !password) {
        showAuthError('Vyplň přezdívku a heslo.');
        return;
    }

    el.authSubmitBtn.disabled = true;
    clearAuthError();

    try {
        const res  = await fetch(isLogin ? '/api/login' : '/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nickname, password }),
        });
        const data = await res.json();

        if (!res.ok) {
            showAuthError(data.error || 'Nastala chyba.');
            return;
        }

        currentUser = data.user;
        await afterAuth();
    } catch {
        showAuthError('Nepodařilo se připojit k serveru.');
    } finally {
        el.authSubmitBtn.disabled = false;
    }
}


// ─── Po přihlášení: zkontroluj save ──────────────────────────────────────────

async function afterAuth() {
    const res   = await fetch('/api/save');
    const saved = await res.json();

    if (saved) {
        gs = { ...gs, ...saved };
        if (!gs.upgrades) gs.upgrades = {};
        if (!gs.earnedAchievements) gs.earnedAchievements = {};
        if (gs.totalClicks === undefined) gs.totalClicks = 0;
        if (gs.streak === undefined) gs.streak = 0;
        if (gs.lastLoginDate === undefined) gs.lastLoginDate = null;
        if (/^\d+$/.test(gs.pizzeriaName)) gs.pizzeriaName = 'Moje Pizzerie';
        if (gs.lastSpinDate === undefined) gs.lastSpinDate = null;
        if (gs.boostType === undefined) gs.boostType = null;
        if (gs.boostMult === undefined) gs.boostMult = 1;
        if (gs.boostEnd === undefined) gs.boostEnd = 0;
        const streakIncreased = _updateStreak();
        el.landingScreen.classList.remove('active');
        el.gameScreen.classList.add('active');
        initGame();
        const offline = applyOfflineEarnings();
        if (offline) {
            updateDisplay();
            saveGame();
            showOfflineToast(offline.earned, offline.awaySecs);
        }
        if (streakIncreased) {
            checkAchievements();
            setTimeout(() => _showStreakToast(gs.streak), offline ? 4500 : 0);
        }
        if (!hasSpunToday()) {
            setTimeout(openSpinWheel, offline ? 6000 : 2000);
        }
    } else {
        showNewGamePanel();
    }
}


// ─── Panel pro novou hru ──────────────────────────────────────────────────────

function showNewGamePanel() {
    el.authPanel.style.display      = 'none';
    el.landingLoading.style.display = 'none';
    el.newGamePanel.style.display   = 'block';
    el.loggedInLabel.textContent    = `Přihlášen jako: ${currentUser.nickname}`;
    el.pizzeriaNameInput.value      = '';
    el.pizzeriaNameInput.focus();
}


// ─── Spuštění nové hry ────────────────────────────────────────────────────────

function startGame() {
    const name       = el.pizzeriaNameInput.value.trim();
    const validation = validatePizzeriaName(name);
    if (!validation.valid) {
        alert(validation.message);
        el.pizzeriaNameInput.focus();
        return;
    }
    gs = {
        pizzeriaName: name || 'Moje Pizzerie',
        money: 0, totalEarned: 0, clickValue: 1,
        upgrades: {}, lastSave: Date.now(),
        earnedAchievements: {}, totalClicks: 0,
        streak: 0, lastLoginDate: null,
        prestigeLevel: 0, lastSpinDate: null,
        boostType: null, boostMult: 1, boostEnd: 0,
    };
    el.landingScreen.classList.remove('active');
    el.gameScreen.classList.add('active');
    initGame();
}


// ─── Denní streak ────────────────────────────────────────────────────────────

function _updateStreak() {
    const today = new Date().toISOString().slice(0, 10);
    if (!gs.lastLoginDate) {
        gs.streak = 1; gs.lastLoginDate = today; return false;
    }
    if (gs.lastLoginDate === today) return false;
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    if (gs.lastLoginDate === yesterday) {
        gs.streak = (gs.streak || 0) + 1;
        gs.lastLoginDate = today;
        return true;
    }
    gs.streak = 1; gs.lastLoginDate = today; return false;
}

function _showStreakToast(streak) {
    const toast = document.createElement('div');
    toast.className = 'achievement-toast streak-toast';
    toast.innerHTML =
        `<span class="ach-toast-icon">🔥</span>` +
        `<div class="ach-toast-text">` +
        `<div class="ach-toast-label">Denní streak!</div>` +
        `<div class="ach-toast-name">${streak} dní v řadě ✨</div>` +
        `</div>`;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 400); }, 4500);
}


// ─── Odhlášení ────────────────────────────────────────────────────────────────

async function logoutUser() {
    await fetch('/api/logout', { method: 'POST' });
    currentUser = null;
    clearInterval(autoSave);
    clearInterval(gameLoop);
    gs = { pizzeriaName: 'Moje Pizzerie', money: 0, totalEarned: 0, clickValue: 1, upgrades: {}, lastSave: Date.now(), earnedAchievements: {}, totalClicks: 0, streak: 0, lastLoginDate: null, prestigeLevel: 0, lastSpinDate: null, boostType: null, boostMult: 1, boostEnd: 0 };
    el.gameScreen.classList.remove('active');
    el.newGamePanel.style.display   = 'none';
    el.authPanel.style.display      = 'block';
    el.landingLoading.style.display = 'none';
    el.authNickname.value = '';
    el.authPassword.value = '';
    clearAuthError();
    switchAuthTab('login');
    el.landingScreen.classList.add('active');
}


// ─── Kontrola session při načtení stránky ────────────────────────────────────

async function initAuth() {
    try {
        const res = await fetch('/api/me');
        if (res.ok) {
            const data = await res.json();
            currentUser = data.user;
            await afterAuth();
            return;
        }
    } catch { /* síťová chyba */ }

    el.landingLoading.style.display = 'none';
    el.authPanel.style.display      = 'block';
}
