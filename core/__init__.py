"""
Core functionality package
Основные функции приложения
"""
from .database import get_db_connection, init_db, is_postgresql
from .email_service import send_email, send_email_async, EmailService
from .scheduler import init_scheduler, check_upcoming_work

__all__ = [
    'get_db_connection',
    'init_db',
    'is_postgresql',
    'send_email',
    'send_email_async',
    'EmailService',
    'init_scheduler',
    'check_upcoming_work'
]