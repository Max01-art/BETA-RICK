"""
Конфигурация приложения BETA-RICK
"""
import os
from datetime import timedelta

class Config:
    """Базовая конфигурация"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'classmate-secret-key-2024')
    
    # База данных
    DATABASE_URL = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Загрузка файлов
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
    
    # Email настройки
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    SMTP_USE_TLS = True
    
    # Безопасность
    HOST_PASSWORD = os.environ.get('HOST_PASSWORD', 'kolya333arbuz')
    SESSION_COOKIE_SECURE = False  # Изменено для работы на Render
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Кеширование
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 минут
    
    # Планировщик
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'Europe/Riga'
    
    # SocketIO - отключаем на продакшене для бесплатного плана
    USE_SOCKETIO = False
    SOCKETIO_MESSAGE_QUEUE = None
    SOCKETIO_CORS_ALLOWED_ORIGINS = '*'
    
    # Уведомления
    NOTIFICATION_CHECK_TIME = '08:00'  # Время проверки уведомлений
    NOTIFICATION_DAYS_BEFORE = [1, 3]  # За сколько дней напоминать
    
    # Пагинация
    ITEMS_PER_PAGE = 20
    
    # Локализация
    LANGUAGES = ['lv', 'en', 'ru']
    DEFAULT_LANGUAGE = 'lv'
    BABEL_DEFAULT_LOCALE = 'lv'
    BABEL_DEFAULT_TIMEZONE = 'Europe/Riga'
    
    # RTU Scraper
    RTU_BASE_URL = 'https://nodarbibas.rtu.lv'
    RTU_SEMESTER_ID = 28
    RTU_PROGRAM_ID = 1393
    RTU_COURSE_ID = 1
    
    # Логирование
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/app.log'
    
    # Версия приложения
    APP_VERSION = '2.1.0'
    APP_NAME = 'Classmate'


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    TESTING = False
    DATABASE_URL = 'sqlite:///school.db'
    USE_SOCKETIO = True  # Включаем для разработки


class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    TESTING = False
    
    # На Render DATABASE_URL уже установлен автоматически
    # Если его нет, используем SQLite как fallback
    if not os.environ.get('DATABASE_URL'):
        DATABASE_URL = 'sqlite:///school.db'
    
    # Безопасность для HTTPS на Render
    SESSION_COOKIE_SECURE = True
    
    # Отключаем SocketIO на продакшене для экономии ресурсов
    USE_SOCKETIO = False


class TestingConfig(Config):
    """Конфигурация для тестирования"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = 'sqlite:///test.db'
    USE_SOCKETIO = False


# Выбор конфигурации в зависимости от окружения
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Возвращает нужную конфигурацию"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    # На Render автоматически определяем продакшен
    if os.environ.get('RENDER'):
        env = 'production'
    
    return config.get(env, config['default'])