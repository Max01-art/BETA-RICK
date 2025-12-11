"""
Главный файл приложения BETA-RICK
Минимизированная версия - вся логика вынесена в модули
"""
from flask import Flask, render_template
import os

from config import get_config
from core.database import init_db
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
    
    config_obj = get_config()
    app.config.from_object(config_obj)
    
    # Инициализация SocketIO только если включено
    socketio = None
    if app.config.get('USE_SOCKETIO', False):
        try:
            from flask_socketio import SocketIO
            socketio = SocketIO(app, cors_allowed_origins="*")
            print("✅ SocketIO enabled")
        except ImportError:
            print("⚠️ flask-socketio not installed, running without WebSocket support")
    else:
        print("ℹ️ SocketIO disabled (production mode)")
    
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
    
    # Инициализация планировщика (только для продакшена с БД)
    # На бесплатном плане Render лучше отключить
    if not app.config['DEBUG'] and not os.environ.get('RENDER_FREE'):
        try:
            from core.scheduler import init_scheduler
            init_scheduler(app)
            print("✅ Scheduler initialized")
        except Exception as e:
            print(f"⚠️ Scheduler disabled: {e}")
    
    # Обработчики ошибок
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', 
                             error_code=404, 
                             error_message='Страница не найдена'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', 
                             error_code=500, 
                             error_message='Внутренняя ошибка сервера'), 500
    
    # Создание необходимых папок
    folders = [
        'static/uploads', 
        'static/uploads/avatars', 
        'static/uploads/news', 
        'static/uploads/exports', 
        'logs'
    ]
    
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            print(f"⚠️ Cannot create folder {folder}: {e}")
    
    print(f"✅ App initialized - {app.config['APP_NAME']} v{app.config['APP_VERSION']}")
    
    return app, socketio


# Создание приложения
app, socketio = create_app()


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    
    # Определяем окружение
    is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RENDER')
    
    if is_production:
        print(f"🚀 Production mode on port: {port}")
        # В продакшене используем gunicorn, не нужен socketio.run
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print(f"🔧 Development mode on port: {port}")
        if socketio:
            socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
        else:
            app.run(host='0.0.0.0', port=port, debug=True)