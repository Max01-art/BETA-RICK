// ============================================
// CLASSMATE - JAVASCRIPT UTILITIES
// ============================================

// ========== DATE & TIME UTILITIES ==========

/**
 * Форматирует дату в читаемый формат
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    
    return `${day}.${month}.${year}`;
}

/**
 * Форматирует время
 */
function formatTime(timeString) {
    if (!timeString) return '';
    return timeString.substring(0, 5); // HH:MM
}

/**
 * Вычисляет количество дней до дедлайна
 */
function calculateDaysLeft(dateString, timeString = '23:59') {
    const now = new Date();
    const deadline = new Date(`${dateString} ${timeString}`);
    
    const diffTime = deadline - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays;
}

/**
 * Возвращает текстовое представление времени до дедлайна
 */
function getTimeLeftText(daysLeft) {
    if (daysLeft < 0) return 'Nokavēts';
    if (daysLeft === 0) return 'Šodien!';
    if (daysLeft === 1) return 'Rīt';
    if (daysLeft <= 7) return `${daysLeft} dienas`;
    return `${daysLeft} dienas`;
}

/**
 * Возвращает класс бейджа в зависимости от дедлайна
 */
function getDeadlineBadgeClass(daysLeft) {
    if (daysLeft === 0) return 'badge-today';
    if (daysLeft === 1) return 'badge-tomorrow';
    if (daysLeft <= 7) return 'badge-soon';
    return 'badge-future';
}

// ========== NOTIFICATION SYSTEM ==========

/**
 * Показывает уведомление
 */
function showNotification(message, type = 'info', duration = 3000) {
    const container = document.getElementById('notification-container') || createNotificationContainer();
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} notification-enter`;
    
    const icon = getNotificationIcon(type);
    
    notification.innerHTML = `
        <div class="notification-icon">${icon}</div>
        <div class="notification-content">
            <p class="notification-message">${message}</p>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(notification);
    
    // Анимация появления
    setTimeout(() => notification.classList.add('notification-show'), 10);
    
    // Автоматическое удаление
    if (duration > 0) {
        setTimeout(() => {
            notification.classList.remove('notification-show');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
}

/**
 * Создает контейнер для уведомлений
 */
function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notification-container';
    container.className = 'notification-container';
    document.body.appendChild(container);
    return container;
}

/**
 * Возвращает иконку для типа уведомления
 */
function getNotificationIcon(type) {
    const icons = {
        success: '<i class="fas fa-check-circle"></i>',
        error: '<i class="fas fa-exclamation-circle"></i>',
        warning: '<i class="fas fa-exclamation-triangle"></i>',
        info: '<i class="fas fa-info-circle"></i>'
    };
    return icons[type] || icons.info;
}

// ========== MODAL UTILITIES ==========

/**
 * Открывает модальное окно
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('modal-open');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Закрывает модальное окно
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('modal-open');
        document.body.style.overflow = '';
    }
}

/**
 * Закрывает модальное окно при клике вне его
 */
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        closeModal(e.target.id);
    }
});

// ========== FORM UTILITIES ==========

/**
 * Валидация формы
 */
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    const inputs = form.querySelectorAll('[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('input-error');
            isValid = false;
        } else {
            input.classList.remove('input-error');
        }
    });
    
    return isValid;
}

/**
 * Очистка формы
 */
function resetForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
        // Удаляем классы ошибок
        form.querySelectorAll('.input-error').forEach(el => {
            el.classList.remove('input-error');
        });
    }
}

// ========== LOCAL STORAGE ==========

/**
 * Сохранить в localStorage
 */
function saveToStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (e) {
        console.error('Error saving to localStorage:', e);
        return false;
    }
}

/**
 * Получить из localStorage
 */
function getFromStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
        console.error('Error reading from localStorage:', e);
        return defaultValue;
    }
}

/**
 * Удалить из localStorage
 */
function removeFromStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (e) {
        console.error('Error removing from localStorage:', e);
        return false;
    }
}

// ========== API HELPERS ==========

/**
 * Выполняет GET запрос
 */
async function apiGet(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API GET error:', error);
        showNotification('Kļūda ielādējot datus', 'error');
        throw error;
    }
}

/**
 * Выполняет POST запрос
 */
async function apiPost(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API POST error:', error);
        showNotification('Kļūda saglabājot datus', 'error');
        throw error;
    }
}

// ========== DOM UTILITIES ==========

/**
 * Дождаться загрузки DOM
 */
function ready(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
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
 * Throttle функция
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ========== COPY TO CLIPBOARD ==========

/**
 * Копирует текст в буфер обмена
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Nokopēts!', 'success', 2000);
        return true;
    } catch (err) {
        console.error('Failed to copy:', err);
        showNotification('Neizdevās nokopēt', 'error');
        return false;
    }
}

// ========== SCROLL UTILITIES ==========

/**
 * Плавная прокрутка к элементу
 */
function scrollToElement(elementId, offset = 100) {
    const element = document.getElementById(elementId);
    if (element) {
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;
        
        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
}

/**
 * Проверка видимости элемента
 */
function isElementInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// ========== THEME UTILITIES ==========

/**
 * Применяет тему
 */
function applyTheme(themeName) {
    document.body.setAttribute('data-theme', themeName);
    saveToStorage('user-theme', themeName);
}

/**
 * Получает текущую тему
 */
function getCurrentTheme() {
    return document.body.getAttribute('data-theme') || getFromStorage('user-theme', 'default');
}

/**
 * Переключает тему
 */
function toggleTheme() {
    const currentTheme = getCurrentTheme();
    const newTheme = currentTheme === 'dark' ? 'default' : 'dark';
    applyTheme(newTheme);
}

// ========== EXPORT ==========
// Делаем функции доступными глобально
window.ClassmateUtils = {
    // Date & Time
    formatDate,
    formatTime,
    calculateDaysLeft,
    getTimeLeftText,
    getDeadlineBadgeClass,
    
    // Notifications
    showNotification,
    
    // Modals
    openModal,
    closeModal,
    
    // Forms
    validateForm,
    resetForm,
    
    // Storage
    saveToStorage,
    getFromStorage,
    removeFromStorage,
    
    // API
    apiGet,
    apiPost,
    
    // DOM
    ready,
    debounce,
    throttle,
    copyToClipboard,
    scrollToElement,
    isElementInViewport,
    
    // Theme
    applyTheme,
    getCurrentTheme,
    toggleTheme
};

// ========== AUTO-INIT ==========
ready(() => {
    console.log('✅ Classmate Utils loaded');
    
    // Применяем сохраненную тему
    const savedTheme = getFromStorage('user-theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    }
});