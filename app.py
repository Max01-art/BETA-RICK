"""
Главный файл приложения BETA-RICK
Минимизированная версия - вся логика вынесена в модули
"""
from flask import Flask, render_template
from flask_socketio import SocketIO
import os

from config import get_config
from core.database import init_db, get_db_connection
from core.scheduler import init_scheduler
from utils.decorators import register_context_processors

# Импорт маршрутов
from routes import (
    main_bp,
    subjects_bp,
    tests_bp,
    homework_bp,
    news_bp,
    auth_bp,
    notifications_bp,
    api_bp,
    import_routes_bp
)

def create_app(config_name=None):
    """
    Фабрика приложений Flask
    """
    app = Flask(__name__)
    
    # Загрузка конфигурации
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app.config.from_object(get_config())
    
    # Инициализация расширений
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Инициализация базы данных
    with app.app_context():
        init_db()
    
    # Регистрация контекст процессоров
    register_context_processors(app)
    
    # Регистрация blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(subjects_bp, url_prefix='/subjects')
    app.register_blueprint(tests_bp, url_prefix='/tests')
    app.register_blueprint(homework_bp, url_prefix='/homework')
    app.register_blueprint(news_bp, url_prefix='/news')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(import_routes_bp, url_prefix='/import')
    
    # Инициализация планировщика (только для продакшена)
    if not app.config['DEBUG']:
        init_scheduler(app)
    
    # Обработчики ошибок
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    # Создание необходимых папок
    for folder in ['static/uploads', 'static/uploads/avatars', 
                   'static/uploads/news', 'static/uploads/exports', 'logs']:
        os.makedirs(folder, exist_ok=True)
    
    return app, socketio


# Создание приложения
app, socketio = create_app()


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Запуск сервера на порту: {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)