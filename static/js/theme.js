/**
 * Theme management
 * Управление темами оформления
 */

// ========== THEME SWITCHING ==========
function toggleTheme() {
    const html = document.documentElement;
    const themeIcon = document.querySelector('.theme-icon');
    const themeText = document.querySelector('.theme-text');
    
    if (html.classList.contains('theme-light')) {
        // Переключаем на темную тему
        html.classList.remove('theme-light');
        html.classList.add('theme-dark');
        
        if (themeIcon) themeIcon.textContent = '☀️';
        if (themeText) themeText.textContent = 'Gaišs';
        
        // Создаем звезды
        createStars();
        
        saveTheme('dark');
        console.log('🌙 Темная тема активирована');
    } else {
        // Переключаем на светлую тему
        html.classList.remove('theme-dark');
        html.classList.add('theme-light');
        
        if (themeIcon) themeIcon.textContent = '🌙';
        if (themeText) themeText.textContent = 'Tumšs';
        
        saveTheme('light');
        console.log('☀️ Светлая тема активирована');
    }
}

// ========== STARS GENERATION ==========
function createStars() {
    const starsContainer = document.getElementById('stars');
    if (!starsContainer) return;
    
    starsContainer.innerHTML = '';
    
    const starCount = 150;
    
    for (let i = 0; i < starCount; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        
        // Случайная позиция
        const left = Math.random() * 100;
        const top = Math.random() * 100;
        const size = Math.random() * 3 + 1;
        const delay = Math.random() * 5;
        
        star.style.left = `${left}%`;
        star.style.top = `${top}%`;
        star.style.width = `${size}px`;
        star.style.height = `${size}px`;
        star.style.animationDelay = `${delay}s`;
        
        starsContainer.appendChild(star);
    }
    
    console.log('✨ Звезды созданы');
}

// ========== THEME PERSISTENCE ==========
function saveTheme(theme) {
    // Сохраняем в памяти (не localStorage)
    window.currentTheme = theme;
    
    // Отправляем на сервер
    fetch('/api/set_theme', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ theme: theme })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('✅ Тема сохранена на сервере');
        }
    })
    .catch(error => {
        console.error('❌ Ошибка сохранения темы:', error);
    });
}

function loadTheme() {
    // Загружаем тему из памяти или HTML класса
    const html = document.documentElement;
    let theme = window.currentTheme;
    
    // Если нет в памяти, проверяем HTML класс
    if (!theme) {
        theme = html.classList.contains('theme-dark') ? 'dark' : 'light';
        window.currentTheme = theme;
    }
    
    // Применяем тему
    if (theme === 'dark') {
        html.classList.remove('theme-light');
        html.classList.add('theme-dark');
        
        const themeIcon = document.querySelector('.theme-icon');
        const themeText = document.querySelector('.theme-text');
        
        if (themeIcon) themeIcon.textContent = '☀️';
        if (themeText) themeText.textContent = 'Gaišs';
        
        createStars();
    }
    
    console.log(`🎨 Тема загружена: ${theme}`);
}

// ========== CUSTOM THEME ==========
function applyCustomTheme(colors) {
    const root = document.documentElement;
    
    if (colors.primary) root.style.setProperty('--primary', colors.primary);
    if (colors.secondary) root.style.setProperty('--secondary', colors.secondary);
    if (colors.accent) root.style.setProperty('--accent', colors.accent);
    if (colors.background) root.style.setProperty('--bg-primary', colors.background);
    
    console.log('🎨 Кастомная тема применена', colors);
}

function resetTheme() {
    const root = document.documentElement;
    
    // Сброс всех кастомных переменных
    root.style.removeProperty('--primary');
    root.style.removeProperty('--secondary');
    root.style.removeProperty('--accent');
    root.style.removeProperty('--bg-primary');
    
    // Возврат к стандартной теме
    const html = document.documentElement;
    html.classList.remove('theme-dark');
    html.classList.add('theme-light');
    
    saveTheme('light');
    
    console.log('🔄 Тема сброшена к стандартной');
}

// ========== THEME PRESETS ==========
const themePresets = {
    default: {
        primary: '#2E5BFF',
        secondary: '#00A3FF',
        accent: '#00C9A7'
    },
    purple: {
        primary: '#8E44AD',
        secondary: '#9B59B6',
        accent: '#BB8FCE'
    },
    green: {
        primary: '#27AE60',
        secondary: '#2ECC71',
        accent: '#58D68D'
    },
    orange: {
        primary: '#E67E22',
        secondary: '#F39C12',
        accent: '#F8C471'
    },
    red: {
        primary: '#E74C3C',
        secondary: '#C0392B',
        accent: '#EC7063'
    }
};

function applyPreset(presetName) {
    const preset = themePresets[presetName];
    if (preset) {
        applyCustomTheme(preset);
        console.log(`✅ Применен пресет: ${presetName}`);
    } else {
        console.error(`❌ Пресет не найден: ${presetName}`);
    }
}

// ========== AUTO THEME (based on time) ==========
function autoTheme() {
    const hour = new Date().getHours();
    
    // Темная тема с 20:00 до 6:00
    if (hour >= 20 || hour < 6) {
        if (!document.documentElement.classList.contains('theme-dark')) {
            toggleTheme();
            console.log('🌙 Авто-переключение на темную тему');
        }
    } else {
        if (!document.documentElement.classList.contains('theme-light')) {
            toggleTheme();
            console.log('☀️ Авто-переключение на светлую тему');
        }
    }
}

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', function() {
    loadTheme();
    
    // Опционально: автоматическое переключение тем
    // autoTheme();
    // setInterval(autoTheme, 60000); // Проверка каждую минуту
});

// ========== EXPORT ==========
window.toggleTheme = toggleTheme;
window.loadTheme = loadTheme;
window.applyCustomTheme = applyCustomTheme;
window.resetTheme = resetTheme;
window.applyPreset = applyPreset;
window.autoTheme = autoTheme;