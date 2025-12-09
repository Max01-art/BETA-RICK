"""
Вспомогательные функции
"""
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for
import os


def calculate_days_left(date_str, time_str='23:59', due_date_str=None):
    """
    Рассчитать количество дней до даты
    
    Args:
        date_str: Дата в формате YYYY-MM-DD
        time_str: Время в формате HH:MM
        due_date_str: Дата сдачи (опционально)
    
    Returns:
        int: Количество дней (0 если сегодня, отрицательное если просрочено)
    """
    try:
        # Используем due_date если он указан
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
        print(f"❌ Ошибка расчета дней: {e}")
        return 999


def get_work_status(days_left):
    """
    Получить статус работы по количеству дней
    
    Args:
        days_left: Количество дней до срока
    
    Returns:
        str: Статус ('today', 'tomorrow', 'soon', 'normal', 'overdue')
    """
    if days_left < 0:
        return 'overdue'
    elif days_left == 0:
        return 'today'
    elif days_left == 1:
        return 'tomorrow'
    elif days_left <= 7:
        return 'soon'
    else:
        return 'normal'


def get_status_color(days_left):
    """
    Получить Bootstrap класс цвета по количеству дней
    
    Args:
        days_left: Количество дней до срока
    
    Returns:
        str: Bootstrap класс цвета
    """
    if days_left is None:
        return 'secondary'
    if days_left < 0:
        return 'dark'
    if days_left == 0:
        return 'danger'
    if days_left == 1:
        return 'warning'
    if days_left <= 7:
        return 'info'
    return 'success'


def format_date(date_value, format='%d.%m.%Y'):
    """
    Безопасное форматирование даты
    
    Args:
        date_value: Дата (строка или объект datetime)
        format: Формат вывода
    
    Returns:
        str: Отформатированная дата
    """
    if not date_value:
        return ''
    
    if isinstance(date_value, str):
        try:
            date_obj = datetime.strptime(date_value, '%Y-%m-%d')
            return date_obj.strftime(format)
        except:
            return date_value
    
    if hasattr(date_value, 'strftime'):
        try:
            return date_value.strftime(format)
        except:
            return str(date_value)
    
    return str(date_value)


def format_time(time_value, format='%H:%M'):
    """
    Безопасное форматирование времени
    
    Args:
        time_value: Время (строка или объект datetime)
        format: Формат вывода
    
    Returns:
        str: Отформатированное время
    """
    if not time_value:
        return ''
    
    if isinstance(time_value, str):
        return time_value
    
    if hasattr(time_value, 'strftime'):
        try:
            return time_value.strftime(format)
        except:
            return str(time_value)
    
    return str(time_value)


def get_work_by_subject():
    """
    Группировка всех работ по предметам
    
    Returns:
        dict: Словарь {subject_name: [work1, work2, ...]}
    """
    from models.subject import Subject
    from models.test import Test
    from models.homework import Homework
    
    subjects = Subject.get_all()
    work_by_subject = {}
    
    for subject in subjects:
        subject_name = subject.name
        
        # Получаем тесты и домашние задания для предмета
        tests = Test.get_by_subject(subject_name)
        homework = Homework.get_by_subject(subject_name)
        
        # Добавляем days_left и source
        for test in tests:
            test_dict = test.to_dict()
            test_dict['days_left'] = calculate_days_left(test.date, test.time, test.due_date)
            test_dict['source'] = 'test'
            
            if subject_name not in work_by_subject:
                work_by_subject[subject_name] = []
            work_by_subject[subject_name].append(test_dict)
        
        for hw in homework:
            hw_dict = hw.to_dict()
            hw_dict['days_left'] = calculate_days_left(hw.date, hw.time, hw.due_date)
            hw_dict['source'] = 'homework'
            
            if subject_name not in work_by_subject:
                work_by_subject[subject_name] = []
            work_by_subject[subject_name].append(hw_dict)
        
        # Сортируем по дате
        if subject_name in work_by_subject:
            work_by_subject[subject_name].sort(key=lambda x: x['date'])
    
    return work_by_subject


def allowed_file(filename, allowed_extensions=None):
    """
    Проверка допустимого расширения файла
    
    Args:
        filename: Имя файла
        allowed_extensions: Набор допустимых расширений
    
    Returns:
        bool: True если расширение допустимо
    """
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def sanitize_filename(filename):
    """
    Очистка имени файла от опасных символов
    
    Args:
        filename: Исходное имя файла
    
    Returns:
        str: Безопасное имя файла
    """
    import re
    import uuid
    
    # Получаем расширение
    name, ext = os.path.splitext(filename)
    
    # Удаляем опасные символы
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name)
    
    # Добавляем уникальный ID
    unique_name = f"{uuid.uuid4().hex[:8]}_{name}{ext}"
    
    return unique_name


def get_file_size_human(size_bytes):
    """
    Преобразовать размер файла в человекочитаемый формат
    
    Args:
        size_bytes: Размер в байтах
    
    Returns:
        str: Размер в KB, MB, GB
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def is_mobile_device():
    """
    Определить мобильное устройство по User-Agent
    
    Returns:
        bool: True если мобильное устройство
    """
    from flask import request
    
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'windows phone']
    
    return any(keyword in user_agent for keyword in mobile_keywords)


def generate_device_id():
    """
    Генерация уникального ID устройства
    
    Returns:
        str: Уникальный ID
    """
    from flask import request
    import hashlib
    
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    device_string = f"{ip_address}_{user_agent}"
    device_hash = hashlib.md5(device_string.encode()).hexdigest()
    
    return device_hash


def paginate_list(items, page=1, per_page=20):
    """
    Пагинация списка
    
    Args:
        items: Список элементов
        page: Номер страницы (начиная с 1)
        per_page: Элементов на странице
    
    Returns:
        dict: {items, total, page, pages, has_prev, has_next}
    """
    total = len(items)
    pages = (total + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page,
        'has_prev': page > 1,
        'has_next': page < pages
    }


def group_by_date(items, date_field='date'):
    """
    Группировка элементов по датам
    
    Args:
        items: Список элементов
        date_field: Название поля с датой
    
    Returns:
        dict: {date: [items]}
    """
    from collections import defaultdict
    
    grouped = defaultdict(list)
    
    for item in items:
        date = getattr(item, date_field, None) if hasattr(item, date_field) else item.get(date_field)
        if date:
            grouped[date].append(item)
    
    return dict(grouped)