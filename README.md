# 🍕 Pizza Clicker

Klikací hra kde budujete pizzové impérium. Vytvořeno jako školní týmový projekt.

## Spuštění

### Požadavky
- Python 3.x

### Instalace a spuštění
```bash
pip install -r requirements.txt
py server.py
```
Poté otevřete prohlížeč na `http://localhost:5000`.

## Struktura projektu

```
pizzaclicker/
├── index.html              # HTML struktura stránky
├── server.py               # Flask server (API + statické soubory)
├── requirements.txt        # Python závislosti
├── README.md               # Tento soubor
├── save.json               # Uložená hra (vznikne automaticky)
├── leaderboard.json        # Žebříček (vznikne automaticky)
├── css/
│   ├── base.css            # Základní styly a CSS proměnné
│   ├── landing.css         # Přihlašovací obrazovka
│   ├── game.css            # Herní plocha a topbar
│   ├── shop.css            # Obchod s upgrady
│   └── modals.css          # Modální okna (žebříček, reset)
└── js/
    ├── config.js           # Sdílená konfigurace, herní stav, UPGRADES
    ├── landing.js          # Přihlášení a načtení hry
    ├── game.js             # Herní smyčka, klikání, animace
    ├── shop.js             # Obchod a nákup upgradů
    ├── leaderboard.js      # Žebříček
    ├── reset.js            # Reset hry
    └── main.js             # Event listenery, propojení modulů
```

## API endpointy

Základní URL: `http://localhost:5000`

Všechny `POST` endpointy očekávají `Content-Type: application/json`.

### GET /api/save
- Popis: Vrátí uloženou hru.
- Odpověď 200: uložený objekt hry nebo `null`, pokud soubor ještě neexistuje.

### POST /api/save
- Popis: Uloží stav hry.
- Tělo požadavku (JSON objekt):

```json
{
    "pizzeriaName": "Nazev pizzerie",
    "money": 105,
    "totalEarned": 155,
    "clickValue": 2,
    "upgrades": {
        "c1": true
    },
    "lastSave": 1773848901086
}
```

- Odpověď 200:

```json
{ "ok": true }
```

- Odpověď 400: nevalidní JSON nebo nevalidní data.

### DELETE /api/save
- Popis: Smaže uloženou hru (pokud existuje).
- Odpověď 200:

```json
{ "ok": true }
```

### GET /api/leaderboard
- Popis: Vrátí žebříček.
- Odpověď 200: pole záznamů, nebo prázdné pole `[]`, pokud soubor ještě neexistuje.

### POST /api/leaderboard
- Popis: Uloží celý žebříček.
- Tělo požadavku (JSON pole, max. 10 položek):

```json
[
    {
        "name": "kastani",
        "pps": 0,
        "total": 121
    }
]
```

- Odpověď 200:

```json
{ "ok": true }
```

- Odpověď 400: nevalidní JSON nebo nevalidní data.

### Chybové odpovědi API
- 400 Bad Request: nevalidní vstup (špatný formát, chybějící pole, neznámá pole, špatné typy, ne-JSON request).
- 404 Not Found: neexistující API cesta.
- 500 Internal Server Error: neočekávaná chyba serveru.

Chyby na API vrací JSON ve formátu:

```json
{ "ok": false, "error": "Popis chyby" }
```

## Nasazení na PythonAnywhere

1. Nahrajte všechny soubory na PythonAnywhere (přes Files nebo Git)
2. **Web** → **Add new web app** → **Flask**
3. Jako source file nastavte cestu k `server.py`
4. Klikněte **Reload**

## Autoři

| Část | Soubory |
|------|---------|
| Základ & Přihlášení | `index.html`, `server.py`, `css/base.css`, `css/landing.css`, `js/config.js`, `js/landing.js` |
| Herní smyčka | `css/game.css`, `js/game.js` |
| Obchod & Upgrady | `css/shop.css`, `js/shop.js` |
| Žebříček | `css/modals.css`, `js/leaderboard.js` |
| Reset & Propojení | `js/reset.js`, `js/main.js`, `README.md` |
