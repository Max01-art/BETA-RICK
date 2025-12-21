"""
Утилиты для работы с датами и временем
"""
from datetime import datetime


def calculate_days_left(date_str, time_str='23:59', due_date_str=None):
    """Вычисляет количество оставшихся дней до дедлайна"""
    try:
        # Используем due_date если указан
        target_date = due_date_str if due_date_str else date_str
        
        if not time_str or time_str == '':
            time_str = '23:59'
        
        datetime_str = f"{target_date} {time_str}"
        deadline = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        now = datetime.now()
        
        time_left = deadline - now
        
        if time_left.total_seconds() <= 0:
            return 0
        else:
            return time_left.days
    except Exception as e:
        print(f"Error calculating days left: {e}")
        return 999


def get_work_status(days_left):
    """Возвращает статус работы на основе оставшихся дней"""
    if days_left == 0:
        return "today"
    elif days_left < 0:
        return "overdue"
    elif days_left == 1:
        return "tomorrow"
    elif days_left <= 7:
        return "soon"
    else:
        return "future"


def format_date(date_value):
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


def format_time(time_value):
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