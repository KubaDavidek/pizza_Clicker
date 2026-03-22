
function renderShop() {
    el.shopList.innerHTML = '';
    UPGRADES.filter(u => u.type === activeTab).forEach(u => {
        const bought = !!gs.upgrades[u.id];
        const unlocked = gs.totalEarned >= u.unlockThreshold;
        const affordable = gs.money >= u.price;
        const item = document.createElement('div');
        item.className = 'shop-item upgrade-item';
        if (!unlocked) {
            item.classList.add('locked');
            item.innerHTML = `<div class="item-icon" style="filter:blur(3px)">❓</div><div class="item-info"><div class="item-name">???</div><div class="item-sub">Odemkni za ${formatNumber(u.unlockThreshold)} € celkem</div></div><div class="item-right"><div class="item-price">🔒</div></div>`;
        } else {
            if (bought) item.classList.add('upgrade-bought');
            else if (affordable) item.classList.add('affordable');
            item.innerHTML = `<div class="item-icon">${u.icon}</div><div class="item-info"><div class="item-name">${u.name}</div><div class="item-sub">${u.desc}</div></div><div class="item-right">${bought ? '<span class="upgrade-done">✓ Koupeno</span>' : `<div class="item-price">${formatNumber(u.price)} €</div><button class="item-buy-btn" data-upgrade-id="${u.id}" ${affordable ? '' : 'disabled'}>Koupit</button>`}</div>`;
        }
        el.shopList.appendChild(item);
    });
}

function buyUpgrade(id) {
    const u = UPGRADES.find(u => u.id === id);
    if (!u || gs.upgrades[id] || gs.money < u.price) return;
    gs.money -= u.price;
    gs.upgrades[id] = true;
    gs.clickValue = 1 + UPGRADES.filter(u => u.type === 'click' && gs.upgrades[u.id]).reduce((s, u) => s + u.bonus, 0);
    updateDisplay();
    renderShop();
    saveGame();
    checkAchievements();
}
