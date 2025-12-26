"""
Theme Service - Управление темами пользователей
Сохраняет выбор темы пользователя (device_id) в БД
Поддерживает: default, dark, colorful, custom
"""

from models.database import get_db_connection
from config.settings import DATABASE_URL
import json
from datetime import datetime

# ============================================
# THEME MANAGEMENT
# ============================================

def get_user_theme(device_id):
    """
    Получает тему пользователя из БД
    
    Args:
        device_id (str): Уникальный ID устройства пользователя
        
    Returns:
        dict: {
            'theme': str,  # Название темы (default/dark/colorful/custom)
            'custom_settings': dict  # Кастомные настройки (если custom)
        }
        или None если не найдено
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DATABASE_URL:  # PostgreSQL
            cursor.execute(
                """
                SELECT theme_name, custom_settings 
                FROM user_settings 
                WHERE device_id = %s
                """,
                (device_id,)
            )
        else:  # SQLite
            cursor.execute(
                """
                SELECT theme_name, custom_settings 
                FROM user_settings 
                WHERE device_id = ?
                """,
                (device_id,)
            )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            theme_name, custom_settings = result
            
            # Парсим JSON если есть кастомные настройки
            if custom_settings:
                try:
                    custom_settings = json.loads(custom_settings)
                except:
                    custom_settings = None
            
            return {
                'theme': theme_name,
                'custom_settings': custom_settings
            }
        
        return None
        
    except Exception as e:
        print(f"Error getting user theme: {e}")
        return None


def save_user_theme(device_id, theme_name, custom_settings=None):
    """
    Сохраняет выбор темы пользователя
    
    Args:
        device_id (str): Уникальный ID устройства
        theme_name (str): Название темы (default/dark/colorful/custom)
        custom_settings (dict, optional): Кастомные настройки цветов
        
    Returns:
        bool: True если успешно, False если ошибка
        
    Example:
        save_user_theme('device_123', 'dark')
        save_user_theme('device_456', 'custom', {
            'primary_color': '#ff5733',
            'secondary_color': '#33ff57'
        })
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Сериализуем кастомные настройки в JSON
        custom_json = json.dumps(custom_settings) if custom_settings else None
        
        # Проверяем существует ли запись
        if DATABASE_URL:  # PostgreSQL
            cursor.execute(
                "SELECT device_id FROM user_settings WHERE device_id = %s",
                (device_id,)
            )
        else:  # SQLite
            cursor.execute(
                "SELECT device_id FROM user_settings WHERE device_id = ?",
                (device_id,)
            )
        
        exists = cursor.fetchone()
        
        if exists:
            # UPDATE существующей записи
            if DATABASE_URL:  # PostgreSQL
                cursor.execute(
                    """
                    UPDATE user_settings 
                    SET theme_name = %s, 
                        custom_settings = %s, 
                        updated_at = %s
                    WHERE device_id = %s
                    """,
                    (theme_name, custom_json, datetime.now(), device_id)
                )
            else:  # SQLite
                cursor.execute(
                    """
                    UPDATE user_settings 
                    SET theme_name = ?, 
                        custom_settings = ?, 
                        updated_at = ?
                    WHERE device_id = ?
                    """,
                    (theme_name, custom_json, datetime.now().isoformat(), device_id)
                )
        else:
            # INSERT новой записи
            if DATABASE_URL:  # PostgreSQL
                cursor.execute(
                    """
                    INSERT INTO user_settings 
                    (device_id, theme_name, custom_settings, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (device_id, theme_name, custom_json, datetime.now(), datetime.now())
                )
            else:  # SQLite
                cursor.execute(
                    """
                    INSERT INTO user_settings 
                    (device_id, theme_name, custom_settings, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (device_id, theme_name, custom_json, 
                     datetime.now().isoformat(), datetime.now().isoformat())
                )
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving user theme: {e}")
        return False


def get_theme_list():
    """
    Возвращает список доступных тем
    
    Returns:
        list: Список словарей с информацией о темах
    """
    return [
        {
            'id': 'default',
            'name': 'Noklusējuma',
            'description': 'Gaišā tēma ar violetu gradientu',
            'preview_colors': ['#667eea', '#764ba2', '#ffffff'],
            'css_file': None  # Uses base.css
        },
        {
            'id': 'dark',
            'name': 'Tumšā',
            'description': 'Tumšā tēma acīm draudzīga',
            'preview_colors': ['#1a202c', '#667eea', '#2d3748'],
            'css_file': 'themes/dark.css'
        },
        {
            'id': 'colorful',
            'name': 'Krāsainā',
            'description': 'Spilgta un enerģiska tēma',
            'preview_colors': ['#f093fb', '#f5576c', '#fdbb2d'],
            'css_file': 'themes/colorful.css'
        },
        {
            'id': 'custom',
            'name': 'Pielāgota',
            'description': 'Izveidojiet savu tēmu',
            'preview_colors': ['#custom', '#custom', '#custom'],
            'css_file': None  # Generated dynamically
        }
    ]


def generate_custom_css(custom_settings):
    """
    Генерирует CSS для кастомной темы
    
    Args:
        custom_settings (dict): Настройки цветов
        {
            'primary_color': '#ff5733',
            'secondary_color': '#33ff57',
            'background_color': '#ffffff',
            'text_color': '#333333'
        }
        
    Returns:
        str: CSS код
    """
    primary = custom_settings.get('primary_color', '#667eea')
    secondary = custom_settings.get('secondary_color', '#764ba2')
    background = custom_settings.get('background_color', '#f7fafc')
    text = custom_settings.get('text_color', '#1a202c')
    
    css = f"""
/* Custom Theme - Generated */
:root {{
    --primary-start: {primary};
    --primary-end: {secondary};
    --primary-gradient: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
    --gray-50: {background};
    --gray-900: {text};
}}

body {{
    background: {background};
    color: {text};
}}

.navbar,
.card,
.work-card {{
    background: {background};
}}

h1, h2, h3 {{
    color: {text};
}}
"""
    
    return css


def get_theme_statistics():
    """
    Статистика использования тем
    
    Returns:
        dict: {
            'total_users': int,
            'by_theme': {
                'default': int,
                'dark': int,
                'colorful': int,
                'custom': int
            }
        }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Общее количество пользователей с темой
        cursor.execute("SELECT COUNT(*) FROM user_settings WHERE theme_name IS NOT NULL")
        total = cursor.fetchone()[0]
        
        # Подсчет по темам
        cursor.execute(
            """
            SELECT theme_name, COUNT(*) 
            FROM user_settings 
            WHERE theme_name IS NOT NULL
            GROUP BY theme_name
            """
        )
        
        by_theme = {}
        for row in cursor.fetchall():
            theme_name, count = row
            by_theme[theme_name] = count
        
        conn.close()
        
        return {
            'total_users': total,
            'by_theme': by_theme
        }
        
    except Exception as e:
        print(f"Error getting theme statistics: {e}")
        return {
            'total_users': 0,
            'by_theme': {}
        }


def reset_user_theme(device_id):
    """
    Сбрасывает тему пользователя на дефолтную
    
    Args:
        device_id (str): ID устройства
        
    Returns:
        bool: True если успешно
    """
    return save_user_theme(device_id, 'default', None)


def export_user_theme(device_id):
    """
    Экспортирует настройки темы пользователя
    
    Args:
        device_id (str): ID устройства
        
    Returns:
        str: JSON строка с настройками
    """
    theme = get_user_theme(device_id)
    if theme:
        return json.dumps(theme, indent=2)
    return None


def import_user_theme(device_id, theme_json):
    """
    Импортирует настройки темы из JSON
    
    Args:
        device_id (str): ID устройства
        theme_json (str): JSON строка с настройками
        
    Returns:
        bool: True если успешно
    """
    try:
        theme_data = json.loads(theme_json)
        theme_name = theme_data.get('theme')
        custom_settings = theme_data.get('custom_settings')
        
        return save_user_theme(device_id, theme_name, custom_settings)
    except:
        return False


# ============================================
# THEME VALIDATION
# ============================================

def validate_theme_name(theme_name):
    """
    Проверяет корректность названия темы
    
    Args:
        theme_name (str): Название темы
        
    Returns:
        bool: True если валидно
    """
    valid_themes = ['default', 'dark', 'colorful', 'custom']
    return theme_name in valid_themes


def validate_custom_settings(custom_settings):
    """
    Проверяет корректность кастомных настроек
    
    Args:
        custom_settings (dict): Настройки
        
    Returns:
        tuple: (bool, str) - (валидно, сообщение об ошибке)
    """
    if not isinstance(custom_settings, dict):
        return False, "Custom settings must be a dictionary"
    
    required_keys = ['primary_color', 'secondary_color']
    for key in required_keys:
        if key not in custom_settings:
            return False, f"Missing required key: {key}"
    
    # Проверка формата цвета (hex)
    import re
    hex_pattern = r'^#[0-9A-Fa-f]{6}$'
    
    for key in ['primary_color', 'secondary_color', 'background_color', 'text_color']:
        if key in custom_settings:
            color = custom_settings[key]
            if not re.match(hex_pattern, color):
                return False, f"Invalid color format for {key}: {color}"
    
    return True, "Valid"


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_or_create_device_id(request):
    """
    Получает или создает device_id из cookies
    
    Args:
        request: Flask request object
        
    Returns:
        str: device_id
    """
    from flask import request as flask_request
    import uuid
    
    device_id = flask_request.cookies.get('device_id')
    
    if not device_id:
        device_id = str(uuid.uuid4())
    
    return device_id


def apply_theme_to_response(response, device_id):
    """
    Добавляет device_id в cookies ответа
    
    Args:
        response: Flask response object
        device_id (str): ID устройства
        
    Returns:
        response: Modified response
    """
    response.set_cookie(
        'device_id', 
        device_id, 
        max_age=365*24*60*60,  # 1 год
        httponly=True,
        samesite='Lax'
    )
    return response


# ============================================
# EXPORT
# ============================================

__all__ = [
    'get_user_theme',
    'save_user_theme',
    'get_theme_list',
    'generate_custom_css',
    'get_theme_statistics',
    'reset_user_theme',
    'export_user_theme',
    'import_user_theme',
    'validate_theme_name',
    'validate_custom_settings',
    'get_or_create_device_id',
    'apply_theme_to_response'
]