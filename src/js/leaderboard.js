
function openLeaderboard() {
    fetch('/api/leaderboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pps: calculatePPS(), total: gs.totalEarned }),
    })
    .then(() => fetch('/api/leaderboard'))
    .then(r => r.json())
    .then(scores => {
        el.leaderboardBody.innerHTML = scores.map((s, i) =>
            `<tr class="${s.name === gs.pizzeriaName ? 'current-player' : ''}"><td>${i + 1}.</td><td>${escapeHtml(s.name)}</td><td>${formatNumber(s.pps)} €/s</td><td>${formatNumber(Math.floor(s.total))} €</td></tr>`
        ).join('') || '<tr><td colspan="4" style="text-align:center">Žádné záznamy</td></tr>';
        el.leaderboardModal.classList.add('active');
    })
    .catch(() => el.leaderboardModal.classList.add('active'));
}

function closeLeaderboard() {
    el.leaderboardModal.classList.remove('active');
}
