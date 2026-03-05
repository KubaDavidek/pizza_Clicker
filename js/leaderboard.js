
function openLeaderboard() {
    const entry = { name: gs.pizzeriaName, pps: calculatePPS(), total: gs.totalEarned };
    fetch('/api/leaderboard').then(r => r.json()).then(scores => {
        const idx = scores.findIndex(s => s.name === gs.pizzeriaName);
        if (idx >= 0) scores[idx] = entry; else scores.push(entry);
        scores = scores.sort((a, b) => b.total - a.total).slice(0, 10);
        fetch('/api/leaderboard', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(scores) });
        el.leaderboardBody.innerHTML = scores.map((s, i) =>
            `<tr class="${s.name === gs.pizzeriaName ? 'current-player' : ''}"><td>${i + 1}.</td><td>${escapeHtml(s.name)}</td><td>${formatNumber(s.pps)} €/s</td><td>${formatNumber(Math.floor(s.total))} €</td></tr>`
        ).join('') || '<tr><td colspan="4" style="text-align:center">Žádné záznamy</td></tr>';
        el.leaderboardModal.classList.add('active');
    });
}

function closeLeaderboard() {
    el.leaderboardModal.classList.remove('active');
}
