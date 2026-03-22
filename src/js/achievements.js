const ACHIEVEMENTS = [
    { id:'a1',  icon:'👆', name:'První krok',       desc:'Klikni na pizzu poprvé',               check: () => gs.totalClicks >= 1 },
    { id:'a2',  icon:'💰', name:'Tisícář',           desc:'Vydělej celkem 1 000 €',               check: () => gs.totalEarned >= 1e3 },
    { id:'a3',  icon:'🛒', name:'Nakupuji!',         desc:'Kup svůj první upgrade',               check: () => _achUpgradeCount() >= 1 },
    { id:'a4',  icon:'🖱️', name:'Klikací stroj',    desc:'Dosáhni 1 000 kliků',                  check: () => gs.totalClicks >= 1e3 },
    { id:'a5',  icon:'🍕', name:'Sto tisíc!',        desc:'Vydělej celkem 100 000 €',             check: () => gs.totalEarned >= 1e5 },
    { id:'a6',  icon:'🔧', name:'Technik',           desc:'Kup 5 upgradů',                        check: () => _achUpgradeCount() >= 5 },
    { id:'a7',  icon:'🏭', name:'Průmyslník',        desc:'Vydělej celkem 10 000 000 €',          check: () => gs.totalEarned >= 1e7 },
    { id:'a8',  icon:'⚡', name:'Pizza maniak',       desc:'Dosáhni 10 000 kliků',                 check: () => gs.totalClicks >= 1e4 },
    { id:'a9',  icon:'🌍', name:'Miliardář',         desc:'Vydělej celkem 1 000 000 000 €',       check: () => gs.totalEarned >= 1e9 },
    { id:'a10', icon:'🏆', name:'Sběratel',          desc:'Kup 10 upgradů',                       check: () => _achUpgradeCount() >= 10 },
    { id:'a11', icon:'💎', name:'Klikací legenda',   desc:'Dosáhni 100 000 kliků',                check: () => gs.totalClicks >= 1e5 },
    { id:'a12', icon:'🚀', name:'Biliardář',         desc:'Vydělej celkem 1 000 000 000 000 €',   check: () => gs.totalEarned >= 1e12 },
    { id:'a13', icon:'⚡', name:'Rychlá pizzerie',   desc:'Dosáhni produkce 1 000 €/s',           check: () => calculatePPS() >= 1e3 },
    { id:'a14', icon:'🌟', name:'Perfekcionista',    desc:'Kup všechny upgrady',                  check: () => _achUpgradeCount() >= UPGRADES.length },
    { id:'a15', icon:'👑', name:'Král pizzy',        desc:'Vydělej celkem 1 Q €',                 check: () => gs.totalEarned >= 1e15 },
    { id:'a16', icon:'🔥', name:'Pravidelník',        desc:'Přihlas se 3 dny za sebou',             check: () => gs.streak >= 3 },
    { id:'a17', icon:'🗓️', name:'Věrný zákazník',    desc:'Přihlas se 7 dní za sebou',             check: () => gs.streak >= 7 },
    { id:'a18', icon:'💫', name:'Pizzový fanatik',    desc:'Přihlas se 30 dní za sebou',            check: () => gs.streak >= 30 },
    { id:'a19', icon:'✨', name:'Nový začátek',       desc:'Dosáhni první prestiže',                check: () => (gs.prestigeLevel || 0) >= 1 },
    { id:'a20', icon:'🌠', name:'Veterán',            desc:'Dosáhni prestiže Level 5',              check: () => (gs.prestigeLevel || 0) >= 5 },
    { id:'a21', icon:'🌌', name:'Pizzový bůh',        desc:'Dosáhni prestiže Level 10',             check: () => (gs.prestigeLevel || 0) >= 10 },
];

function _achUpgradeCount() {
    return Object.values(gs.upgrades).filter(Boolean).length;
}

function checkAchievements() {
    ACHIEVEMENTS.forEach(a => {
        if (!gs.earnedAchievements[a.id] && a.check()) {
            gs.earnedAchievements[a.id] = true;
            _showAchievementToast(a);
        }
    });
}

function _showAchievementToast(a) {
    const toast = document.createElement('div');
    toast.className = 'achievement-toast';
    toast.innerHTML =
        `<span class="ach-toast-icon">${a.icon}</span>` +
        `<div class="ach-toast-text">` +
        `<div class="ach-toast-label">Achievement odemčen!</div>` +
        `<div class="ach-toast-name">${a.name}</div>` +
        `</div>`;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

function openAchievements() {
    _renderAchievementsModal();
    el.achievementsModal.classList.add('active');
}

function closeAchievements() {
    el.achievementsModal.classList.remove('active');
}

function _renderAchievementsModal() {
    const earned = ACHIEVEMENTS.filter(a => gs.earnedAchievements[a.id]).length;
    el.achievementsCount.textContent = `${earned} / ${ACHIEVEMENTS.length}`;
    el.achievementsList.innerHTML = '';
    ACHIEVEMENTS.forEach(a => {
        const done = !!gs.earnedAchievements[a.id];
        const div = document.createElement('div');
        div.className = 'ach-item' + (done ? ' ach-done' : '');
        div.innerHTML =
            `<div class="ach-icon">${done ? a.icon : '🔒'}</div>` +
            `<div class="ach-info">` +
            `<div class="ach-name">${a.name}</div>` +
            `<div class="ach-desc">${done ? a.desc : 'Ještě neodemčeno'}</div>` +
            `</div>`;
        el.achievementsList.appendChild(div);
    });
}
