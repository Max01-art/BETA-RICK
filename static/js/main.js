/**
 * Основной JavaScript файл приложения
 */

// ========== GLOBAL VARIABLES ==========
let socket = null;

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Приложение загружено');
    
    // Инициализация компонентов
    initSocketIO();
    initMobileMenu();
    initDropdowns();
    initModals();
    initForms();
    initTooltips();
    
    // Обновление времени
    updateCurrentTime();
    setInterval(updateCurrentTime, 30000); // Каждые 30 секунд
});

// ========== SOCKET.IO ==========
function initSocketIO() {
    if (typeof io !== 'undefined') {
        socket = io();
        
        socket.on('connect', function() {
            console.log('✅ Подключен к серверу');
        });
        
        socket.on('disconnect', function() {
            console.log('❌ Отключен от сервера');
        });
        
        socket.on('online_count_update', function(data) {
            updateOnlineCount(data.count);
        });
    }
}

function updateOnlineCount(count) {
    const element = document.getElementById('onlineCount');
    if (element) {
        element.textContent = count;
        // Анимация
        element.style.transform = 'scale(1.2)';
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 300);
    }
}

// ========== MOBILE MENU ==========
function toggleMobileMenu() {
    const menu = document.getElementById('navbarMenu');
    if (menu) {
        menu.classList.toggle('open');
    }
}

function initMobileMenu() {
    // Закрытие меню при клике вне его
    document.addEventListener('click', function(event) {
        const navbar = document.querySelector('.navbar');
        const menu = document.getElementById('navbarMenu');
        const toggle = document.querySelector('.navbar-toggle');
        
        if (menu && menu.classList.contains('open') && 
            !navbar.contains(event.target) && 
            !toggle.contains(event.target)) {
            menu.classList.remove('open');
        }
    });
}

// ========== DROPDOWNS ==========
function initDropdowns() {
    const dropdowns = document.querySelectorAll('.nav-dropdown');
    
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('mouseenter', function() {
            const menu = this.querySelector('.dropdown-menu');
            if (menu) {
                menu.style.display = 'block';
            }
        });
        
        dropdown.addEventListener('mouseleave', function() {
            const menu = this.querySelector('.dropdown-menu');
            if (menu) {
                menu.style.display = 'none';
            }
        });
    });
}

// ========== MODALS ==========
function initModals() {
    // Закрытие модалов по клику на overlay
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal-overlay')) {
            closeModal(event.target.closest('.modal'));
        }
    });
    
    // Закрытие по ESC
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.active');
            openModals.forEach(modal => closeModal(modal));
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modal) {
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// ========== FORMS ==========
function initForms() {
    // Автосохранение черновиков
    const forms = document.querySelectorAll('form[data-autosave]');
    
    forms.forEach(form => {
        const formId = form.id || 'form_' + Date.now();
        
        // Загрузка сохраненных данных
        loadFormDraft(form, formId);
        
        // Сохранение при изменении
        form.addEventListener('input', function() {
            saveFormDraft(form, formId);
        });
    });
}

function saveFormDraft(form, formId) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    // Не используем localStorage - сохраняем в памяти
    window[`draft_${formId}`] = data;
    console.log(`💾 Черновик формы ${formId} сохранен`);
}

function loadFormDraft(form, formId) {
    const data = window[`draft_${formId}`];
    
    if (data) {
        for (let [key, value] of Object.entries(data)) {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = value;
            }
        }
        console.log(`📂 Черновик формы ${formId} загружен`);
    }
}

function clearFormDraft(formId) {
    delete window[`draft_${formId}`];
    console.log(`🗑️ Черновик формы ${formId} удален`);
}

// ========== TOOLTIPS ==========
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const element = event.currentTarget;
    const text = element.getAttribute('data-tooltip');
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.id = 'active-tooltip';
    
    document.body.appendChild(tooltip);
    
    // Позиционирование
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('active-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// ========== UTILITY FUNCTIONS ==========
function updateCurrentTime() {
    const element = document.getElementById('currentTime');
    if (element) {
        const now = new Date();
        const timeString = now.toLocaleTimeString('lv-LV', {
            hour: '2-digit',
            minute: '2-digit'
        });
        element.textContent = timeString;
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Показать
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Скрыть через 3 секунды
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('lv-LV', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

function formatTime(timeString) {
    if (!timeString) return '';
    return timeString.substring(0, 5); // HH:MM
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Nokopēts!', 'success');
    }).catch(err => {
        console.error('Kļūda kopējot:', err);
        showNotification('Nevarēja nokopēt', 'error');
    });
}

// ========== API REQUESTS ==========
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Request Error:', error);
        showNotification('Kļūda savienojumā ar serveri', 'error');
        throw error;
    }
}

// ========== EXPORT ==========
window.toggleMobileMenu = toggleMobileMenu;
window.openModal = openModal;
window.closeModal = closeModal;
window.showNotification = showNotification;
window.confirmAction = confirmAction;
window.formatDate = formatDate;
window.formatTime = formatTime;
window.copyToClipboard = copyToClipboard;
window.apiRequest = apiRequest;