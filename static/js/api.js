/**
 * API JavaScript
 * Функции для работы с API
 */

// ==================== API CLIENT ====================
const API = {
    baseURL: window.location.origin,
    
    /**
     * Выполнить GET запрос
     */
    async get(endpoint) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API GET Error:', error);
            throw error;
        }
    },
    
    /**
     * Выполнить POST запрос
     */
    async post(endpoint, data) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API POST Error:', error);
            throw error;
        }
    },
    
    /**
     * Выполнить DELETE запрос
     */
    async delete(endpoint) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API DELETE Error:', error);
            throw error;
        }
    }
};


// ==================== TESTS API ====================
const TestsAPI = {
    /**
     * Получить все тесты
     */
    async getAll() {
        return await API.get('/tests/upcoming');
    },
    
    /**
     * Получить тест по ID
     */
    async getById(id) {
        return await API.get(`/tests/${id}`);
    },
    
    /**
     * Получить тесты по предмету
     */
    async getBySubject(subjectName) {
        return await API.get(`/tests/by-subject/${encodeURIComponent(subjectName)}`);
    },
    
    /**
     * Получить статистику тестов
     */
    async getStats() {
        return await API.get('/tests/stats');
    }
};


// ==================== HOMEWORK API ====================
const HomeworkAPI = {
    /**
     * Получить все домашние задания
     */
    async getAll() {
        return await API.get('/homework/upcoming');
    },
    
    /**
     * Получить домашнее задание по ID
     */
    async getById(id) {
        return await API.get(`/homework/${id}`);
    },
    
    /**
     * Получить домашние задания по предмету
     */
    async getBySubject(subjectName) {
        return await API.get(`/homework/by-subject/${encodeURIComponent(subjectName)}`);
    },
    
    /**
     * Получить статистику домашних заданий
     */
    async getStats() {
        return await API.get('/homework/stats');
    }
};


// ==================== NEWS API ====================
const NewsAPI = {
    /**
     * Получить последние новости
     */
    async getLatest(limit = 5) {
        return await API.get(`/news/latest?limit=${limit}`);
    },
    
    /**
     * Получить новость по ID
     */
    async getById(id) {
        return await API.get(`/news/${id}`);
    },
    
    /**
     * Поиск новостей
     */
    async search(query) {
        return await API.get(`/news/search?q=${encodeURIComponent(query)}`);
    }
};


// ==================== SUBJECTS API ====================
const SubjectsAPI = {
    /**
     * Получить все предметы
     */
    async getAll() {
        return await API.get('/api/subjects');
    },
    
    /**
     * Получить предмет по имени
     */
    async getByName(name) {
        return await API.get(`/subjects/${encodeURIComponent(name)}`);
    }
};


// ==================== NOTIFICATIONS API ====================
const NotificationsAPI = {
    /**
     * Подписаться на уведомления
     */
    async subscribe(email, options = {}) {
        return await API.post('/notifications/subscribe', {
            email: email,
            notify_1_day: options.notify_1_day !== false,
            notify_3_days: options.notify_3_days !== false
        });
    },
    
    /**
     * Отписаться от уведомлений
     */
    async unsubscribe(email) {
        return await API.post('/notifications/unsubscribe', {
            email: email
        });
    },
    
    /**
     * Получить настройки уведомлений
     */
    async getSettings(email) {
        return await API.get(`/notifications/settings?email=${encodeURIComponent(email)}`);
    }
};


// ==================== HELPER FUNCTIONS ====================

/**
 * Показать уведомление об успехе
 */
function showSuccessNotification(message) {
    showNotificationToast(message, 'success');
}

/**
 * Показать уведомление об ошибке
 */
function showErrorNotification(message) {
    showNotificationToast(message, 'danger');
}

/**
 * Показать информационное уведомление
 */
function showInfoNotification(message) {
    showNotificationToast(message, 'info');
}

/**
 * Показать toast уведомление
 */
function showNotificationToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `notification-toast notification-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: var(--card-bg);
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: var(--shadow);
        z-index: 9999;
        animation: slideInRight 0.3s ease;
        border-left: 4px solid;
    `;
    
    switch(type) {
        case 'success':
            toast.style.borderColor = 'var(--success-color)';
            break;
        case 'danger':
            toast.style.borderColor = 'var(--danger-color)';
            break;
        case 'warning':
            toast.style.borderColor = 'var(--warning-color)';
            break;
        default:
            toast.style.borderColor = 'var(--info-color)';
    }
    
    document.body.appendChild(toast);
    
    // Автоматическое удаление через 3 секунды
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
    
    // Удаление по клику
    toast.addEventListener('click', () => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    });
}

/**
 * Показать индикатор загрузки
 */
function showLoading(element) {
    const loader = document.createElement('div');
    loader.className = 'spinner spinner-sm';
    loader.style.margin = '0 auto';
    
    element.innerHTML = '';
    element.appendChild(loader);
}

/**
 * Форматировать дату
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('lv-LV', options);
}

/**
 * Форматировать время
 */
function formatTime(timeString) {
    if (!timeString) return '';
    return timeString.slice(0, 5); // HH:MM
}

/**
 * Рассчитать дни до даты
 */
function calculateDaysLeft(dateString, timeString = '23:59') {
    const now = new Date();
    const target = new Date(`${dateString} ${timeString}`);
    const diff = target - now;
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    return days;
}

/**
 * Получить текст статуса
 */
function getStatusText(daysLeft) {
    if (daysLeft < 0) return 'Nokavēts';
    if (daysLeft === 0) return 'Šodien';
    if (daysLeft === 1) return 'Rīt';
    return `${daysLeft} dienas`;
}

/**
 * Получить класс статуса
 */
function getStatusClass(daysLeft) {
    if (daysLeft < 0) return 'status-overdue';
    if (daysLeft === 0) return 'status-today';
    if (daysLeft === 1) return 'status-tomorrow';
    if (daysLeft <= 7) return 'status-soon';
    return 'status-normal';
}

/**
 * Debounce функция
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Копировать текст в буфер обмена
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showSuccessNotification('Nokopēts starpliktuvē');
    } catch (err) {
        showErrorNotification('Neizdevās nokopēt');
    }
}

/**
 * Скачать файл
 */
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}


// ==================== ЭКСПОРТ ====================
// Делаем API доступным глобально
window.API = API;
window.TestsAPI = TestsAPI;
window.HomeworkAPI = HomeworkAPI;
window.NewsAPI = NewsAPI;
window.SubjectsAPI = SubjectsAPI;
window.NotificationsAPI = NotificationsAPI;

// Вспомогательные функции
window.showSuccessNotification = showSuccessNotification;
window.showErrorNotification = showErrorNotification;
window.showInfoNotification = showInfoNotification;
window.formatDate = formatDate;
window.formatTime = formatTime;
window.calculateDaysLeft = calculateDaysLeft;
window.getStatusText = getStatusText;
window.getStatusClass = getStatusClass;
window.debounce = debounce;
window.copyToClipboard = copyToClipboard;
window.downloadFile = downloadFile;

console.log('✅ API module loaded');