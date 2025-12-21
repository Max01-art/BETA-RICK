"""
Помощники для Jinja2 шаблонов
"""
from flask import request
from datetime import datetime


def inject_common_variables():
    """Внедряет общие переменные во все шаблоны"""
    
    def safe_format_date(date_value):
        """Безопасно форматирует дату"""
        if not date_value:
            return ''
        
        if isinstance(date_value, str):
            return date_value
        
        if hasattr(date_value, 'strftime'):
            try:
                return date_value.strftime('%d.%m.%Y')
            except:
                return str(date_value)
        
        return str(date_value)
    
    def safe_format_time(time_value):
        """Безопасно форматирует время"""
        if not time_value:
            return ''
        
        if isinstance(time_value, str):
            return time_value
        
        if hasattr(time_value, 'strftime'):
            try:
                return time_value.strftime('%H:%M')
            except:
                return str(time_value)
        
        return str(time_value)
    
    def get_status_color(days_left):
        """Возвращает Bootstrap класс цвета на основе оставшихся дней"""
        if days_left is None:
            return 'secondary'
        if days_left == 0:
            return 'danger'
        if days_left == 1:
            return 'warning'
        if days_left <= 7:
            return 'info'
        return 'success'
    
    def is_mobile():
        """Проверяет, использует ли пользователь мобильное устройство"""
        user_agent = request.headers.get('User-Agent', '') if request else ''
        return 'Mobi' in user_agent
    
    # Возвращаем словарь переменных
    return {
        'current_year': datetime.now().year,
        'current_time': datetime.now(),
        'app_name': 'Classmate',
        'app_version': '2.0',
        'format_date': safe_format_date,
        'format_time': safe_format_time,
        'get_status_color': get_status_color,
        'is_mobile': is_mobile,
        'now': datetime.now,
    }