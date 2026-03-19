
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
        if (/^\d+$/.test(gs.pizzeriaName)) gs.pizzeriaName = 'Moje Pizzerie';
        el.landingScreen.classList.remove('active');
        el.gameScreen.classList.add('active');
        initGame();
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
    };
    el.landingScreen.classList.remove('active');
    el.gameScreen.classList.add('active');
    initGame();
}


// ─── Odhlášení ────────────────────────────────────────────────────────────────

async function logoutUser() {
    await fetch('/api/logout', { method: 'POST' });
    currentUser = null;
    clearInterval(autoSave);
    clearInterval(gameLoop);
    gs = { pizzeriaName: 'Moje Pizzerie', money: 0, totalEarned: 0, clickValue: 1, upgrades: {}, lastSave: Date.now() };
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
