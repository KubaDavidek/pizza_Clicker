
const SPIN_REWARDS = [
    { label:'5 min produkce',   icon:'💰', color:'#FBBF24', type:'money', ppsMinutes:5 },
    { label:'2× klik (30 min)', icon:'👆', color:'#FB923C', type:'boost', boostType:'click', mult:2, durationMin:30 },
    { label:'30 min produkce',  icon:'💵', color:'#4ADE80', type:'money', ppsMinutes:30 },
    { label:'2× PPS (30 min)',  icon:'⚡', color:'#60A5FA', type:'boost', boostType:'pps',  mult:2, durationMin:30 },
    { label:'2h produkce',      icon:'💎', color:'#C084FC', type:'money', ppsMinutes:120 },
    { label:'3× PPS (15 min)',  icon:'🚀', color:'#F472B6', type:'boost', boostType:'pps',  mult:3, durationMin:15 },
    { label:'8h produkce',      icon:'🏆', color:'#F87171', type:'money', ppsMinutes:480 },
    { label:'2× vše (20 min)',  icon:'✨', color:'#34D399', type:'boost', boostType:'all',  mult:2, durationMin:20 },
];

let _spinAngle = 0;
let _spinning  = false;

function hasSpunToday() {
    const today = new Date().toISOString().slice(0, 10);
    return gs.lastSpinDate === today;
}

function openSpinWheel() {
    _buildWheel();
    _updateSpinUI();
    el.spinModal.classList.add('active');
}

function closeSpinWheel() {
    el.spinModal.classList.remove('active');
}

function _buildWheel() {
    const wheelEl = el.spinWheelEl;
    const stops   = SPIN_REWARDS.map((r, i) => `${r.color} ${i * 45}deg ${(i + 1) * 45}deg`).join(', ');
    wheelEl.style.background  = `conic-gradient(${stops})`;
    wheelEl.style.transition  = 'none';
    wheelEl.style.transform   = `rotate(${_spinAngle}deg)`;
    wheelEl.innerHTML = '';
    SPIN_REWARDS.forEach((r, i) => {
        const icon = document.createElement('div');
        icon.className = 'spin-sector-icon';
        icon.style.setProperty('--deg', `${i * 45 + 22.5}deg`);
        icon.textContent = r.icon;
        wheelEl.appendChild(icon);
    });
    const dot = document.createElement('div');
    dot.className = 'spin-center-dot';
    wheelEl.appendChild(dot);
}

function _updateSpinUI() {
    const spun = hasSpunToday();
    el.spinBtn.disabled    = spun || _spinning;
    el.spinBtn.textContent = spun ? '✓ Zítra znovu!' : 'Točit! 🎡';
    el.spinResult.classList.remove('active');
}

function spin() {
    if (_spinning || hasSpunToday()) return;
    _spinning = true;
    el.spinBtn.disabled = true;

    const winIndex = Math.floor(Math.random() * SPIN_REWARDS.length);
    const jitter   = (Math.random() - 0.5) * 30;
    const target   = winIndex * 45 + 22.5 + jitter;
    const prevMod  = _spinAngle % 360;
    const delta    = (target - prevMod + 360) % 360 || 360;
    _spinAngle     = _spinAngle + 5 * 360 + delta;

    const wheelEl = el.spinWheelEl;
    requestAnimationFrame(() => {
        wheelEl.style.transition = 'transform 4s cubic-bezier(0.17,0.67,0.12,1.0)';
        wheelEl.style.transform  = `rotate(${_spinAngle}deg)`;
    });

    setTimeout(() => {
        _spinning = false;
        gs.lastSpinDate = new Date().toISOString().slice(0, 10);
        const reward = SPIN_REWARDS[winIndex];
        _applyReward(reward);
        _showSpinResult(reward);
        el.spinBtn.disabled    = true;
        el.spinBtn.textContent = '✓ Zítra znovu!';
        updateDisplay();
        checkAchievements();
        saveGame();
    }, 4300);
}

function _applyReward(reward) {
    if (reward.type === 'money') {
        const pps    = calculatePPS();
        const base   = pps > 0 ? pps * reward.ppsMinutes * 60 : 100;
        const amount = Math.max(Math.floor(base), 100);
        gs.money       += amount;
        gs.totalEarned += amount;
        reward._amount  = amount;
    } else {
        gs.boostType = reward.boostType;
        gs.boostMult = reward.mult;
        gs.boostEnd  = Date.now() + reward.durationMin * 60 * 1000;
        reward._amount = null;
    }
}

function _showSpinResult(reward) {
    el.spinResultIcon.textContent = reward.icon;
    el.spinResultName.textContent = reward.label;
    el.spinResultDesc.textContent = reward.type === 'money'
        ? `+${formatNumber(reward._amount)} €`
        : `×${reward.mult} po dobu ${reward.durationMin} minut`;
    el.spinResult.classList.add('active');
}

// ── Boost helpers (used in game.js) ─────────────────────────────────────────

function getClickBoostMult() {
    if (!gs.boostEnd || Date.now() >= gs.boostEnd) return 1;
    return (gs.boostType === 'click' || gs.boostType === 'all') ? (gs.boostMult || 1) : 1;
}

function getPPSBoostMult() {
    if (!gs.boostEnd || Date.now() >= gs.boostEnd) return 1;
    return (gs.boostType === 'pps' || gs.boostType === 'all') ? (gs.boostMult || 1) : 1;
}

function getBoostTimeLeft() {
    if (!gs.boostEnd || Date.now() >= gs.boostEnd) return 0;
    return Math.ceil((gs.boostEnd - Date.now()) / 1000);
}

function _formatBoostTime(secs) {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return m > 0 ? `${m}m ${s < 10 ? '0' + s : s}s` : `${s}s`;
}
