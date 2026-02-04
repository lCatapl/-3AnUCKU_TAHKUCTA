// Данные танков WoT (сокращённый каталог для скорости)
const tanksData = {
    "СССР": {
        "10":["Obj. 277","Obj. 705","Obj. 279(e)","ИС-7","Т-62А"],
        "9":["Obj. 257","Obj. 430U","Obj. 140","ИС-4"],
        "8":["ИС-3","Obj. 252F","Т-44-100"],
        "7":["Obj. 252U","ИС","Т-54 лтр."]
    },
    "Германия": {
        "10":["E 100","Maus","VK 72.01(K)"],
        "9":["VK 45.02(P) A","Maus 165/2"],
        "8":["Maus","VK 45.02(P) B"],
        "7":["Tiger II (H)","E 75"]
    },
    "США": {
        "10":["T110E5","T57 Heavy","T110E4"],
        "9":["T30","T110E3","T55A"],
        "8":["T92","M103","M48A5 Patton"],
        "7":["T29","T69"]
    },
    "Франция": {
        "10":["AMX 30 B","AMX 13 105"],
        "9":["AMX 30 Prototype"],
        "8":["AMX 50 120"],
        "7":["AMX 50 100"]
    },
    "Великобритания": {
        "10":["Super Conqueror","FV215b (183)"],
        "9":["FV215b","Conqueror Gun Carriage"],
        "8":["Conqueror"]
    },
    "Китай": {
        "10":["WZ-113G EBR","113"],
        "9":["WZ-113-II"],
        "8":["121","121B"]
    },
    "Япония": {
        "10":["Type 5 Chi-Ri","O-47"],
        "9":["Type 5 Heavy"],
        "8":["O-Ho"]
    }
};

// Инициализация
async function init() {
    loadChat();
    loadNotes();
    loadTanks();
    setupTankControls();
    setInterval(loadChat, 3000);
}

// Парallax танк + выстрелы
function setupTankControls() {
    window.addEventListener('scroll', updateTankPosition);
    window.addEventListener('mousemove', rotateTurret);
    window.addEventListener('click', fire);
}

function updateTankPosition() {
    const scrolled = window.scrollY;
    const tank = document.getElementById('tank');
    tank.style.transform = `translateX(-50%) translateY(${scrolled * 0.4}px)`;
}

function rotateTurret(e) {
    const tankBody = document.getElementById('tank-body');
    const rect = tankBody.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX) * 180 / Math.PI - 90;
    tankBody.style.setProperty('--turret-angle', `${angle}deg`);
}

function fire(e) {
    const tank = document.getElementById('tank-body');
    tank.style.setProperty('--muzzle-flash', '1');
    createExplosion(e.clientX, e.clientY);
    createSmoke(e.clientX, e.clientY);
    setTimeout(() => tank.style.setProperty('--muzzle-flash', '0'), 150);
}

// Эффекты
function createExplosion(x, y) {
    const explosion = document.createElement('div');
    explosion.className = 'explosion';
    explosion.innerHTML = '💥';
    explosion.style.left = x + 'px';
    explosion.style.top = y + 'px';
    document.body.appendChild(explosion);
    setTimeout(() => explosion.remove(), 700);
}

function createSmoke(x, y) {
    for(let i = 0; i < 6; i++) {
        setTimeout(() => {
            const smoke = document.createElement('div');
            smoke.className = 'smoke';
            smoke.style.left = (x + (Math.random()-0.5)*60) + 'px';
            smoke.style.top = (y + (Math.random()-0.5)*40) + 'px';
            document.body.appendChild(smoke);
            setTimeout(() => smoke.remove(), 2500);
        }, i * 120);
    }
}

// Чат
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('chat-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        await fetch('/chat', { method: 'POST', body: formData });
        e.target.reset();
        loadChat();
    });
});

async function loadChat() {
    try {
        const res = await fetch('/chat');
        const data = await res.json();
        const chat = document.getElementById('chat-container');
        chat.innerHTML = data.messages?.map(msg => 
            `<div class="chat-message"><strong>${msg[0]} (${msg[2]}):</strong> ${msg[1]}</div>`
        ).join('') || '<div style="color:#888; text-align:center;">📡 Канал пуст. Напиши первым!</div>';
        chat.scrollTop = chat.scrollHeight;
    } catch(e) {
        document.getElementById('chat-container').innerHTML = '<div style="color:#ff4444;">❌ Ошибка подключения</div>';
    }
}

// Заметки
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('notes-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const title = document.getElementById('note-title').value || 'Без названия';
        formData.append('title', title);
        await fetch('/notes', { method: 'POST', body: formData });
        e.target.reset();
        loadNotes();
    });
});

async function loadNotes() {
    try {
        const res = await fetch('/notes');
        const data = await res.json();
        const notesDiv = document.getElementById('notes-list');
        notesDiv.innerHTML = data.notes?.map(note => 
            `<div class="note"><h4>${note[0]}</h4><p>${note[1]}</p><small>${note[2]}</small></div>`
        ).join('') || '<div style="color:#888;">📝 Заметок пока нет</div>';
    } catch(e) {
        document.getElementById('notes-list').innerHTML = '<div style="color:#ff4444;">❌ Ошибка загрузки</div>';
    }
}

// Каталог танков
function loadTanks() {
    const catalog = document.getElementById('tank-catalog');
    let html = '';
    let totalTanks = 0;
    
    for(const [nation, tiers] of Object.entries(tanksData)) {
        for(const [tier, tankList] of Object.entries(tiers)) {
            tankList.forEach(tankName => {
                html += `
                    <div class="tank-card" data-nation="${nation}" data-tier="${tier}">
                        <h3>${tankName}</h3>
                        <div style="font-size:1.1em; margin-top:8px;">
                            <span style="font-size:1.4em;">${tier}</span> ур.
                        </div>
                    </div>`;
                totalTanks++;
            });
        }
    }
    catalog.innerHTML = html;
    document.getElementById('filter-status').textContent = `Загружено ${totalTanks} танков`;
    
    // Фильтры
    document.getElementById('nation-filter').addEventListener('change', filterTanks);
    document.getElementById('tier-filter').addEventListener('change', filterTanks);
}

function filterTanks() {
    const nation = document.getElementById('nation-filter').value;
    const tier = document.getElementById('tier-filter').value;
    const cards = document.querySelectorAll('.tank-card');
    let visible = 0;
    
    cards.forEach(card => {
        const show = (!nation || card.dataset.nation === nation) && 
                   (!tier || card.dataset.tier === tier);
        card.style.display = show ? 'block' : 'none';
        if(show) visible++;
    });
    
    document.getElementById('filter-status').textContent = 
        visible ? `Найдено: ${visible} танков` : 'Танки не найдены';
}

function clearFilters() {
    document.getElementById('nation-filter').value = '';
    document.getElementById('tier-filter').value = '';
    document.querySelectorAll('.tank-card').forEach(card => card.style.display = 'block');
    document.getElementById('filter-status').textContent = 'Все фильтры сброшены';
}

// Автозапуск
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
// Бой 1v1
async function startBattle() {
    const tankSelect = document.getElementById('battle-tank');
    const resultDiv = document.getElementById('battle-result');
    const statsDiv = document.getElementById('battle-stats');
    
    const playerTank = tankSelect.value;
    
    // Анимация "загрузка"
    resultDiv.innerHTML = '🎯 Наводимся... <span id="loading-dots">...</span>';
    statsDiv.innerHTML = '';
    
    const dots = document.getElementById('loading-dots');
    let dotCount = 0;
    const dotInterval = setInterval(() => {
        dots.textContent = '.'.repeat(++dotCount % 4);
    }, 300);
    
    try {
        const response = await fetch('/battle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({tank: playerTank})
        });
        
        clearInterval(dotInterval);
        const data = await response.json();
        
        resultDiv.innerHTML = `
            <div style="font-size: 24px; margin-bottom: 10px;">${data.result}</div>
            <div style="color: #ffd700; font-size: 20px;">+${data.reward} очков!</div>
        `;
        resultDiv.style.borderLeftColor = data.reward >= 250 ? '#44ff44' : '#ffaa44';
        
        statsDiv.innerHTML = `
            Твой танк: ${playerTank} | Бот: ${data.bot_tank}<br>
            Награда: ${data.reward} очков → Новое звание через релоад чата!
        `;
        
        // Звук победы (визуальный)
        createExplosion(window.innerWidth / 2, window.innerHeight / 2);
        
    } catch(e) {
        clearInterval(dotInterval);
        resultDiv.innerHTML = '❌ Ошибка сервера. Попробуй ещё раз!';
        resultDiv.style.borderLeftColor = '#ff4444';
    }
}
