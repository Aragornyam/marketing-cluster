const loadBtn = document.getElementById('loadBtn');
const refreshBtn = document.getElementById('refreshBtn');
const statusMsg = document.getElementById('statusMsg');
const statusIndicator = document.getElementById('statusIndicator');
const recordCount = document.getElementById('recordCount');

loadBtn.addEventListener('click', async () => {
    loadBtn.disabled = true;
    loadBtn.innerText = 'Обработка...';
    statusMsg.innerText = 'Связь с источником и загрузка данных...';
    statusIndicator.className = 'indicator loading';
    statusMsg.style.color = '#111827';

    try {
        const res = await fetch('/api/load_data', { method: 'POST' });
        const data = await res.json();
        
        statusMsg.innerText = data.message;
        statusIndicator.className = 'indicator success';
        updateStats();
    } catch (err) {
        statusMsg.innerText = 'Сбой операции импорта.';
        statusIndicator.className = 'indicator error';
    } finally {
        loadBtn.disabled = false;
        loadBtn.innerText = 'Запустить импорт данных';
    }
});

async function updateStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        recordCount.innerText = data.total_records.toLocaleString('ru-RU');
    } catch (err) {
        console.error('Ошибка синхронизации:', err);
    }
}

refreshBtn.addEventListener('click', updateStats);
updateStats();