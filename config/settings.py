"""
Конфигурация приложения Classmate
"""
import os
from datetime import timedelta

# ================= БАЗОВЫЕ НАСТРОЙКИ =================
SECRET_KEY = 'classmate-secret-key-2024'
HOST_USERNAME = os.getenv('HOST_USERNAME', 'admin')
HOST_PASSWORD = os.getenv('HOST_PASSWORD', 'default')

# ================= БАЗА ДАННЫХ =================
DB_FILE = 'school.db'
DATABASE_URL = os.environ.get('DATABASE_URL')

# ================= ФАЙЛЫ =================
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# ================= КЭШ =================
CACHE_DURATION = 30  # секунды

# ================= SMTP НАСТРОЙКИ =================
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

# ================= SOCKETIO =================
SOCKETIO_CORS_ALLOWED_ORIGINS = "*"

# ================= SCHEDULER =================
NOTIFICATION_CHECK_TIME = "08:00"  # Время проверки уведомлений
SCHEDULER_CHECK_INTERVAL = 60  # Интервал проверки в секундах