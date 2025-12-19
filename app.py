"""
Главный файл приложения BETA-RICK
"""
from flask import Flask, render_template
import os

from config import get_config
from core.database import init_db
from utils.decorators import register_context_processors

# ПРЯМЫЕ импорты blueprints (не через routes пакет!)
from routes.main import main_bp
from routes.subjects import subjects_bp
from routes.tests import tests_bp
from routes.homework import homework_bp
from routes.news import news_bp
from routes.auth import auth_bp
from routes.notifications import notifications_bp
from routes.api import api_bp
from routes.import_routes import import_routes_bp


def create_app():
    """Фабрика приложений Flask"""
    app = Flask(__name__)
    
    # Загрузка конфигурации
    config_obj = get_config()
    app.config.from_object(config_obj)
    
    print(f"🚀 Starting {app.config['APP_NAME']} v{app.config['APP_VERSION']}")
    
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
    
    print("✅ All blueprints registered")
    
    # Обработчики ошибок
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', 
                             error_code=404, 
                             error_message='Lapa nav atrasta'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', 
                             error_code=500, 
                             error_message='Servera kļūda'), 500
    
    # Создание необходимых папок
    folders = ['static/uploads', 'static/uploads/avatars', 
               'static/uploads/news', 'static/uploads/exports', 'logs']
    
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
        except:
            pass
    
    print("✅ App initialized successfully")
    return app


# Создание приложения
app = create_app()


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"🌐 Running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)