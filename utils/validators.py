"""
Валидация данных
"""
import re
from datetime import datetime


def validate_email(email):
    """
    Валидация email адреса
    
    Args:
        email: Email для проверки
    
    Returns:
        tuple: (bool, str) - (валидность, сообщение об ошибке)
    """
    if not email:
        return False, "Email не может быть пустым"
    
    # Простая regex для email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Неверный формат email"
    
    if len(email) > 255:
        return False, "Email слишком длинный (максимум 255 символов)"
    
    return True, ""


def validate_date(date_str, allow_past=False):
    """
    Валидация даты
    
    Args:
        date_str: Дата в формате YYYY-MM-DD
        allow_past: Разрешить прошлые даты
    
    Returns:
        tuple: (bool, str) - (валидность, сообщение об ошибке)
    """
    if not date_str:
        return False, "Дата не может быть пустой"
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        
        if not allow_past and date.date() < datetime.now().date():
            return False, "Дата не может быть в прошлом"
        
        return True, ""
        
    except ValueError:
        return False, "Неверный формат даты (используйте YYYY-MM-DD)"


def validate_time(time_str):
    """
    Валидация времени
    
    Args:
        time_str: Время в формате HH:MM
    
    Returns:
        tuple: (bool, str) - (валидность, сообщение об ошибке)
    """
    if not time_str:
        return True, ""  # Время опционально
    
    time_pattern = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'
    
    if not re.match(time_pattern, time_str):
        return False, "Неверный формат времени (используйте HH:MM)"
    
    return True, ""


def validate_subject_name(name):
    """
    Валидация названия предмета
    
    Args:
        name: Название предмета
    
    Returns:
        tuple: (bool, str) - (валидность, сообщение об ошибке)
    """
    if not name or not name.strip():
        return False, "Название предмета не может быть пустым"
    
    if len(name) < 2:
        return False, "Название слишком короткое (минимум 2 символа)"
    
    if len(name) > 100:
        return False, "Название слишком длинное (максимум 100 символов)"
    
    # Проверка на допустимые символы (буквы, цифры, пробелы, дефисы)
    if not re.match(r'^[a-zA-Z0-9\s\-āčēģīķļņšūžĀČĒĢĪĶĻŅŠŪŽ]+$', name):
        return False, "Название содержит недопустимые символы"
    
    return True, ""


def validate_color(color):
    """
    Валидация HEX цвета
    
    Args:
        color: HEX цвет (#RRGGBB)
    
    Returns:
        tuple: (bool, str) - (валидность, сообщение об ошибке)
    """
    if not color:
        return True, ""  # Цвет опционален
    
    hex_pattern = r'^#[0-9A-Fa-f]{6}$'
    
    if not re.match(hex_pattern, color):
        return False, "Неверный формат цвета (используйте #RRGGBB)"
    
    return True, ""


def validate_text_length(text, min_length=0, max_length=1000, field_name="Текст"):
    """
    Валидация длины текста
    
    Args:
        text: Текст для проверки
        min_length: Минимальная длина
        max_length: Максимальная длина
        field_name: Название поля для сообщений
    
    Returns:
        tuple: (bool, str) - (валидность, сообщение об ошибке)
    """
    if not text:
        text = ""
    
    text_length = len(text.strip())
    
    if text_length < min_length:
        return False, f"{field_name} слишком короткий (минимум {min_length} символов)"
    
    if text_length > max_length:
        return False, f"{field_name} слишком длинный (максимум {max_length} символов)"
    
    return True, ""


def validate_work_type(work_type, allowed_types=None):
    """
    Валидация типа работы
    
    Args:
        work_type: Тип работы
        allowed_types: Список допустимых типов
    
    Returns:
        tuple: (bool, str) - (валидность, сообщение об ошибке)
    """
    if allowed_types is None:
        allowed_types = [
            'Kontroldarbs', 'Tests', 'Eksāmens', 'Starpeksāmens',
            'LD', 'Prezentācija', 'Mājasdarbs'
        ]
    
    if not work_type:
        return False, "Тип работы не может быть пустым"
    
    if work_type not in allowed_types:
        return False, f"Недопустимый тип работы (разрешены: {', '.join(allowed_types)})"
    
    return True, ""


def validate_password(password, min_length=8):
    """
    Валидация пароля
    
    Args:
        password: Пароль
        min_length: Минимальная длина
    
    Returns:
        tuple: (bool, str) - (валидность, сообщение об ошибке)
    """
    if not password:
        return False, "Пароль не может быть пустым"
    
    if len(password) < min_length:
        return False, f"Пароль слишком короткий (минимум {min_length} символов)"
    
    return True, ""


def validate_url(url):
    """
    Валидация URL
    
    Args:
        url: URL для проверки
    
    Returns:
        tuple: (bool, str) - (валидность, сообщение об ошибке)
    """
    if not url:
        return True, ""  # URL опционален
    
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    
    if not re.match(url_pattern, url):
        return False, "Неверный формат URL"
    
    if len(url) > 500:
        return False, "URL слишком длинный"
    
    return True, ""


def validate_file_extension(filename, allowed_extensions=None):
    """
    Валидация расширения файла
    
    Args:
        filename: Имя файла
        allowed_extensions: Список допустимых расширений
    
    Returns:
        tuple: (bool, str) - (валидность, сообщение об ошибке)
    """
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
    
    if not filename or '.' not in filename:
        return False, "Неверное имя файла"
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext not in allowed_extensions:
        return False, f"Недопустимый тип файла (разрешены: {', '.join(allowed_extensions)})"
    
    return True, ""


def sanitize_input(text, max_length=1000):
    """
    Очистка пользовательского ввода
    
    Args:
        text: Текст для очистки
        max_length: Максимальная длина
    
    Returns:
        str: Очищенный текст
    """
    if not text:
        return ""
    
    # Удаляем лишние пробелы
    text = text.strip()
    
    # Ограничиваем длину
    if len(text) > max_length:
        text = text[:max_length]
    
    # Удаляем опасные HTML теги (базовая защита от XSS)
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'javascript:',
        r'on\w+\s*=',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text


def sanitize_html(text, allowed_tags=None):
    """
    Очистка HTML с сохранением разрешенных тегов
    
    Args:
        text: HTML текст
        allowed_tags: Список разрешенных тегов
    
    Returns:
        str: Очищенный HTML
    """
    if not text:
        return ""
    
    if allowed_tags is None:
        allowed_tags = {'p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3'}
    
    # Удаляем опасные атрибуты и скрипты
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    
    return text


def validate_file_upload(file, max_size_mb=10, allowed_extensions=None):
    """
    Валидация загружаемого файла
    
    Args:
        file: Объект файла (Flask FileStorage)
        max_size_mb: Максимальный размер в МБ
        allowed_extensions: Список допустимых расширений
    
    Returns:
        tuple: (bool, str) - (валидность, сообщение об ошибке)
    """
    if not file:
        return False, "Файл не выбран"
    
    if not file.filename:
        return False, "Неверное имя файла"
    
    # Проверка расширения
    is_valid, error = validate_file_extension(file.filename, allowed_extensions)
    if not is_valid:
        return False, error
    
    # Проверка размера (если доступно)
    if hasattr(file, 'content_length') and file.content_length:
        max_size_bytes = max_size_mb * 1024 * 1024
        if file.content_length > max_size_bytes:
            return False, f"Файл слишком большой (максимум {max_size_mb}МБ)"
    
    return True, ""


def validate_homework_data(data):
    """
    Валидация данных домашнего задания
    
    Args:
        data: Словарь с данными
    
    Returns:
        tuple: (bool, dict) - (валидность, словарь ошибок)
    """
    errors = {}
    
    # Проверка предмета
    if not data.get('subject_id'):
        errors['subject_id'] = "Выберите предмет"
    
    # Проверка даты
    is_valid, error = validate_date(data.get('due_date', ''), allow_past=False)
    if not is_valid:
        errors['due_date'] = error
    
    # Проверка времени (опционально)
    is_valid, error = validate_time(data.get('due_time', ''))
    if not is_valid:
        errors['due_time'] = error
    
    # Проверка описания
    is_valid, error = validate_text_length(
        data.get('description', ''),
        min_length=1,
        max_length=2000,
        field_name="Описание"
    )
    if not is_valid:
        errors['description'] = error
    
    # Проверка URL (опционально)
    is_valid, error = validate_url(data.get('url', ''))
    if not is_valid:
        errors['url'] = error
    
    return len(errors) == 0, errors


def validate_test_data(data):
    """
    Валидация данных теста/контрольной
    
    Args:
        data: Словарь с данными
    
    Returns:
        tuple: (bool, dict) - (валидность, словарь ошибок)
    """
    errors = {}
    
    # Проверка предмета
    if not data.get('subject_id'):
        errors['subject_id'] = "Выберите предмет"
    
    # Проверка типа работы
    is_valid, error = validate_work_type(data.get('work_type', ''))
    if not is_valid:
        errors['work_type'] = error
    
    # Проверка даты
    is_valid, error = validate_date(data.get('date', ''), allow_past=False)
    if not is_valid:
        errors['date'] = error
    
    # Проверка времени (опционально)
    is_valid, error = validate_time(data.get('time', ''))
    if not is_valid:
        errors['time'] = error
    
    # Проверка темы
    is_valid, error = validate_text_length(
        data.get('topic', ''),
        min_length=2,
        max_length=200,
        field_name="Тема"
    )
    if not is_valid:
        errors['topic'] = error
    
    # Проверка описания (опционально)
    is_valid, error = validate_text_length(
        data.get('description', ''),
        min_length=0,
        max_length=1000,
        field_name="Описание"
    )
    if not is_valid:
        errors['description'] = error
    
    return len(errors) == 0, errors


def validate_news_data(data):
    """
    Валидация данных новости
    
    Args:
        data: Словарь с данными
    
    Returns:
        tuple: (bool, dict) - (валидность, словарь ошибок)
    """
    errors = {}
    
    # Проверка заголовка
    is_valid, error = validate_text_length(
        data.get('title', ''),
        min_length=3,
        max_length=200,
        field_name="Заголовок"
    )
    if not is_valid:
        errors['title'] = error
    
    # Проверка содержимого
    is_valid, error = validate_text_length(
        data.get('content', ''),
        min_length=10,
        max_length=5000,
        field_name="Содержимое"
    )
    if not is_valid:
        errors['content'] = error
    
    # Проверка URL изображения (опционально)
    is_valid, error = validate_url(data.get('image_url', ''))
    if not is_valid:
        errors['image_url'] = error
    
    return len(errors) == 0, errors


def validate_subject_data(data):
    """
    Валидация данных предмета
    
    Args:
        data: Словарь с данными
    
    Returns:
        tuple: (bool, dict) - (валидность, словарь ошибок)
    """
    errors = {}
    
    # Проверка названия
    is_valid, error = validate_subject_name(data.get('name', ''))
    if not is_valid:
        errors['name'] = error
    
    # Проверка преподавателя (опционально)
    is_valid, error = validate_text_length(
        data.get('teacher', ''),
        min_length=0,
        max_length=100,
        field_name="Преподаватель"
    )
    if not is_valid:
        errors['teacher'] = error
    
    # Проверка цвета (опционально)
    is_valid, error = validate_color(data.get('color', ''))
    if not is_valid:
        errors['color'] = error
    
    # Проверка описания (опционально)
    is_valid, error = validate_text_length(
        data.get('description', ''),
        min_length=0,
        max_length=500,
        field_name="Описание"
    )
    if not is_valid:
        errors['description'] = error
    
    return len(errors) == 0, errors


class ValidationError(Exception):
    """Исключение для ошибок валидации"""
    pass


def validate_form_data(data, rules):
    """
    Валидация данных формы по правилам
    
    Args:
        data: Словарь с данными формы
        rules: Словарь с правилами валидации
            Пример: {
                'email': [validate_email],
                'date': [lambda x: validate_date(x, allow_past=False)],
                'name': [validate_subject_name]
            }
    
    Returns:
        tuple: (bool, dict) - (валидность, словарь ошибок)
    
    Raises:
        ValidationError: Если валидация не прошла
    """
    errors = {}
    
    for field, validators in rules.items():
        value = data.get(field, '')
        
        for validator in validators:
            is_valid, error_message = validator(value)
            
            if not is_valid:
                errors[field] = error_message
                break
    
    return len(errors) == 0, errors