# 🍕 Pizza Clicker - Kompletní dokumentace projektu

Pizza Clicker je interaktivní webová hra, kde budujete vlastní pizzové impérium. Projekt vznikl jako školní týmový úkol a postupně se vyvinul do komplexní webové aplikace, která klade důraz nejen na herní mechaniky, ale i na bezpečný backend, optimalizaci a přehlednou architekturu.

---

## 📋 Hlavní funkce a herní mechaniky
- **Základní klikání:** Zisk peněz (hotovosti) klikáním na hlavní pizzu na obrazovce.
- **Obchod (Upgrady):** Dva druhy vylepšení: 
  - *Klikací (`click`):* Zvyšují zisk za každé kliknutí.
  - *Produkční (`pps` - Pizza Per Second):* Generují pasivní příjem každou sekundu.
- **Prestižní systém:** Možnost resetovat pokrok, pokud hráč dosáhne určité hranice (základ 1 miliarda €). Za to hráč získá trvalý násobič (multiplier) svých budoucích zisků. Ostatní statistiky jako achievementy a počty kliknutí zůstávají.
- **Denní bonusy a Streak:** Kolo štěstí pro extra odměny (dočasné boosty, peníze) a systém každodenního přihlašování (streak).
- **Achievementy:** 15+ unikátních ocenění za dosažení herních milníků.
- **Offline produkce:** Hra dále generuje výdělek i když je hráč offline (částečně zpomaleno, max. 8 hodin).
- **Uživatelské účty:** Podpora registrace, loginu, hešování hesel a správy profilů.
- **Globální žebříček:** Zobrazení TOP 10 nejlepších hráčů podle celkového výdělku.

---

## 🏗️ Architektura systému

Projekt využívá **Client-Server architekturu** složenou z:
1. **Frontend (Prezentační vrstva a herní logika):** Napsáno v čistém HTML, CSS a JavaScriptu (Vanilla JS). Klientská strana řeší kompletní herní smyčku s obnovovací frekvencí 100 milisekund (10 ticků za sekundu), dynamické výpočty cen a odměn a particle efekty.
2. **Backend (API a zabezpečení):** Napsáno v Pythonu s využitím frameworku Flask. Komunikuje s frontendem výhradně jako REST API poskytující JSON data (ukládání postupu, auth, žebříčky).
3. **Databáze:** PostgreSQL v produkčním prostředí, nebo SQLite pro lokální vývoj – spravováno přes abstrakční vrstvu SQLAlchemy.

---

## 📂 Detailní struktura souborů a k čemu slouží

```text
pizzaclicker/
├── server.py               # Hlavní vstupní bod backendu (API endpointy, routování statiky, inicializace DB)
├── validation.py           # Bezpečnostní vrstva pro kontrolu vstupů (payload validace pro API)
├── logging_config.py       # Centrální konfigurace pro logování serverových errorů a warningů
├── sql_script.sql          # DDL schéma databáze (obsahuje definice tabulek users, saves, leaderboard)
├── requirements.txt        # Seznam Python závislostí
├── requirements.lock       # Uzamčený stav závislostí pro 100% reprodukovatelné prostředí
├── ChangeLog               # Historie změn rozepsaná do commitů podle autorů
├── CheckList.txt           # Souhrn pro provedené a probíhající úkoly, požadavky a bugfixing
├── README.md               # Kompletní projektová dokumentace
│
├── public/                 # Kořenová složka pro klientovy soubory
│   ├── index.html          # Hlavní prezentační a strukturovací kostra celé aplikace (modaly, layout tabů)
│   
├── src/                    # Zdrojové soubory (styly a skripty, pro API namapováno do /js a /css)
│   ├── css/
│   │   ├── base.css        # Základní paleta, CSS proměnné, resety, typografie (fonts)
│   │   ├── game.css        # Layout herní sekce, animace u pizzy, particle efekty, topbar rozložení
│   │   ├── landing.css     # Design uvítací, registrační a přihlašovací obrazovky (Landing page)
│   │   ├── modals.css      # Univerzální a specifické styly pro vyskakovací okna, tabulky žebříčků
│   │   └── shop.css        # Styly pro obchodní část a jednotlivé položky (kartičky upgradů)
│   │
│   └── js/
│       ├── config.js       # Konstanty, seznam upgradů (ceny, bonusy, thresholds), sdílený herní objekt `gs`
│       ├── main.js         # DOM Event listenery, globální bindování akcí UI (klávesové zkratky, propojení DOMu)
│       ├── game.js         # Srdce hry - herní smyčka (tick interval), offline progres, pps kalkulace, floating čísla
│       ├── landing.js      # Správa autentizace (login, registrace) pomocí fetch do Python API k vrstvě
│       ├── shop.js         # Logika dokupování vylepšení a odečítání peněz
│       ├── achievements.js # Správa odemykání odměn a notifikační toasty pro achievement pop-upy
│       ├── leaderboard.js  # Komunikace a formátování výsledků z backend (/api/leaderboard)
│       ├── prestige.js     # Resetovací část hry na vyšší vrstvu multiplieru (obnova `gs` při zachování prestiže)
│       ├── profile.js      # Profilová karta - statistiky a mazání nebo změna údajů na účtu hráče
│       ├── reset.js        # Úplné vyčištění dat (smazaní progresu z DB)
│       └── spinwheel.js    # Kolo štěstí na získání denních odměn
```

---

## 🔍 Klíčové části kódu a jejich role

### 1. `server.py` (Základní Backend)
Definuje ORM modely: `User`, `Save`, `LeaderboardEntry`.
Spravuje API endpointy:
- **Autentizační routes:** `/api/login`, `/api/register`, `/api/logout` (Založené na hešování hesel přes `werkzeug.security` - `generate_password_hash`).
- **Herní progres:** GET/POST `/api/save` funguje jako cloud save. Veškerá citlivá čísla se z FE hází přes tento endpoint do `extra_data` pod JSON zprávou.
- **Bezpečností limity:** Obsahuje lokální in-memory *Rate-limiting buckets*, kontrolu max 10 pokusů přihlašení IP/min (`_LOGIN_RATE_WINDOW`) pro zamezení Brute-Force útoku a ochranu na nadměrný počet ukládání (`_SAVE_RATE_WINDOW`).

### 2. `validation.py` (Klíč k bezpečnosti)
Veškeré POST requesty nejprve prochází přísnou validací. Zamezuje se ukládání a injekci nebezpečných Payload objektů do hry:
- Přísně validuje Keys, Types, Minima a Maxima čísel, null hodnoty, validuje pole a nedovolí průchod nadbytečných polí (`unknown_keys = set(data.keys()) - ALLOWED_SAVE_KEYS`). Tím zabraňuje Mass Assignment Attacks.
- `validate_nickname()` i `validate_password()` hlídá délkové parametry na stringech.

### 3. `src/js/game.js` (Herní smyčka a Anti-Cheat)
Funkce `handleClick()` je stěžejní. Kontroluje click rate, kdy pomocí deque pattern pole `_clickTimes` omezuje počet kliků hráče na max. 30 CPS (`MAX_CPS = 30`), čímž **eliminuje běžně dostupné AutoClickery**. Spawnuje se zde také částicový vizuální feedback a volá se kalkulace progresu.
Smyčka se ptá backendu přes fetch v pravidelných časových úsecích nastavených v konfiguračním souboru. V modulu je i část kalkulující `applyOfflineEarnings()`.

### 4. Databázový návrh (`sql_script.sql`)
Použito relační tabulkové paradigma s jasným foreign key mapováním.
- **`users`**: spravuje ID a hash logovacího hesla.
- **`saves`**: `user_id` má `UNIQUE` index propojen s postupem v podobě peněz, statistik, ale i JSON bloku uloženého v textových polích `upgrades` a `extra_data`.
- **`leaderboard`**: rychlá referenční tabulka pro vytahování TOP pořadí beze strachu o načítání všech Save files.

---

## 💻 Ukázky klíčového kódu

Pro lepší představu o fungování herních a bezpečnostních mechanismů zde uvádíme ukázky stěžejních částí samotného originálního kódu projektu.

### 1. Herní smyčka a Anti-Autoclicker (`src/js/game.js`)
Frontend efektivně a spravedlivě registruje kliknutí na pizzu. Místo obyčejného přičítání skóre se každý klik zaznamenává do pole s ověřením časových razítek. Pokud hráč přesáhne limit kliknutí (což simulují cheaty a autoclickery), funkce smyčky ho tiše omezí.

```javascript
const _clickTimes = [];
const MAX_CPS = 30;

function handleClick(e) {
    const now = Date.now();
    // Vyčištění pole listu od kliků starších než vteřina
    while (_clickTimes.length && now - _clickTimes[0] > 1000) _clickTimes.shift();
    
    // Ochrana před podvodem: přesáhl-li hráč stanovený limit 30 CPS, ignoruj
    if (_clickTimes.length >= MAX_CPS) return;
    
    _clickTimes.push(now); // Bezpečný validní hook

    const earned = gs.clickValue * getPrestigeMultiplier() * getClickBoostMult();
    gs.money += earned;
    gs.totalEarned += earned;
    gs.totalClicks++;
    
    // Zobrazení padajících mincí na kurzoru a spuštění API ukládání
    spawnFloat(e, earned);
    spawnParticles(e);
    updateDisplay();
    saveGame();
}
```

### 2. Přísná validace API Payloadu (`validation.py`)
Všechny POST a PUT požadavky na server nesmí obsahovat cizí atributy. Zde je příklad validace ukládací struktury ve frameworku Flask. Takto kontrolujeme, že nepoctivý hráč nepošle vlastní atribut upravující peníze ze scamu.

```python
ALLOWED_SAVE_KEYS = {'pizzeriaName', 'money', 'totalEarned', 'clickValue', 'upgrades', 'lastSave', ...}

def validate_save_payload(data):
    if not isinstance(data, dict):
        raise BadRequest('Save data must be a JSON object.')

    # Ochrana proti Mass Assignment Security: Nedovolí zápis neznámých polí klienta
    unknown_keys = set(data.keys()) - ALLOWED_SAVE_KEYS
    if unknown_keys:
        raise BadRequest(f'Unknown save fields: {", ".join(sorted(unknown_keys))}.')

    # Provádění specifické kontroly minim, maxim a délky povolených stringů
    pizzeria_name = validate_name(data.get('pizzeriaName'), 'pizzeriaName')
    money = validate_number(data.get('money'), 'money', minimum=0)
    # ... validace dalších fields ...

    return {
        'pizzeriaName': pizzeria_name,
        'money': money,
        # vracíme 100% bezpečně zkontrolovanou entitu přímo k zapsání k DB modulu
    }
```

### 3. Rate-Limiting na vrstvě Autentizace (`server.py`)
Flask server disponuje interním In-Memory algoritmem, zabraňujícím zlomyslným skriptům ověřovat masivně hesla a hrubou silou je narušit (Brute-Force útok).

```python
_login_buckets = defaultdict(deque)  # Paměť pro historii přihlášení (vázáno na klient IP)
_LOGIN_RATE_LIMIT  = 10              # Maximum 10 odeslaných hesel...
_LOGIN_RATE_WINDOW = 60.0            # ... ve fixním rámci jedné minuty.

def _check_login_rate():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
    now = time.monotonic()
    bucket = _login_buckets[ip]
    cutoff = now - _LOGIN_RATE_WINDOW
    
    # Průběžné uvolňování zámků, jakmile IP odesílatele "vychladne" nad rámec 60s okna
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
        
    # Zamítnutí s HTTP chybou Forbidden do frontendu a zamezení propustnosti loginu
    if len(bucket) >= _LOGIN_RATE_LIMIT:
        raise Forbidden('Příliš mnoho pokusů o přihlášení. Zkus to znovu za minutu.')
        
    bucket.append(now)
```

---

## 🔒 Zabezpečení (Security Implementations)
- **Ověřování (Authentication):** Uživatelská hesla jsou hashována přes PBKDF2 metodiky.
- **Ochrana API:** Zahrnuje *Rate-limiting* pro login formuláře (Brute-Force bariéra) i cloud ukládání. 
- **Ochrana Frontend Inputů:** Implementovány limity proti Auto-Clickingu (omezeno na 30 kliknutí za sekundu na clientu). Server ověřuje všechny modely přes `validation.py`.
- **Cookies:** Session cookie framework má nastaveno `HttpOnly: True` a `Secure: True` s `SameSite: 'Lax'` ochranou pro předcházení typickým vektorům krádeže tokenů nebo **CSRF** (Cross-Site Request Forgery). Bezpečné po nasazení nad HTTPS komunikací.
- **Ochrana před XSS:** Na frontendu se text z inputů ošetřuje escape string metodami pro bezpečný výstup z JSON. Backend navíc vrací čistý validovaný string typ z databáze a neumožňuje uložení payloadů.
- **Ošetření SQL Injections:** Backend postaven na ORM **SQLAlchemy**, kde každá komunikace nad databází využívá bezpečné parametrizované dotazy a brání injekcím do String proměnných. Projekt prošel analýzou proti typickým **OWASP Top 10** vektorům.

---

## 🛠 Instalace a spuštění projektů

### Požadavky
- Python 3.9+
- Pip package manager

### Lokální spuštění
1. Otevřete terminál a nainstalujte povinné balíčky a závislosti:
   ```bash
   pip install -r requirements.txt
   ```
2. Inicializujte databázi a backendový server příkazem:
   ```bash
   py server.py
   ```
   *(Při prvním spuštění dojde automaticky k vygenerování lokální SQLite databáze)*
3. Hra je k dispozici v prohlížeči na adrese:
   **http://localhost:5000**

### Produkční nasazení (Deployment na službě Vercel)
Aplikace je nasazena live pro veřejné hraní.
Projekt je připraven ve své hierarchii k servírování přes WSGI / Vercel Python runtime, přítomný je i konfigurační `vercel.json`. Podmínkou do produkce je nastavení proměnných prostředí `.env` (a příprava remote Postgres DB):
- `DATABASE_URL` = postgres://...
- `SECRET_KEY` = produkční\_kryptografický\_klíč

---

## 📉 API Endpointy (Referenční dokumentace)
Díky GZIP kompresi odpovědí a strukturování přes REST metodiku běží API bleskově.

* `POST /api/register` – Registrace (`nickname`, `password`), vrací 200 s uživatelskými daty + zakládá Session cookie.
* `POST /api/login` – Přihlášení (vrací 401 při špatné dvojici, 200 při úspěchu).
* `POST /api/logout` – Odpojení aktuální Session hráčem.
* `GET /api/me` – Zjištění stavu, koho momentálně zastupuje ověřená Session.
* `GET /api/save` – Replikace aktuálního savu z DB zpět k hráči (Data o stavu konta a upgrade položkách).
* `POST /api/save` – Deserializace z JSON formátu pro uložení herního pokroku. Nutné posílat obohacený extra blok validní datovou sadou přes body parametrii.
* `DELETE /api/save` – Akce resetu rozehrané hry z backendu pro stávajícího uživatele.
* `GET /api/leaderboard` – Kolekce Top 10 profilů (`total`, `name`, `pps`).
* `POST /api/leaderboard` – Update osobního skóre u hráče napojeného na live výsledky.
* `GET /api/stats` – Sumarizovaná public statistika registrovaných a hrajících uzlíků.
* `GET /api/profile` – Zrcadlí public herní detaily připravené pro rendering.
* `POST /api/profile/password` – Umožní měnit heslo (`old_password`, `new_password`).
* `DELETE /api/profile` – Návratný krok bez slitování - mažou se relace, účet a veškerý herní progres z databáze (Cascade operace na Foreign Key).

### Standardní Chybové zprávy u API komunikace
Chyby na API vrací strukturovaný JSON (nikdy nestrukturovaný TraceBack kód serveru!):
`{ "ok": false, "error": "Srozumitelný popis proč příkaz zamítnut" }`
Status kódy:
- `400 Bad Request` | `401 Unauthorized` | `403 Forbidden` (BruteForce Limit) | `404 Not Found` | `409 Conflict` (Obsazené jméno) | `500 Internal Error`

---

## 👨‍💻 Autoři a tým vývojářů
Každému členovi byl přiřazen úkol s jasně danými prioritami:

- **Michal Němec:** Návrhy herního rozlišení (koncept), tabulka Leaderboard systémů, Testovací scénáře a Unit testy na chování hry. Generace SQL Scriptů.
- **Jakub Davídek:** Startovní set-up vrstvy projektu. Systém denního streakování, Achievements okruh, ochrana před Autoclickery (CAP). Nastavení komplexní error loging a User input Validation.
- **Jiří Janoušek:** Jádro herní smyčky včetně Prestige systému s multiplierem a grafika denního spinu (Kolo štěstí). Oprava UI zobrazení pro mobily, databázové spojení, a příprava na Vercel nasazení.
- **David Pivoňka:** Algoritmus nákupních seznamů `shop.js`, zpracování HTTP request responzí (200.. 500 status kognitivko) a backend routing structure.
- **David Čadek:** Security operace nad celou doménou včetně OWASP prověrkou. Tvorba vizuálu Resetu hry. Řešení responzivity stránek (SEO + skóre styly na mobily). Práce s repozitáři na Python Requirements lockách (závislosti), manipulace na profilu hráče v DB a integrace GZIP komprese u API. Plus tvorba a optimalizace tohoto README do ucelené a plně popsané verze.
