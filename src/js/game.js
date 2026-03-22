
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
        if (gs.boostEnd > 0 && Date.now() >= gs.boostEnd) {
            gs.boostType = null; gs.boostMult = 1; gs.boostEnd = 0;
        }
        const boostActive = getBoostTimeLeft() > 0;
        const pps = calculatePPS() * getPrestigeMultiplier();
        if (pps > 0) {
            gs.money += pps * CONFIG.TICK_INTERVAL / 1000;
            gs.totalEarned += pps * CONFIG.TICK_INTERVAL / 1000;
        }
        if (pps > 0 || boostActive) updateDisplay();
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

    const earned = gs.clickValue * getPrestigeMultiplier() * getClickBoostMult();
    gs.money += earned;
    gs.totalEarned += earned;
    gs.totalClicks++;
    spawnFloat(e, earned);
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
    const base = UPGRADES.filter(u => u.type === 'pps' && gs.upgrades[u.id]).reduce((s, u) => s + u.flat, 0);
    return base * getPPSBoostMult();
}

function updateDisplay() {
    const mult      = getPrestigeMultiplier();
    const boostLeft = getBoostTimeLeft();
    el.pizzeriaTitle.textContent     = gs.pizzeriaName;
    el.moneyDisplay.textContent      = `${formatNumber(Math.floor(gs.money))} €`;
    el.ppsDisplay.textContent        = `${formatNumber(calculatePPS() * mult)} €/s`;
    el.totalDisplay.textContent      = `${formatNumber(Math.floor(gs.totalEarned))} €`;
    el.clickValueDisplay.textContent = `${formatNumber(gs.clickValue * mult * getClickBoostMult())} €`;
    el.streakDisplay.textContent     = `🔥 ${gs.streak || 0}`;
    el.prestigeDisplay.textContent   = `✨ ${gs.prestigeLevel || 0}`;
    el.prestigeBtn.classList.toggle('prestige-ready', canPrestige());
    el.bonusBtn.classList.toggle('bonus-ready', !hasSpunToday());
    if (boostLeft > 0) {
        const icon = gs.boostType === 'all' ? '✨' : gs.boostType === 'click' ? '👆' : '⚡';
        el.boostDisplay.textContent = `${icon} ×${gs.boostMult} ${_formatBoostTime(boostLeft)}`;
        el.boostStat.style.display  = '';
        document.getElementById('boost-stat-divider').style.display = '';
    } else {
        el.boostStat.style.display = 'none';
        document.getElementById('boost-stat-divider').style.display = 'none';
    }
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
    const now = Date.now();
    const awaySecs = Math.min(Math.max((now - gs.lastSave) / 1000, 0), OFFLINE_MAX_SECS);
    if (awaySecs < 10) return null;

    const basePps = UPGRADES
        .filter(u => u.type === 'pps' && gs.upgrades[u.id])
        .reduce((sum, u) => sum + u.flat, 0) * getPrestigeMultiplier();
    if (basePps <= 0) return null;

    // Pokud byl aktivní PPS/all boost při posledním uložení, dopočítáme jen část,
    // která reálně pokryla dobu offline.
    let boostedSecs = 0;
    const hasPpsBoost = (gs.boostType === 'pps' || gs.boostType === 'all') && (gs.boostMult || 1) > 1;
    if (hasPpsBoost && gs.boostEnd > gs.lastSave) {
        boostedSecs = Math.min(awaySecs, Math.max((gs.boostEnd - gs.lastSave) / 1000, 0));
    }
    const normalSecs = awaySecs - boostedSecs;
    const boostedPps = basePps * (gs.boostMult || 1);

    const earned = Math.floor(((normalSecs * basePps) + (boostedSecs * boostedPps)) * OFFLINE_RATE);
    if (earned <= 0) return null;

    gs.money       += earned;
    gs.totalEarned += earned;
    return { earned, awaySecs, capped: awaySecs >= OFFLINE_MAX_SECS };
}

function showOfflineToast(earned, awaySecs, capped = false) {
    const h = Math.floor(awaySecs / 3600);
    const m = Math.floor((awaySecs % 3600) / 60);
    const s = Math.floor(awaySecs % 60);
    let timeStr = `${s}s`;
    if (m > 0 || h > 0) timeStr = `${m}m ${s}s`;
    if (h > 0) timeStr = `${h}h ${m}m`;
    const capNote = capped ? ' (max 8h)' : '';
    const toast = document.createElement('div');
    toast.className = 'achievement-toast offline-toast';
    toast.innerHTML =
        `<span class="ach-toast-icon">💤</span>` +
        `<div class="ach-toast-text">` +
        `<div class="ach-toast-label">Byl jsi pryč ${timeStr}${capNote}</div>` +
        `<div class="ach-toast-name">+${formatNumber(earned)} €</div>` +
        `</div>`;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}
