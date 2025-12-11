/**
 * Notifications JavaScript
 * Система уведомлений приложения
 */

// ==================== BROWSER NOTIFICATIONS ====================
const BrowserNotifications = {
    /**
     * Проверить поддержку уведомлений
     */
    isSupported() {
        return 'Notification' in window;
    },
    
    /**
     * Получить текущее разрешение
     */
    getPermission() {
        if (!this.isSupported()) {
            return 'unsupported';
        }
        return Notification.permission;
    },
    
    /**
     * Запросить разрешение
     */
    async requestPermission() {
        if (!this.isSupported()) {
            console.warn('Browser notifications not supported');
            return 'unsupported';
        }
        
        if (Notification.permission === 'granted') {
            return 'granted';
        }
        
        try {
            const permission = await Notification.requestPermission();
            return permission;
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            return 'denied';
        }
    },
    
    /**
     * Показать уведомление
     */
    show(title, options = {}) {
        if (Notification.permission !== 'granted') {
            console.warn('Notification permission not granted');
            return null;
        }
        
        const defaultOptions = {
            icon: '/static/images/logo.png',
            badge: '/static/images/logo.png',
            requireInteraction: false,
            ...options
        };
        
        try {
            return new Notification(title, defaultOptions);
        } catch (error) {
            console.error('Error showing notification:', error);
            return null;
        }
    }
};


// ==================== EMAIL NOTIFICATIONS ====================
const EmailNotifications = {
    /**
     * Подписаться на email уведомления
     */
    async subscribe(email, preferences = {}) {
        try {
            const data = await NotificationsAPI.subscribe(email, preferences);
            
            if (data.success) {
                showSuccessNotification('Jūs esat veiksmīgi parakstījies uz paziņojumiem');
                
                // Сохраняем email в localStorage
                localStorage.setItem('notification_email', email);
                
                return true;
            } else {
                throw new Error(data.error || 'Subscription failed');
            }
        } catch (error) {
            console.error('Subscription error:', error);
            showErrorNotification('Kļūda parakstīšanās laikā');
            return false;
        }
    },
    
    /**
     * Отписаться от email уведомлений
     */
    async unsubscribe(email) {
        try {
            const data = await NotificationsAPI.unsubscribe(email);
            
            if (data.success) {
                showSuccessNotification('Jūs esat veiksmīgi atrakstījies no paziņojumiem');
                
                // Удаляем email из localStorage
                localStorage.removeItem('notification_email');
                
                return true;
            } else {
                throw new Error(data.error || 'Unsubscription failed');
            }
        } catch (error) {
            console.error('Unsubscription error:', error);
            showErrorNotification('Kļūda atrakstīšanās laikā');
            return false;
        }
    },
    
    /**
     * Получить сохраненный email
     */
    getSavedEmail() {
        return localStorage.getItem('notification_email');
    },
    
    /**
     * Проверить подписку
     */
    async checkSubscription(email) {
        try {
            const data = await NotificationsAPI.getSettings(email);
            return data;
        } catch (error) {
            console.error('Check subscription error:', error);
            return null;
        }
    }
};


// ==================== IN-APP NOTIFICATIONS ====================
const InAppNotifications = {
    container: null,
    notifications: [],
    maxNotifications: 5,
    
    /**
     * Инициализация контейнера уведомлений
     */
    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notifications-container';
            this.container.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 9998;
                display: flex;
                flex-direction: column;
                gap: 1rem;
                max-width: 400px;
            `;
            document.body.appendChild(this.container);
        }
    },
    
    /**
     * Показать уведомление
     */
    show(message, type = 'info', duration = 5000) {
        this.init();
        
        // Ограничиваем количество уведомлений
        if (this.notifications.length >= this.maxNotifications) {
            this.remove(this.notifications[0]);
        }
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">${this.getIcon(type)}</div>
                <div class="notification-message">${message}</div>
                <button class="notification-close" onclick="InAppNotifications.remove(this.parentElement.parentElement)">✕</button>
            </div>
        `;
        
        notification.style.cssText = `
            background: var(--card-bg);
            border-radius: 10px;
            padding: 1rem;
            box-shadow: var(--shadow-hover);
            animation: slideInRight 0.3s ease;
            border-left: 4px solid ${this.getColor(type)};
            cursor: pointer;
        `;
        
        // Добавляем в контейнер
        this.container.appendChild(notification);
        this.notifications.push(notification);
        
        // Автоматическое удаление
        if (duration > 0) {
            setTimeout(() => {
                this.remove(notification);
            }, duration);
        }
        
        // Удаление по клику
        notification.addEventListener('click', () => {
            this.remove(notification);
        });
        
        return notification;
    },
    
    /**
     * Удалить уведомление
     */
    remove(notification) {
        if (notification && notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.parentElement.removeChild(notification);
                }
                const index = this.notifications.indexOf(notification);
                if (index > -1) {
                    this.notifications.splice(index, 1);
                }
            }, 300);
        }
    },
    
    /**
     * Удалить все уведомления
     */
    removeAll() {
        this.notifications.forEach(notification => {
            this.remove(notification);
        });
    },
    
    /**
     * Получить иконку по типу
     */
    getIcon(type) {
        const icons = {
            success: '✓',
            danger: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || icons.info;
    },
    
    /**
     * Получить цвет по типу
     */
    getColor(type) {
        const colors = {
            success: 'var(--success-color)',
            danger: 'var(--danger-color)',
            warning: 'var(--warning-color)',
            info: 'var(--info-color)'
        };
        return colors[type] || colors.info;
    }
};


// ==================== NOTIFICATION MANAGER ====================
const NotificationManager = {
    /**
     * Инициализация
     */
    async init() {
        // Инициализируем in-app уведомления
        InAppNotifications.init();
        
        // Проверяем поддержку браузерных уведомлений
        if (BrowserNotifications.isSupported()) {
            console.log('Browser notifications supported');
            
            // Проверяем разрешение
            const permission = BrowserNotifications.getPermission();
            console.log('Notification permission:', permission);
        }
        
        // Проверяем сохраненный email
        const savedEmail = EmailNotifications.getSavedEmail();
        if (savedEmail) {
            console.log('Saved notification email:', savedEmail);
        }
    },
    
    /**
     * Показать уведомление о работе
     */
    notifyWork(work, type = 'test') {
        const daysLeft = calculateDaysLeft(work.date, work.time);
        const statusText = getStatusText(daysLeft);
        
        let message = '';
        if (type === 'test') {
            message = `${work.type} - ${work.subject}: ${statusText}`;
        } else {
            message = `${work.title} - ${work.subject}: ${statusText}`;
        }
        
        // Определяем тип уведомления
        let notificationType = 'info';
        if (daysLeft === 0) {
            notificationType = 'danger';
        } else if (daysLeft === 1) {
            notificationType = 'warning';
        } else if (daysLeft < 0) {
            notificationType = 'danger';
        }
        
        // Показываем in-app уведомление
        InAppNotifications.show(message, notificationType);
        
        // Показываем браузерное уведомление если разрешено
        if (BrowserNotifications.getPermission() === 'granted') {
            BrowserNotifications.show(message, {
                body: `Datums: ${work.date} ${work.time}`,
                tag: `work-${type}-${work.id}`,
                requireInteraction: daysLeft <= 1
            });
        }
    },
    
    /**
     * Запросить разрешения на уведомления
     */
    async requestPermissions() {
        const permission = await BrowserNotifications.requestPermission();
        
        if (permission === 'granted') {
            InAppNotifications.show('Paziņojumi ieslēgti!', 'success');
        } else if (permission === 'denied') {
            InAppNotifications.show('Paziņojumi bloķēti', 'warning');
        }
        
        return permission;
    },
    
    /**
     * Показать уведомление об успехе
     */
    success(message) {
        InAppNotifications.show(message, 'success');
    },
    
    /**
     * Показать уведомление об ошибке
     */
    error(message) {
        InAppNotifications.show(message, 'danger');
    },
    
    /**
     * Показать информационное уведомление
     */
    info(message) {
        InAppNotifications.show(message, 'info');
    },
    
    /**
     * Показать предупреждение
     */
    warning(message) {
        InAppNotifications.show(message, 'warning');
    }
};


// ==================== АНИМАЦИИ ====================
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .notification-icon {
        font-size: 1.5rem;
        flex-shrink: 0;
    }
    
    .notification-message {
        flex: 1;
        line-height: 1.5;
    }
    
    .notification-close {
        background: none;
        border: none;
        font-size: 1.25rem;
        cursor: pointer;
        opacity: 0.6;
        transition: opacity 0.3s ease;
        flex-shrink: 0;
    }
    
    .notification-close:hover {
        opacity: 1;
    }
`;
document.head.appendChild(style);


// ==================== ЭКСПОРТ ====================
window.BrowserNotifications = BrowserNotifications;
window.EmailNotifications = EmailNotifications;
window.InAppNotifications = InAppNotifications;
window.NotificationManager = NotificationManager;

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    NotificationManager.init();
    console.log('✅ Notifications module loaded');
});

console.log('✅ Notifications script loaded');