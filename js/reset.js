
function resetGame() {
    fetch('/api/save', { method: 'DELETE' });
    gs = { pizzeriaName: 'Moje Pizzerie', money: 0, totalEarned: 0, clickValue: 1, upgrades: {}, lastSave: Date.now() };
    el.resetModal.classList.remove('active');
    el.gameScreen.classList.remove('active');
    el.landingScreen.classList.add('active');
    el.pizzeriaNameInput.value = '';
}
