

const CONFIG = { AUTOSAVE_INTERVAL: 5000, TICK_INTERVAL: 100, STORAGE_KEY: 'pizzaClickerSave' };

const UPGRADES = [
    { id:'c1',  type:'click', icon:'📋', name:'Lepší recept',          price:50,          unlockThreshold:0,          bonus:1,       desc:'+1 € za klik' },
    { id:'c2',  type:'click', icon:'🍅', name:'Tajná omáčka',          price:300,         unlockThreshold:100,        bonus:3,       desc:'+3 € za klik' },
    { id:'c3',  type:'click', icon:'🍞', name:'Speciální těsto',       price:2000,        unlockThreshold:800,        bonus:8,       desc:'+8 € za klik' },
    { id:'c4',  type:'click', icon:'🧑‍🍳', name:'Mistr pizzar',       price:12000,       unlockThreshold:5000,       bonus:25,      desc:'+25 € za klik' },
    { id:'c5',  type:'click', icon:'🤲', name:'Zlaté ruce',            price:80000,       unlockThreshold:30000,      bonus:75,      desc:'+75 € za klik' },
    { id:'c6',  type:'click', icon:'🍕', name:'Perfektní slice',       price:500000,      unlockThreshold:180000,     bonus:250,     desc:'+250 € za klik' },
    { id:'c7',  type:'click', icon:'🔪', name:'Mistrný řez',           price:3000000,     unlockThreshold:1000000,    bonus:800,     desc:'+800 € za klik' },
    { id:'c8',  type:'click', icon:'👨‍🎤', name:'Pizza guru',          price:15000000,    unlockThreshold:5000000,    bonus:3000,    desc:'+3 000 € za klik' },
    { id:'c9',  type:'click', icon:'🌟', name:'Legenda ulice',         price:80000000,    unlockThreshold:25000000,   bonus:10000,   desc:'+10 000 € za klik' },
    { id:'c10', type:'click', icon:'💎', name:'Diamantová pizza',      price:400000000,   unlockThreshold:130000000,  bonus:40000,   desc:'+40 000 € za klik' },
    { id:'c11', type:'click', icon:'🍾', name:'Šampanská kůrka',       price:2000000000,  unlockThreshold:700000000,  bonus:200000,  desc:'+200 000 € za klik' },
    { id:'c12', type:'click', icon:'🌌', name:'Kosmická pizza',        price:15000000000, unlockThreshold:5000000000, bonus:1000000, desc:'+1 M € za klik' },
    { id:'p1',  type:'pps',   icon:'🔥', name:'Rychlejší trouba',      price:500,         unlockThreshold:0,          flat:2,        desc:'+2 €/s' },
    { id:'p2',  type:'pps',   icon:'⚙️', name:'Optimalizace výroby',   price:4000,        unlockThreshold:0,          flat:15,       desc:'+15 €/s' },
    { id:'p3',  type:'pps',   icon:'🏭', name:'Moderní vybavení',      price:30000,       unlockThreshold:10000,      flat:100,      desc:'+100 €/s' },
    { id:'p4',  type:'pps',   icon:'🤖', name:'AI asistent',           price:200000,      unlockThreshold:70000,      flat:600,      desc:'+600 €/s' },
    { id:'p5',  type:'pps',   icon:'🦾', name:'Robotická linka',       price:1500000,     unlockThreshold:500000,     flat:4000,     desc:'+4 000 €/s' },
    { id:'p6',  type:'pps',   icon:'🛸', name:'Kvantová pec',          price:10000000,    unlockThreshold:3000000,    flat:25000,    desc:'+25 000 €/s' },
    { id:'p7',  type:'pps',   icon:'⚡', name:'Turbo ingredience',     price:70000000,    unlockThreshold:20000000,   flat:180000,   desc:'+180 000 €/s' },
    { id:'p8',  type:'pps',   icon:'🧬', name:'Geneticky lepší mouka', price:500000000,   unlockThreshold:150000000,  flat:1200000,  desc:'+1.2 M €/s' },
    { id:'p9',  type:'pps',   icon:'🌍', name:'Globální síť pecí',     price:3000000000,  unlockThreshold:900000000,  flat:8000000,  desc:'+8 M €/s' },
    { id:'p10', type:'pps',   icon:'🚀', name:'Vesmírná pizzerie',     price:20000000000, unlockThreshold:6000000000, flat:60000000, desc:'+60 M €/s' },
];


const PRESTIGE_THRESHOLD = 1e9; // 1 Miliarda € pro první prestiž

let gs = { pizzeriaName: 'Moje Pizzerie', money: 0, totalEarned: 0, clickValue: 1, upgrades: {}, lastSave: Date.now(), earnedAchievements: {}, totalClicks: 0, streak: 0, lastLoginDate: null, prestigeLevel: 0 };

function getPrestigeMultiplier() {
    return 1 + ((gs.prestigeLevel || 0) * 0.25);
}
const el = {};
let activeTab = 'click';
let autoSave, gameLoop, lastUnlockCount = 0;

function formatNumber(n) {
    if (n >= 1e15) return (n / 1e15).toFixed(2) + ' Q';
    if (n >= 1e12) return (n / 1e12).toFixed(2) + ' T';
    if (n >= 1e9)  return (n / 1e9).toFixed(2) + ' B';
    if (n >= 1e6)  return (n / 1e6).toFixed(2) + ' M';
    if (n >= 1e3)  return (n / 1e3).toFixed(2) + ' K';
    return n.toFixed(n % 1 === 0 ? 0 : 1);
}

function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}
