/**
 * Study Timer functionality
 * Функционал таймера для учебы
 */

// ========== TIMER VARIABLES ==========
let timerInterval = null;
let seconds = 0;
let isRunning = false;
let lastSaveTime = 0;

// ========== INITIALIZATION ==========
function initTimer() {
    console.log('⏱️ Инициализация таймера');
    loadTimerData();
}

// ========== TIMER CONTROLS ==========
function startTimer() {
    if (!isRunning) {
        isRunning = true;
        timerInterval = setInterval(() => {
            seconds++;
            updateTimerDisplay();
            
            // Автосохранение каждые 30 секунд
            if (seconds - lastSaveTime >= 30) {
                saveTimerData();
                lastSaveTime = seconds;
            }
        }, 1000);
        
        console.log('▶️ Таймер запущен');
        showNotification('Таймер запущен', 'info');
    }
}

function pauseTimer() {
    if (isRunning) {
        isRunning = false;
        clearInterval(timerInterval);
        saveTimerData();
        
        console.log('⏸️ Таймер остановлен');
        showNotification('Таймер остановлен', 'info');
    }
}

function resetTimer() {
    const confirmReset = confirm('Vai tiešām vēlaties apturēt taimeri? Visi dati tiks dzēsti.');
    
    if (confirmReset) {
        isRunning = false;
        clearInterval(timerInterval);
        seconds = 0;
        updateTimerDisplay();
        saveTimerData();
        
        console.log('⏹️ Таймер сброшен');
        showNotification('Таймер сброшен', 'success');
    }
}

function toggleTimerModal() {
    const modal = document.getElementById('timerModal');
    if (modal) {
        modal.classList.toggle('active');
    }
}

// ========== DISPLAY UPDATE ==========
function updateTimerDisplay() {
    const hours = Math.floor(seconds / 3600).toString().padStart(2, '0');
    const minutes = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    const secs = (seconds % 60).toString().padStart(2, '0');
    
    const hoursEl = document.getElementById('timerHours');
    const minutesEl = document.getElementById('timerMinutes');
    const secondsEl = document.getElementById('timerSeconds');
    
    if (hoursEl) hoursEl.textContent = hours;
    if (minutesEl) minutesEl.textContent = minutes;
    if (secondsEl) secondsEl.textContent = secs;
}

// ========== DATA PERSISTENCE ==========
async function loadTimerData() {
    try {
        const response = await fetch('/api/timer/stats');
        const data = await response.json();
        
        if (data.success && data.stats) {
            const stats = data.stats;
            
            // Обновляем отображение статистики
            updateTimerStats(stats.today_seconds, stats.total_seconds);
            
            console.log('✅ Статистика таймера загружена');
        }
    } catch (error) {
        console.error('❌ Ошибка загрузки статистики:', error);
        updateTimerStats(0, 0);
    }
}

async function saveTimerData() {
    try {
        const response = await fetch('/api/timer/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ seconds: seconds })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('💾 Данные таймера сохранены');
            // Обновляем статистику после сохранения
            await loadTimerData();
        }
    } catch (error) {
        console.error('❌ Ошибка сохранения:', error);
        // Fallback: сохраняем локально в памяти
        window.timerBackup = {
            seconds: seconds,
            timestamp: Date.now()
        };
    }
}

function updateTimerStats(todaySeconds, totalSeconds) {
    const todayEl = document.getElementById('todayTime');
    const totalEl = document.getElementById('totalTime');
    
    if (todayEl) {
        todayEl.textContent = formatTimeHuman(todaySeconds);
    }
    
    if (totalEl) {
        totalEl.textContent = formatTimeHuman(totalSeconds);
    }
}

// ========== UTILITY FUNCTIONS ==========
function formatTimeHuman(totalSeconds) {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

// ========== EVENT LISTENERS ==========
// Сохранение при закрытии страницы
window.addEventListener('beforeunload', function() {
    if (seconds > 0 && isRunning) {
        // Используем sendBeacon для надежной отправки
        const data = JSON.stringify({ seconds: seconds });
        navigator.sendBeacon('/api/timer/save', data);
    }
});

// Закрытие модального окна при клике вне его
document.addEventListener('click', function(event) {
    const modal = document.getElementById('timerModal');
    const btn = document.querySelector('.timer-floating-btn');
    
    if (modal && modal.classList.contains('active') && 
        !modal.contains(event.target) && 
        !btn.contains(event.target)) {
        modal.classList.remove('active');
    }
});

// ========== EXPORT ==========
window.startTimer = startTimer;
window.pauseTimer = pauseTimer;
window.resetTimer = resetTimer;
window.toggleTimerModal = toggleTimerModal;
window.initTimer = initTimer;

console.log('✅ Timer.js загружен');