
function resetGame() {
    fetch('/api/save', { method: 'DELETE' });
    clearInterval(autoSave);
    clearInterval(gameLoop);
    gs = { pizzeriaName: 'Moje Pizzerie', money: 0, totalEarned: 0, clickValue: 1, upgrades: {}, lastSave: Date.now(), earnedAchievements: {}, totalClicks: 0 };
    el.resetModal.classList.remove('active');
    el.gameScreen.classList.remove('active');
    el.landingScreen.classList.add('active');
    showNewGamePanel();
}
