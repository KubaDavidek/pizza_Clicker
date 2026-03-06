
document.addEventListener('DOMContentLoaded', () => {
    const ids = {
        landingScreen:'landing-screen',    gameScreen:'game-screen',
        pizzeriaNameInput:'pizzeria-name', startBtn:'start-game-btn',
        pizzeriaTitle:'pizzeria-title',    moneyDisplay:'money-display',
        ppsDisplay:'pps-display',          totalDisplay:'total-display',
        clickValueDisplay:'click-value-display',
        pizzaButton:'pizza-button',        floatContainer:'float-container',
        shopList:'shop-list',
        leaderboardBtn:'leaderboard-btn',  leaderboardModal:'leaderboard-modal',
        closeLeaderboard:'close-leaderboard', leaderboardBody:'leaderboard-body',
        resetBtn:'reset-btn',              resetModal:'reset-modal',
        closeReset:'close-reset',          confirmReset:'confirm-reset',
        cancelReset:'cancel-reset'
    };
    Object.entries(ids).forEach(([k, v]) => el[k] = document.getElementById(v));
    el.shopTabs = document.querySelectorAll('.shop-tab');

  
    el.startBtn.addEventListener('click', startGame);
    el.pizzeriaNameInput.addEventListener('keypress', e => e.key === 'Enter' && startGame());

 
    el.pizzaButton.addEventListener('click', handleClick);
    el.pizzaButton.addEventListener('mousedown', () => el.pizzaButton.classList.add('clicked'));
    ['mouseup', 'mouseleave'].forEach(ev => el.pizzaButton.addEventListener(ev, () => el.pizzaButton.classList.remove('clicked')));
    el.pizzaButton.addEventListener('touchstart', e => { e.preventDefault(); el.pizzaButton.classList.add('clicked'); handleClick(e); });
    el.pizzaButton.addEventListener('touchend', () => el.pizzaButton.classList.remove('clicked'));

 
    el.shopTabs.forEach(tab => tab.addEventListener('click', () => {
        activeTab = tab.dataset.tab;
        el.shopTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        renderShop();
    }));
    el.shopList.addEventListener('click', e => {
        const btn = e.target.closest('.item-buy-btn[data-upgrade-id]');
        if (btn && !btn.disabled) buyUpgrade(btn.dataset.upgradeId);
    });

   
    el.leaderboardBtn.addEventListener('click', openLeaderboard);
    el.closeLeaderboard.addEventListener('click', closeLeaderboard);
    el.leaderboardModal.addEventListener('click', e => e.target === el.leaderboardModal && closeLeaderboard());

 
    el.resetBtn.addEventListener('click', () => el.resetModal.classList.add('active'));
    [el.closeReset, el.cancelReset].forEach(b => b.addEventListener('click', () => el.resetModal.classList.remove('active')));
    el.confirmReset.addEventListener('click', resetGame);
    el.resetModal.addEventListener('click', e => e.target === el.resetModal && el.resetModal.classList.remove('active'));

    
    document.addEventListener('keydown', e => {
        if (e.code === 'Space' && el.gameScreen.classList.contains('active')) {
            e.preventDefault();
            handleClick({ clientX: innerWidth / 2, clientY: innerHeight / 2 });
        }
        if (e.code === 'Escape') { closeLeaderboard(); el.resetModal.classList.remove('active'); }
    });

    loadGame();
});
