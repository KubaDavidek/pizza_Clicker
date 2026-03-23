
// ─── Otevření profilu ───────────────────────────────────────────────────────

async function openProfile() {
    el.profileModal.classList.add('active');
    el.profilePwMsg.textContent = '';
    el.profileOldPw.value = '';
    el.profileNewPw.value = '';

    try {
        const res = await fetch('/api/profile');
        const data = await res.json();
        if (!res.ok) return;

        el.profileNickname.textContent = data.nickname;
        el.profileCreated.textContent = data.created_at
            ? new Date(data.created_at).toLocaleDateString('cs-CZ')
            : '–';
        el.profileTotal.textContent = formatNumber(data.total_earned) + ' €';
        el.profileUpgrades.textContent = data.upgrades_bought + ' / 22';
    } catch {
        el.profileNickname.textContent = '–';
    }
}

function closeProfile() {
    el.profileModal.classList.remove('active');
}


// ─── Změna hesla ───────────────────────────────────────────────────────────

async function changePassword() {
    const oldPw = el.profileOldPw.value;
    const newPw = el.profileNewPw.value;

    if (!oldPw || !newPw) {
        showProfileMsg('Vyplň obě pole.', 'err');
        return;
    }

    el.profileSavePw.disabled = true;
    try {
        const res = await fetch('/api/profile/password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_password: oldPw, new_password: newPw }),
        });
        const data = await res.json();

        if (res.ok) {
            showProfileMsg('Heslo bylo úspěšně změněno. ✓', 'ok');
            el.profileOldPw.value = '';
            el.profileNewPw.value = '';
        } else {
            showProfileMsg(data.error || 'Nastala chyba.', 'err');
        }
    } catch {
        showProfileMsg('Nepodařilo se připojit k serveru.', 'err');
    } finally {
        el.profileSavePw.disabled = false;
    }
}

function showProfileMsg(msg, type) {
    el.profilePwMsg.textContent = msg;
    el.profilePwMsg.className = 'profile-msg ' + type;
}


// ─── Smazání účtu ──────────────────────────────────────────────────────────

async function deleteAccount() {
    const confirmed = confirm(
        'Opravdu chceš trvale smazat svůj účet?\n\nBude smazán tvůj herní postup a záznam v žebříčku. Tato akce je nevratná.'
    );
    if (!confirmed) return;

    try {
        const res = await fetch('/api/profile', { method: 'DELETE' });
        if (res.ok) {
            closeProfile();
            logoutUser();
        }
    } catch {
        alert('Nepodařilo se smazat účet. Zkus to znovu.');
    }
}
