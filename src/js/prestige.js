
function canPrestige() {
    return gs.totalEarned >= PRESTIGE_THRESHOLD;
}

function openPrestige() {
    const level   = gs.prestigeLevel || 0;
    const nextMult = 1 + (level + 1) * 0.25;
    const pct     = Math.min(gs.totalEarned / PRESTIGE_THRESHOLD * 100, 100);

    el.prestigeCurrentLevel.textContent  = level;
    el.prestigeNextMult.textContent      = `×${nextMult.toFixed(2)}`;
    el.prestigeThresholdVal.textContent  = formatNumber(PRESTIGE_THRESHOLD) + ' €';
    el.prestigeCurrentEarned.textContent = formatNumber(Math.floor(gs.totalEarned)) + ' €';
    el.prestigeProgressFill.style.width  = pct + '%';
    el.prestigeConfirmBtn.disabled       = !canPrestige();
    el.prestigeNotReady.textContent      = canPrestige()
        ? ''
        : `Potřebuješ ještě ${formatNumber(Math.ceil(PRESTIGE_THRESHOLD - gs.totalEarned))} €`;
    el.prestigeModal.classList.add('active');
}

function closePrestige() {
    el.prestigeModal.classList.remove('active');
}

function doPrestige() {
    if (!canPrestige()) return;
    gs.prestigeLevel = (gs.prestigeLevel || 0) + 1;

    // Reset herního postupu, zachová se prestiž + achievementy + streak + kliky
    gs.money       = 0;
    gs.totalEarned = 0;
    gs.clickValue  = 1;
    gs.upgrades    = {};

    closePrestige();
    updateDisplay();
    renderShop();
    checkAchievements();
    saveGame();
    _showPrestigeToast(gs.prestigeLevel);
}

function _showPrestigeToast(level) {
    const mult  = 1 + level * 0.25;
    const toast = document.createElement('div');
    toast.className = 'achievement-toast prestige-toast';
    toast.innerHTML =
        `<span class="ach-toast-icon">✨</span>` +
        `<div class="ach-toast-text">` +
        `<div class="ach-toast-label">Prestiž Level ${level} aktivována!</div>` +
        `<div class="ach-toast-name">Permanentní ×${mult.toFixed(2)} na všechny příjmy</div>` +
        `</div>`;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}
