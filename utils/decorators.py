"""
Декораторы для Flask приложения
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request
from datetime import datetime


def host_required(f):
    """
    Декоратор для защиты админских страниц
    Требует авторизации как хост
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_host'):
            flash('⛔ Vajag host piekļuvi', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def login_required(f):
    """
    Декоратор для страниц, требующих авторизации
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('⛔ Lūdzu ielogojieties', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def anonymous_required(f):
    """
    Декоратор для страниц, доступных только неавторизованным
    (например, страница логина)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('is_host') or session.get('logged_in'):
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def rate_limit(limit=10, per=60):
    """
    Простой rate limiter
    
    Args:
        limit: Количество запросов
        per: За сколько секунд
    """
    def decorator(f):
        from collections import defaultdict
        from time import time
        
        # Хранилище запросов {ip: [timestamps]}
        requests = defaultdict(list)
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            now = time()
            
            # Удаляем старые записи
            requests[ip] = [timestamp for timestamp in requests[ip] 
                          if now - timestamp < per]
            
            # Проверяем лимит
            if len(requests[ip]) >= limit:
                flash(f'⚠️ Pārāk daudz pieprasījumu. Uzgaidiet {per} sekundes.', 'warning')
                return redirect(request.referrer or url_for('main.index'))
            
            # Добавляем текущий запрос
            requests[ip].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_json(f):
    """
    Декоратор для валидации JSON в API запросах
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return {'error': 'Content-Type должен быть application/json'}, 400
        return f(*args, **kwargs)
    return decorated_function


def log_activity(activity_type):
    """
    Декоратор для логирования действий пользователя
    
    Args:
        activity_type: Тип активности (например, 'create_homework', 'delete_test')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)
            
            # Логируем активность
            try:
                from core.database import get_db_connection, is_postgresql
                conn = get_db_connection()
                cursor = conn.cursor()
                
                user_id = session.get('user_id', 'anonymous')
                ip_address = request.remote_addr
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Можно добавить таблицу activity_log в БД
                print(f"📝 {timestamp} | {activity_type} | User: {user_id} | IP: {ip_address}")
                
                conn.close()
            except Exception as e:
                print(f"❌ Ошибка логирования: {e}")
            
            return result
        return decorated_function
    return decorator


def cache_response(timeout=300):
    """
    Простое кеширование ответов
    
    Args:
        timeout: Время кеширования в секундах (по умолчанию 5 минут)
    """
    def decorator(f):
        from time import time
        cache = {}
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Создаем ключ кеша из URL и параметров
            cache_key = f"{request.url}_{args}_{kwargs}"
            now = time()
            
            # Проверяем кеш
            if cache_key in cache:
                cached_response, cached_time = cache[cache_key]
                if now - cached_time < timeout:
                    return cached_response
            
            # Выполняем функцию
            response = f(*args, **kwargs)
            
            # Сохраняем в кеш
            cache[cache_key] = (response, now)
            
            return response
        return decorated_function
    return decorator


def require_fields(*fields):
    """
    Декоратор для проверки обязательных полей в форме
    
    Args:
        *fields: Список обязательных полей
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            missing_fields = []
            
            for field in fields:
                if field not in request.form or not request.form.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                flash(f"⚠️ Trūkst obligātie lauki: {', '.join(missing_fields)}", 'warning')
                return redirect(request.referrer or url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def register_context_processors(app):
    """
    Регистрация context processors для всех шаблонов
    
    Args:
        app: Flask приложение
    """
    @app.context_processor
    def inject_helpers():
        """Добавляет вспомогательные функции в контекст шаблонов"""
        from utils.helpers import (
            calculate_days_left,
            format_date,
            format_time,
            get_status_color,
            get_work_status
        )
        
        return {
            'calculate_days_left': calculate_days_left,
            'format_date': format_date,
            'format_time': format_time,
            'get_status_color': get_status_color,
            'get_work_status': get_work_status,
            'now': datetime.now()
        }
    
    @app.context_processor
    def inject_config():
        """Добавляет конфигурацию приложения"""
        return {
            'app_name': app.config.get('APP_NAME', 'Classmate'),
            'app_version': app.config.get('APP_VERSION', '2.1.0'),
            'current_year': datetime.now().year
        }
    
    @app.context_processor
    def inject_user_data():
        """Добавляет данные пользователя"""
        return {
            'is_host': session.get('is_host', False),
            'logged_in': session.get('logged_in', False),
            'user_theme': session.get('theme', 'default')
        }
    
    @app.template_filter('pluralize')
    def pluralize_filter(count, singular, plural):
        """Фильтр для множественного числа"""
        return singular if count == 1 else plural
    
    @app.template_filter('truncate_text')
    def truncate_text_filter(text, length=100):
        """Фильтр для обрезания текста"""
        if len(text) <= length:
            return text
        return text[:length] + '...'
    
    @app.template_filter('time_ago')
    def time_ago_filter(date_str):
        """Фильтр для отображения времени в формате 'X дней назад'"""
        try:
            if isinstance(date_str, str):
                date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            else:
                date = date_str
            
            now = datetime.now()
            diff = now - date
            
            if diff.days == 0:
                hours = diff.seconds // 3600
                if hours == 0:
                    minutes = diff.seconds // 60
                    return f"pirms {minutes} minūtēm"
                return f"pirms {hours} stundām"
            elif diff.days == 1:
                return "vakar"
            elif diff.days < 7:
                return f"pirms {diff.days} dienām"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"pirms {weeks} nedēļām"
            else:
                months = diff.days // 30
                return f"pirms {months} mēnešiem"
        except:
            return date_str