
function getUnlockCount() {
    return UPGRADES.filter(u => gs.totalEarned >= u.unlockThreshold).length;
}

function initGame() {
    updateDisplay();
    renderShop();
    clearInterval(autoSave);
    clearInterval(gameLoop);
    autoSave = setInterval(saveGame, CONFIG.AUTOSAVE_INTERVAL);
    gameLoop = setInterval(() => {
        const pps = calculatePPS();
        if (pps > 0) {
            gs.money += pps * CONFIG.TICK_INTERVAL / 1000;
            gs.totalEarned += pps * CONFIG.TICK_INTERVAL / 1000;
            updateDisplay();
        }
        const u = getUnlockCount();
        if (u !== lastUnlockCount) { lastUnlockCount = u; renderShop(); }
        checkAchievements();
    }, CONFIG.TICK_INTERVAL);
}

const _clickTimes = [];
const MAX_CPS = 30;

function handleClick(e) {
    const now = Date.now();
    while (_clickTimes.length && now - _clickTimes[0] > 1000) _clickTimes.shift();
    if (_clickTimes.length >= MAX_CPS) return;
    _clickTimes.push(now);

    gs.money += gs.clickValue;
    gs.totalEarned += gs.clickValue;
    gs.totalClicks++;
    spawnFloat(e, gs.clickValue);
    spawnParticles(e);
    const u = getUnlockCount();
    if (u !== lastUnlockCount) { lastUnlockCount = u; renderShop(); }
    updateDisplay();
    checkAchievements();
    saveGame();
}

function spawnFloat(e, value) {
    const div = document.createElement('div');
    div.className = 'float-number';
    div.textContent = `+${formatNumber(value)} €`;
    const r = el.floatContainer.getBoundingClientRect();
    div.style.left = ((e.touches ? e.touches[0].clientX : e.clientX) - r.left + (Math.random() - 0.5) * 50) + 'px';
    div.style.top  = ((e.touches ? e.touches[0].clientY : e.clientY) - r.top) + 'px';
    el.floatContainer.appendChild(div);
    setTimeout(() => div.remove(), 1000);
}

function spawnParticles(e) {
    const colors = ['#f39c12','#e74c3c','#2ecc71','#3498db','#9b59b6'];
    const r = el.floatContainer.getBoundingClientRect();
    const cx = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
    const cy = (e.touches ? e.touches[0].clientY : e.clientY) - r.top;
    for (let i = 0; i < 5; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        const size = Math.random() * 10 + 5;
        const angle = Math.random() * Math.PI * 2;
        const dist = Math.random() * 50 + 30;
        p.style.cssText = `width:${size}px;height:${size}px;background:${colors[Math.random()*5|0]};left:${cx+Math.cos(angle)*dist}px;top:${cy+Math.sin(angle)*dist}px`;
        el.floatContainer.appendChild(p);
        setTimeout(() => p.remove(), 600);
    }
}

function calculatePPS() {
    return UPGRADES.filter(u => u.type === 'pps' && gs.upgrades[u.id]).reduce((s, u) => s + u.flat, 0);
}

function updateDisplay() {
    el.pizzeriaTitle.textContent = gs.pizzeriaName;
    el.moneyDisplay.textContent = `${formatNumber(Math.floor(gs.money))} €`;
    el.ppsDisplay.textContent = `${formatNumber(calculatePPS())} €/s`;
    el.totalDisplay.textContent = `${formatNumber(Math.floor(gs.totalEarned))} €`;
    el.clickValueDisplay.textContent = `${formatNumber(gs.clickValue)} €`;
    el.streakDisplay.textContent = `🔥 ${gs.streak || 0}`;
    document.title = `${formatNumber(Math.floor(gs.money))} € — Pizza Clicker 🍕`;
    el.shopList.querySelectorAll('.item-buy-btn[data-upgrade-id]').forEach(btn => {
        const u = UPGRADES.find(u => u.id === btn.dataset.upgradeId);
        if (u) {
            btn.disabled = gs.money < u.price;
            btn.closest('.shop-item')?.classList.toggle('affordable', gs.money >= u.price);
        }
    });
}

function saveGame() {
    gs.lastSave = Date.now();
    fetch('/api/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(gs) })
        .then(r => { if (r.status === 401) logoutUser(); })
        .catch(() => {});
}

const OFFLINE_RATE     = 0.25;
const OFFLINE_MAX_SECS = 8 * 3600; // max 8 hodin

function applyOfflineEarnings() {
    const pps = calculatePPS();
    if (pps <= 0) return null;
    const awaySecs = Math.min((Date.now() - gs.lastSave) / 1000, OFFLINE_MAX_SECS);
    if (awaySecs < 10) return null;
    const earned = Math.floor(pps * awaySecs * OFFLINE_RATE);
    gs.money       += earned;
    gs.totalEarned += earned;
    return { earned, awaySecs };
}

function showOfflineToast(earned, awaySecs) {
    const h = Math.floor(awaySecs / 3600);
    const m = Math.floor((awaySecs % 3600) / 60);
    const timeStr = h > 0 ? `${h}h ${m}m` : `${m}m`;
    const toast = document.createElement('div');
    toast.className = 'achievement-toast offline-toast';
    toast.innerHTML =
        `<span class="ach-toast-icon">💤</span>` +
        `<div class="ach-toast-text">` +
        `<div class="ach-toast-label">Byl jsi pryč ${timeStr}</div>` +
        `<div class="ach-toast-name">+${formatNumber(earned)} €</div>` +
        `</div>`;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}
