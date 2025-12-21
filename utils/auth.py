"""
Утилиты для авторизации и проверки прав доступа
"""
from functools import wraps
from flask import session, redirect, url_for, jsonify, request


def is_host():
    """Проверяет, является ли пользователь хостом"""
    return session.get('is_host', False)


def login_required(f):
    """Декоратор для защиты маршрутов"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_host():
            # Если это API запрос, возвращаем JSON
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Nav tiesību'}), 403
            # Иначе редирект на страницу логина
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_only(f):
    """Альтернативный декоратор (синоним login_required)"""
    return login_required(f)