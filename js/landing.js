
function startGame() {
    const name = el.pizzeriaNameInput.value.trim();
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
        el.pizzeriaNameInput.value = gs.pizzeriaName;
        el.landingScreen.classList.remove('active');
        el.gameScreen.classList.add('active');
        initGame();
    }).catch(() => {});
}
