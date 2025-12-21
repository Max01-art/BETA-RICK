"""
Главный файл приложения Classmate
Структурированная версия
"""
import os
from flask import Flask
from flask_socketio import SocketIO

# Импорт конфигурации
from config.settings import (
    SECRET_KEY, UPLOAD_FOLDER, MAX_CONTENT_LENGTH,
    SOCKETIO_CORS_ALLOWED_ORIGINS
)

# Импорт инициализации БД
from models.database import init_database

# Импорт blueprints
from routes.public import public_bp
from routes.admin import admin_bp
from routes.api import api_bp

# Импорт контекстных процессоров
from utils.template_helpers import inject_common_variables

# Импорт WebSocket обработчиков
from services.websocket_service import register_socketio_handlers

# Импорт фоновых задач
from services.scheduler_service import start_scheduler
from services.email_service import start_email_worker


def create_app():
    """Фабрика приложений Flask"""
    app = Flask(__name__)
    
    # Конфигурация
    app.secret_key = SECRET_KEY
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    
    # Создаем директорию для загрузок
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # Инициализация SocketIO
    socketio = SocketIO(app, cors_allowed_origins=SOCKETIO_CORS_ALLOWED_ORIGINS)
    
    # Регистрация blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Регистрация контекстных процессоров
    app.context_processor(inject_common_variables)
    
    # Регистрация WebSocket обработчиков
    register_socketio_handlers(socketio)
    
    # Инициализация базы данных
    with app.app_context():
        init_database()
    
    # Запуск фоновых задач
    start_email_worker()
    start_scheduler()
    
    return app, socketio


# Создание приложения
app, socketio = create_app()


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting server on port: {port}")
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True
    )