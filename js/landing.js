
function validatePizzeriaName(name) {
    if (!name) return { valid: true };
    if (/^\d+$/.test(name)) {
        return { valid: false, message: 'Název pizzerie nemůže obsahovat jen čísla.' };
    }
    return { valid: true };
}

function startGame() {
    const name = el.pizzeriaNameInput.value.trim();
    const validation = validatePizzeriaName(name);
    if (!validation.valid) {
        alert(validation.message);
        el.pizzeriaNameInput.focus();
        return;
    }

    gs = { pizzeriaName: name || 'Moje Pizzerie', money: 0, totalEarned: 0, clickValue: 1, upgrades: {}, lastSave: Date.now() };
    el.landingScreen.classList.remove('active');
    el.gameScreen.classList.add('active');
    initGame();
}

function loadGame() {
    fetch('/api/save').then(r => r.json()).then(saved => {
        if (!saved) return;
        gs = { ...gs, ...saved };
        if (!gs.upgrades) gs.upgrades = {};
        if (/^\d+$/.test(gs.pizzeriaName)) gs.pizzeriaName = 'Moje Pizzerie';
        el.pizzeriaNameInput.value = gs.pizzeriaName;
        el.landingScreen.classList.remove('active');
        el.gameScreen.classList.add('active');
        initGame();
    }).catch(() => {});
}
