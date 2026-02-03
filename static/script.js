// Чат в реальном времени (WebSocket заглушка)
function initChat() {
    const ws = new WebSocket('ws://localhost:5000/chat');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        addMessage(data.username, data.role, data.message);
    };
}

// Автозагрузка записок
async function loadStories(tankFilter = '') {
    const response = await fetch(`/api/stories?tank=${tankFilter}`);
    const data = await response.json();
    displayStories(data.stories);
}

// Модальное окно мута
function showMuteModal(targetId, targetName) {
    document.getElementById('mute-target').textContent = targetName;
    document.getElementById('mute-modal').style.display = 'block';
}